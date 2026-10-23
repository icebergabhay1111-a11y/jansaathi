"""Tests for: optional category + any-of rules, document checklist, tracker fields, FIR/consumer templates,
voice transcription endpoint, Tamil assistant, seed sync, Gemini model fallback."""
import base64

import httpx
import pytest
from fastapi.testclient import TestClient

from app.ai.provider import AIProvider, AIUnavailable, GeminiProvider
from app.documents import checklist, classify
from app.eligibility import _check
from app.main import app
from app.routers import public

from .conftest import H


# ---------- 1. eligibility: optional category, any-of rules ----------
def test_any_rule():
    rule = {"op": "any", "label": "x", "rules": [{"field": "gender", "op": "eq", "value": "female"},
                                                  {"field": "social_category", "op": "in", "value": ["sc", "st"]}]}
    assert _check(rule, {"gender": "female"}) == "pass"
    assert _check(rule, {"social_category": "st"}) == "pass"
    assert _check(rule, {"gender": "male", "social_category": "general"}) == "fail"
    assert _check(rule, {"gender": "male"}) == "unknown"   # category not given → never ruled out
    assert _check(rule, {}) == "unknown"


def test_standup_india_with_and_without_category(client):
    base = {"interests": ["entrepreneurship"], "answers": {"age": 30, "gender": "male", "occupation": "self_employed"}}
    r = {x["slug"]: x for x in client.post("/api/eligibility/match", json=base).json()["results"]}
    assert r["stand-up-india"]["label"] in ("more_info", "rules_need_verification")
    base["answers"]["social_category"] = "sc"
    r = {x["slug"]: x for x in client.post("/api/eligibility/match", json=base).json()["results"]}
    assert r["stand-up-india"]["failed"] == []
    qs = {q["field"]: q for q in client.get("/api/eligibility/questions", params={"categories": "entrepreneurship"}).json()["questions"]}
    assert qs["social_category"]["sensitive"] is True and "optional" in qs["social_category"]["why"].lower()
    assert client.post("/api/eligibility/match", json={"answers": {"social_category": "brahmin"}}).status_code == 422


# ---------- 3. document checklist ----------
def test_document_classification():
    assert classify("Family income certificate (fresh applicants)")["key"] == "income_certificate"
    assert classify("Savings bank account in the student's name (for DBT)")["key"] == "bank_account"
    assert classify("Aadhaar-based e-KYC")["key"] == "aadhaar"
    assert classify("Something unusual") is None
    merged = checklist(["Savings bank account", "Bank or post office account for DBT wages"])
    assert len(merged) == 1


def test_scheme_detail_has_checklist_with_where_to_get(client):
    d = client.get("/api/schemes/central-sector-scholarship-college-university").json()
    keys = [c["doc"]["key"] for c in d["document_checklist"] if c["doc"]]
    assert {"marksheet", "income_certificate", "bank_account"} <= set(keys)
    inc = next(c for c in d["document_checklist"] if c["doc"] and c["doc"]["key"] == "income_certificate")
    assert inc["doc"]["how"] and inc["doc"]["links"][0]["href"] == "/services/svc-income-certificate"
    # every internal link in the registry resolves to a published page
    for item in client.get("/api/documents").json()["items"]:
        for link in item["links"]:
            kind, slug = link["href"].strip("/").split("/") if link["href"] != "/offices" else ("offices", None)
            if slug:
                assert client.get(f"/api/{kind}/{slug}").status_code == 200, link


# ---------- 4. tracker ----------
def test_tracker_fields_and_linked_reminders():
    c = TestClient(app)
    c.post("/api/auth/register", json={"email": "tracker@test.in", "password": "a-long-password"}, headers=H)
    s = c.post("/api/me/saved", json={"item_type": "scheme", "item_slug": "pm-kisan-samman-nidhi"}, headers=H).json()
    upd = c.patch(f"/api/me/saved/{s['id']}", json={"my_status": "applied", "applied_on": "2026-10-01", "reference_no": " PMK-123 "}, headers=H).json()
    assert upd["applied_on"] == "2026-10-01" and upd["reference_no"] == "PMK-123"
    assert c.patch(f"/api/me/saved/{s['id']}", json={"applied_on": "2099-01-01"}, headers=H).status_code == 422
    c.post("/api/me/reminders", json={"title": "Check status", "due_date": "2026-11-15", "related_slug": "pm-kisan-samman-nidhi"}, headers=H)
    item = c.get("/api/me/saved").json()["items"][0]
    assert item["reminders"][0]["title"] == "Check status"
    assert c.post("/api/me/reminders", json={"title": "far", "due_date": "2099-01-01"}, headers=H).status_code == 422
    c.delete("/api/auth/account", headers=H)


# ---------- 5. quick cards / templates ----------
def test_fir_guide_and_templates(client):
    g = client.get("/api/guides/guide-fir-refusal").json()
    assert any("173(4)" in l["law"] for l in g["law_basis"])
    d = client.post("/api/drafts/fir-refusal", json={
        "district": "Vellore", "police_station": "Katpadi", "incident_date": "1 Oct 2026", "incident_place": "Katpadi bus stand",
        "facts": "Two men on a motorbike snatched my phone near the bus stand.", "refusal_details": "The duty officer refused to write it down.",
        "applicant_name": "Asha", "address": "12 Main Road, Vellore", "contact": "asha@example.com"}).json()
    assert d["submitted"] is False and "Superintendent of Police" in d["draft"] and "173(4)" in d["draft"]
    c = client.post("/api/drafts/consumer-notice", json={
        "company": "ABC Electronics", "product": "Phone", "purchase_date": "1 Oct 2026", "problem": "The phone stopped charging after five days of use.",
        "relief": "Replace the phone or refund", "applicant_name": "Asha", "contact": "asha@example.com", "days": 15}).json()
    assert "Consumer Protection Act, 2019" in c["draft"] and "15 days" in c["draft"]
    assert client.post("/api/drafts/consumer-notice", json={"company": "x"}).status_code == 422
    assert client.get("/api/search", params={"q": "FIR"}).json()["results"][0]["slug"] == "guide-fir-refusal"


# ---------- 2. voice ----------
class FakeVoice(AIProvider):
    name = "fake"

    def __init__(self):
        self.seen = None

    def generate(self, system, messages):
        if "search keywords" in system:
            return "old age pension"
        return "பதில் [1]"

    def transcribe(self, audio, mime_type, language_hint):
        self.seen = (len(audio), mime_type, language_hint)
        return "  முதியோர் ஓய்வூதியம்  "


def test_transcribe_requires_ai(client):
    audio = base64.b64encode(b"\x1aE\xdf\xa3" + b"0" * 2000).decode()
    r = client.post("/api/assistant/transcribe", json={"audio_base64": audio, "mime_type": "audio/webm;codecs=opus", "lang": "ta"})
    assert r.status_code == 503 and "type" in r.json()["detail"]


def test_transcribe_with_provider(client, monkeypatch):
    fake = FakeVoice()
    monkeypatch.setattr(public, "get_provider", lambda: fake)
    audio = base64.b64encode(b"0" * 3000).decode()
    r = client.post("/api/assistant/transcribe", json={"audio_base64": audio, "mime_type": "audio/webm;codecs=opus", "lang": "ta"}).json()
    assert r["text"] == "முதியோர் ஓய்வூதியம்" and fake.seen == (3000, "audio/webm", "Tamil")
    assert client.post("/api/assistant/transcribe", json={"audio_base64": base64.b64encode(b"x" * 10).decode(), "mime_type": "audio/webm"}).status_code == 422
    assert client.post("/api/assistant/transcribe", json={"audio_base64": audio, "mime_type": "video/mp4"}).status_code == 422


def test_tamil_question_retrieves_via_keywords(client, monkeypatch):
    monkeypatch.setattr(public, "get_provider", lambda: FakeVoice())
    a = client.post("/api/assistant/ask", json={"question": "என் பாட்டிக்கு முதியோர் உதவி வேண்டும்", "lang": "ta"}).json()
    assert a["search_keywords"] == "old age pension" and a["mode"] == "ai"
    assert any(s["slug"] == "nsap-old-age-pension" for s in a["sources"])
    assert "அரசு அமைப்பு அல்ல" in a["disclaimer"]


def test_tamil_without_ai_uses_tamil_keywords(client):
    a = client.post("/api/assistant/ask", json={"question": "ஓய்வூதியம்", "lang": "ta"}).json()
    assert a["mode"] == "fallback" and a["found_sources"]
    assert client.post("/api/assistant/ask", json={"question": "hello", "lang": "fr"}).status_code == 422


# ---------- seed sync ----------
def test_seed_sync_respects_human_edits(admin_client):
    from app.db import SessionLocal
    from app.importer import sync_seed
    from app.models import Scheme
    db = SessionLocal()
    s = db.query(Scheme).filter_by(slug="pm-jan-dhan-yojana").one()
    s.summary, s.updated_by = "Edited by an admin", "admin@test.in"
    seed_owned = db.query(Scheme).filter_by(slug="pm-ujjwala-yojana").one()
    seed_owned.summary = "stale seed text"
    db.commit()
    out = sync_seed(db)
    db.expire_all()
    assert db.query(Scheme).filter_by(slug="pm-jan-dhan-yojana").one().summary == "Edited by an admin"
    assert db.query(Scheme).filter_by(slug="pm-ujjwala-yojana").one().summary != "stale seed text"
    assert out["scheme"]["kept_human_edits"] >= 1 and out["scheme"]["refreshed"] >= 1
    again = sync_seed(db)
    assert again["scheme"]["refreshed"] == 0 and again["scheme"]["added"] == 0
    db.close()


# ---------- Gemini model fallback ----------
class R:
    def __init__(self, status, data=None):
        self.status_code, self._d = status, data or {}

    def json(self):
        return self._d


def test_gemini_falls_back_to_next_model_and_skips_thoughts(monkeypatch):
    calls = []

    def fake_post(url, json, timeout, headers):
        calls.append((url, json["generationConfig"]))
        if "gemini-3.8-flash" in url:
            return R(404)
        return R(200, {"candidates": [{"content": {"parts": [{"text": "thinking...", "thought": True}, {"text": "Answer"}]}}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    p = GeminiProvider("k", "gemini-3.8-flash", 5, ["gemini-3.6-flash"])
    assert p.generate("s", [{"role": "user", "content": "q"}]) == "Answer"
    assert "gemini-3.6-flash" in calls[1][0] and calls[1][1]["thinkingConfig"]["thinkingLevel"] == "low"


def test_gemini_all_models_unavailable(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: R(404))
    with pytest.raises(AIUnavailable, match="404"):
        GeminiProvider("k", "a", 5, ["b"]).generate("s", [{"role": "user", "content": "q"}])


def test_gemini_transcribe_payload(monkeypatch):
    seen = {}

    def fake_post(url, json, timeout, headers):
        seen.update(json)
        return R(200, {"candidates": [{"content": {"parts": [{"text": "नमस्ते"}]}}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    out = GeminiProvider("k", "gemini-3.8-flash", 5).transcribe(b"abc", "audio/webm", "Hindi")
    part = seen["contents"][0]["parts"][1]["inline_data"]
    assert out == "नमस्ते" and part["mime_type"] == "audio/webm" and base64.b64decode(part["data"]) == b"abc"
