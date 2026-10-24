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
    out = GeminiProvider("k-123", "gemini-2.5-flash", 5, []).generate("sys", [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "x"}])
    assert out == "Answer [1]"
    assert "k-123" not in seen["url"] and seen["headers"]["x-goog-api-key"] == "k-123"
    assert seen["body"]["contents"][1]["role"] == "model"


@pytest.mark.parametrize("status,data,msg", [(429, {}, "quota"), (500, {}, "m 500"), (501, {}, "provider error 501"), (200, {"candidates": []}, "empty")])
def test_gemini_failures_raise_unavailable(monkeypatch, status, data, msg):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: R(status, data))
    with pytest.raises(AIUnavailable, match=msg):
        GeminiProvider("k", "m", 5).generate("s", [{"role": "user", "content": "q"}])


def test_gemini_network_error(monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("dns")
    monkeypatch.setattr(httpx, "post", boom)
    with pytest.raises(AIUnavailable, match="network"):
        GeminiProvider("k", "m", 5).generate("s", [{"role": "user", "content": "q"}])


def test_gemini_timeout_reports_timed_out(monkeypatch):
    def slow(*a, **k):
        raise httpx.ConnectTimeout("t")
    monkeypatch.setattr(httpx, "post", slow)
    with pytest.raises(AIUnavailable, match="m timed out"):
        GeminiProvider("k", "m", 5).generate("s", [{"role": "user", "content": "q"}])


def _ok(text="Answer [1]"):
    return R(200, {"candidates": [{"content": {"parts": [{"text": text}]}}]})


def test_timeout_then_overload_falls_through_to_next_model(monkeypatch):
    """What happened live on 24 Oct 2026: main model timed out / returned 503."""
    calls = []

    def fake_post(url, json, timeout, headers):
        model = url.split("/models/")[1].split(":")[0]
        calls.append((model, timeout))
        if model == "a":
            raise httpx.ReadTimeout("slow")
        if model == "b":
            return R(503, {"error": {"message": "overloaded"}})
        return _ok("from c")

    monkeypatch.setattr(httpx, "post", fake_post)
    p = GeminiProvider("k", "a", 25, ["b", "c"], per_model_timeout=12)
    assert p.generate("s", [{"role": "user", "content": "q"}]) == "from c"
    assert [m for m, _ in calls] == ["a", "b", "c"]
    assert all(t <= 12 for _, t in calls)


def test_per_model_quota_tries_next_model(monkeypatch):
    def fake_post(url, json, timeout, headers):
        return R(429, {}) if "/models/a:" in url else _ok("ok")
    monkeypatch.setattr(httpx, "post", fake_post)
    assert GeminiProvider("k", "a", 25, ["b"]).generate("s", [{"role": "user", "content": "q"}]) == "ok"


def test_all_quota_exceeded_reports_quota(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: R(429, {}))
    with pytest.raises(AIUnavailable, match="^quota exceeded$"):
        GeminiProvider("k", "a", 25, ["b"]).generate("s", [{"role": "user", "content": "q"}])


def test_total_budget_is_respected(monkeypatch):
    import time as _t
    clock = {"now": 1000.0}
    monkeypatch.setattr(_t, "monotonic", lambda: clock["now"])
    seen = []

    def slow(url, json, timeout, headers):
        seen.append(timeout)
        clock["now"] += timeout  # each attempt burns its whole timeout
        raise httpx.ReadTimeout("slow")

    monkeypatch.setattr(httpx, "post", slow)
    with pytest.raises(AIUnavailable, match="timed out"):
        GeminiProvider("k", "a", 25, ["b", "c", "d"], per_model_timeout=12).generate("s", [{"role": "user", "content": "q"}], budget=25)
    # 12s + 12s used; the 1s left is under the 2s minimum, so no third attempt is started
    assert seen == [12, 12]
