"""AI provider abstraction. Keys stay on the server; the frontend never sees them."""
from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from ..config import get_settings


class AIUnavailable(Exception):
    """Raised when no provider is configured or the provider call fails."""


class AIProvider(ABC):
    name = "base"

    @abstractmethod
    def generate(self, system: str, messages: list[dict]) -> str: ...


class GeminiProvider(AIProvider):
    name = "gemini"
    URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, api_key: str, model: str, timeout: float) -> None:
        self.api_key, self.model, self.timeout = api_key, model, timeout

    def generate(self, system: str, messages: list[dict]) -> str:
        contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]} for m in messages]
        body = {"systemInstruction": {"parts": [{"text": system}]}, "contents": contents,
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1400}}
        try:
            r = httpx.post(self.URL.format(model=self.model), json=body, timeout=self.timeout,
                           headers={"x-goog-api-key": self.api_key, "content-type": "application/json"})
        except httpx.HTTPError as e:
            raise AIUnavailable(f"network error: {type(e).__name__}") from e
        if r.status_code == 429:
            raise AIUnavailable("quota exceeded")
        if r.status_code >= 400:
            raise AIUnavailable(f"provider error {r.status_code}")
        try:
            data = r.json()
            parts = data["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts).strip()
        except (KeyError, IndexError, ValueError) as e:
            raise AIUnavailable("empty or blocked response") from e
        if not text:
            raise AIUnavailable("empty response")
        return text


def get_provider() -> AIProvider | None:
    s = get_settings()
    if s.ai_provider == "gemini" and s.gemini_api_key:
        return GeminiProvider(s.gemini_api_key, s.gemini_model, s.ai_timeout_seconds)
    return None
