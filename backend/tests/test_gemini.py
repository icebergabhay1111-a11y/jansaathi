"""Gemini adapter tests with mocked HTTP (no real key or network used)."""
import httpx
import pytest

from app.ai.provider import AIUnavailable, GeminiProvider


class R:
    def __init__(self, status, data):
        self.status_code, self._d = status, data

    def json(self):
        return self._d


def test_gemini_parses_text_and_keeps_key_in_header(monkeypatch):
    seen = {}

    def fake_post(url, json, timeout, headers):
        seen.update(url=url, headers=headers, body=json)
        return R(200, {"candidates": [{"content": {"parts": [{"text": "Answer [1]"}]}}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    out = GeminiProvider("k-123", "gemini-2.5-flash", 5).generate("sys", [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "x"}])
    assert out == "Answer [1]"
    assert "k-123" not in seen["url"] and seen["headers"]["x-goog-api-key"] == "k-123"
    assert seen["body"]["contents"][1]["role"] == "model"


@pytest.mark.parametrize("status,data,msg", [(429, {}, "quota"), (500, {}, "provider error"), (200, {"candidates": []}, "empty")])
def test_gemini_failures_raise_unavailable(monkeypatch, status, data, msg):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: R(status, data))
    with pytest.raises(AIUnavailable, match=msg):
        GeminiProvider("k", "m", 5).generate("s", [{"role": "user", "content": "q"}])


def test_gemini_network_error(monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectTimeout("t")
    monkeypatch.setattr(httpx, "post", boom)
    with pytest.raises(AIUnavailable, match="network"):
        GeminiProvider("k", "m", 5).generate("s", [{"role": "user", "content": "q"}])
