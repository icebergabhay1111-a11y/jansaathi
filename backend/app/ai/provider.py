"""AI provider abstraction. Keys stay on the server; the frontend never sees them."""
from __future__ import annotations

import base64
import logging
import time
from abc import ABC, abstractmethod

import httpx

from ..config import get_settings

log = logging.getLogger("jansaathi.ai")

# Status codes where another model may still work: bad/unknown model for this key (400/403/404),
# per-model quota (429) and temporary overload/outage (5xx).
RETRY_NEXT_MODEL = {400, 403, 404, 429, 500, 502, 503, 504}


class AIUnavailable(Exception):
    """Raised when no provider is configured or the provider call fails."""


class AIProvider(ABC):
    name = "base"

    @abstractmethod
    def generate(self, system: str, messages: list[dict], budget: float | None = None) -> str: ...

    def transcribe(self, audio: bytes, mime_type: str, language_hint: str) -> str:
        raise AIUnavailable("transcription not supported by this provider")


class GeminiProvider(AIProvider):
    """Gemini via the REST generateContent endpoint.

    Tries the configured model, then the fallbacks, when a model is unavailable to this key, over
    its quota, overloaded or too slow. Every call has a total time budget, so a visitor never waits
    longer than that before getting at least the record-based answer."""

    name = "gemini"
    URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, api_key: str, model: str, timeout: float, fallbacks: list[str] | None = None,
                 per_model_timeout: float = 12.0) -> None:
        self.api_key, self.timeout, self.per_model_timeout = api_key, timeout, per_model_timeout
        self.models = [model] + [m for m in (fallbacks or []) if m and m != model]

    @staticmethod
    def _config(model: str, max_tokens: int) -> dict:
        cfg: dict = {"temperature": 0.2, "maxOutputTokens": max_tokens}
        if model.startswith(("gemini-3", "gemini-4")):
            cfg["thinkingConfig"] = {"thinkingLevel": "low"}  # factual grounded answers; keeps latency/cost down
        return cfg

    def _call(self, body_for, max_tokens: int, budget: float | None = None) -> str:
        deadline = time.monotonic() + (budget or self.timeout)
        reasons: list[str] = []
        for model in self.models:
            remaining = deadline - time.monotonic()
            if remaining < 2:
                reasons.append("time budget used up")
                break
            body = body_for(model)
            body["generationConfig"] = self._config(model, max_tokens)
            t0 = time.monotonic()
            try:
                r = httpx.post(self.URL.format(model=model), json=body, timeout=min(self.per_model_timeout, remaining),
                               headers={"x-goog-api-key": self.api_key, "content-type": "application/json"})
            except httpx.TimeoutException:
                log.warning("gemini model=%s timed out after %.1fs", model, time.monotonic() - t0)
                reasons.append(f"{model} timed out")
                continue
            except httpx.HTTPError as e:
                log.warning("gemini model=%s network error %s", model, type(e).__name__)
                raise AIUnavailable(f"network error: {type(e).__name__}") from e
            log.info("gemini model=%s status=%s %.1fs", model, r.status_code, time.monotonic() - t0)
            if r.status_code in RETRY_NEXT_MODEL:
                reasons.append(f"{model} {'quota exceeded' if r.status_code == 429 else r.status_code}")
                continue
            if r.status_code >= 400:
                raise AIUnavailable(f"provider error {r.status_code}")
            try:
                parts = r.json()["candidates"][0]["content"]["parts"]
                text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
            except (KeyError, IndexError, ValueError):
                reasons.append(f"{model} empty or blocked response")
                continue
            if not text:
                reasons.append(f"{model} empty response")
                continue
            return text
        if reasons and all("quota exceeded" in r for r in reasons):
            raise AIUnavailable("quota exceeded")
        raise AIUnavailable("; ".join(reasons) or "provider error")

    def generate(self, system: str, messages: list[dict], budget: float | None = None) -> str:
        contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]} for m in messages]
        return self._call(lambda _m: {"systemInstruction": {"parts": [{"text": system}]}, "contents": contents}, 2048, budget)

    def transcribe(self, audio: bytes, mime_type: str, language_hint: str) -> str:
        prompt = (f"Transcribe this short voice message exactly as spoken. The speaker most likely uses {language_hint}. "
                  "Write it in that language's own script (Devanagari for Hindi, Tamil script for Tamil). "
                  "Return only the transcription — no translation, labels or commentary. "
                  "If there is no intelligible speech, return an empty string.")
        data = base64.b64encode(audio).decode()
        return self._call(lambda _m: {"contents": [{"role": "user", "parts": [
            {"text": prompt}, {"inline_data": {"mime_type": mime_type, "data": data}}]}]}, 512, budget=20)


def get_provider() -> AIProvider | None:
    s = get_settings()
    if s.ai_provider == "gemini" and s.gemini_api_key:
        return GeminiProvider(s.gemini_api_key, s.gemini_model, s.ai_timeout_seconds, s.gemini_fallback_models,
                              s.ai_model_timeout_seconds)
    return None
