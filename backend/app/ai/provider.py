"""AI provider abstraction. Keys stay on the server; the frontend never sees them."""
from __future__ import annotations

import base64
from abc import ABC, abstractmethod

import httpx

from ..config import get_settings


class AIUnavailable(Exception):
    """Raised when no provider is configured or the provider call fails."""


class AIProvider(ABC):
    name = "base"

    @abstractmethod
    def generate(self, system: str, messages: list[dict]) -> str: ...

    def transcribe(self, audio: bytes, mime_type: str, language_hint: str) -> str:
        raise AIUnavailable("transcription not supported by this provider")


class GeminiProvider(AIProvider):
    """Gemini via the REST generateContent endpoint.

    Tries the configured model, then fallbacks, when a model is unavailable to this key
    (Google restricts older models such as 2.5 Flash to existing users)."""

    name = "gemini"
    URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, api_key: str, model: str, timeout: float, fallbacks: list[str] | None = None) -> None:
        self.api_key, self.timeout = api_key, timeout
        self.models = [model] + [m for m in (fallbacks or []) if m and m != model]

    @staticmethod
    def _config(model: str, max_tokens: int) -> dict:
        cfg: dict = {"temperature": 0.2, "maxOutputTokens": max_tokens}
        if model.startswith(("gemini-3", "gemini-4")):
            cfg["thinkingConfig"] = {"thinkingLevel": "low"}  # factual grounded answers; keeps latency/cost down
        return cfg

    def _call(self, body_for, max_tokens: int) -> str:
        last = "provider error"
        for model in self.models:
            body = body_for(model)
            body["generationConfig"] = self._config(model, max_tokens)
            try:
                r = httpx.post(self.URL.format(model=model), json=body, timeout=self.timeout,
                               headers={"x-goog-api-key": self.api_key, "content-type": "application/json"})
            except httpx.HTTPError as e:
                raise AIUnavailable(f"network error: {type(e).__name__}") from e
            if r.status_code == 429:
                raise AIUnavailable("quota exceeded")
            if r.status_code in (400, 403, 404):
                # model not found / not enabled for this key → try the next model
                last = f"provider error {r.status_code} for {model}"
                continue
            if r.status_code >= 400:
                raise AIUnavailable(f"provider error {r.status_code}")
            try:
                parts = r.json()["candidates"][0]["content"]["parts"]
                text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
            except (KeyError, IndexError, ValueError) as e:
                raise AIUnavailable("empty or blocked response") from e
            if not text:
                raise AIUnavailable("empty response")
            return text
        raise AIUnavailable(last)

    def generate(self, system: str, messages: list[dict]) -> str:
        contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]} for m in messages]
        return self._call(lambda _m: {"systemInstruction": {"parts": [{"text": system}]}, "contents": contents}, 2048)

    def transcribe(self, audio: bytes, mime_type: str, language_hint: str) -> str:
        prompt = (f"Transcribe this short voice message exactly as spoken. The speaker most likely uses {language_hint}. "
                  "Write it in that language's own script (Devanagari for Hindi, Tamil script for Tamil). "
                  "Return only the transcription — no translation, labels or commentary. "
                  "If there is no intelligible speech, return an empty string.")
        data = base64.b64encode(audio).decode()
        return self._call(lambda _m: {"contents": [{"role": "user", "parts": [
            {"text": prompt}, {"inline_data": {"mime_type": mime_type, "data": data}}]}]}, 512)


def get_provider() -> AIProvider | None:
    s = get_settings()
    if s.ai_provider == "gemini" and s.gemini_api_key:
        return GeminiProvider(s.gemini_api_key, s.gemini_model, s.ai_timeout_seconds, s.gemini_fallback_models)
    return None
