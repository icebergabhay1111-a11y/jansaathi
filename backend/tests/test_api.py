"""Integration / journey tests against the real FastAPI app and database."""
from fastapi.testclient import TestClient

from app.ai import assistant as assistant_mod
from app.ai.provider import AIProvider, AIUnavailable
from app.main import app
from app.routers import public

from .conftest import H


# Journey F: guest browsing
def test_guest_can_browse_and_search(client):
    assert client.get("/api/health").json()["status"] == "ok"
    r = client.get("/api/schemes").json()
    assert r["total"] >= 20 and all("verification_status" in i for i in r["items"])
    assert client.get("/api/services").json()["total"] >= 20
    assert len(client.get("/api/rights").json()["items"]) >= 20


def test_filters(client):
    r = client.get("/api/schemes", params={"category": "agriculture"}).json()
    assert r["items"] and all("agriculture" in i["categories"] for i in r["items"])
    tn = client.get("/api/schemes", params={"level": "state", "state": "Tamil Nadu"}).json()["items"]
    assert [i["slug"] for i in tn] == ["tn-pudhumai-penn"]
    kerala = client.get("/api/schemes", params={"level": "state", "state": "Kerala"}).json()["items"]
    assert kerala == []
    page2 = client.get("/api/schemes", params={"size": 5, "page": 2}).json()
    assert page2["page"] == 2 and len(page2["items"]) == 5


# Journey A: student finds scholarships with sourced, explained recommendations
def test_student_scholarship_journey(client):
    q = client.get("/api/eligibility/questions", params={"categories": "education"}).json()["questions"]
    fields = [x["field"] for x in q]
    assert "study_level" in fields and "land_owner" not in fields
    body = {"interests": ["education"], "answers": {"state": "Uttar Pradesh", "age": 18, "occupation": "student", "study_level": "undergraduate_regular",
                                                   "class12_top20": True, "annual_income": 300000, "other_scholarship": False}}
    res = client.post("/api/eligibility/match", json=body).json()
    top = res["results"][0]
    assert top["slug"] == "central-sector-scholarship-college-university"
    assert top["label"] == "potential_match" and top["satisfied"] and not top["failed"]
    assert "not an official eligibility decision" in res["note"]
    detail = client.get(f"/api/schemes/{top['slug']}").json()
    assert detail["sources"] and detail["last_verified"] and detail["apply_url"].startswith("https://")


def test_income_over_limit_appears_ineligible(client):
    body = {"interests": ["education"], "answers": {"occupation": "student", "study_level": "undergraduate_regular", "class12_top20": True, "annual_income": 900000, "other_scholarship": False}}
    r = {x["slug"]: x for x in client.post("/api/eligibility/match", json=body).json()["results"]}
    assert r["central-sector-scholarship-college-university"]["label"] == "appears_ineligible"


def test_eligibility_input_validation(client):
    r = client.post("/api/eligibility/match", json={"answers": {"age": 500}})
    assert r.status_code == 422 and r.json()["errors"]
    r = client.post("/api/eligibility/match", json={"answers": {"state": "Atlantis"}})
    assert r.status_code == 422


# Journey H: unverified record warns
def test_unverified_record_shows_warning(client):
    d = client.get("/api/schemes/pm-kisan-samman-nidhi").json()
    assert d["verification_status"] == "needs_verification" and d["freshness"]["state"] == "unverified"
    assert d["benefit_amount"] is None


# Journey B: constitutional article -> grounded explanation (fallback mode, no AI key)
def test_article_search_and_assistant_fallback(client):
    hits = client.get("/api/search", params={"q": "Article 21"}).json()["results"]
    assert hits[0]["slug"] == "art-21"
    hi = client.get("/api/search", params={"q": "अनुच्छेद 21"}).json()["results"]
    assert hi[0]["slug"] == "art-21"
    a = client.post("/api/assistant/ask", json={"question": "Explain Article 21 in simple words", "lang": "en"}).json()
    assert a["mode"] == "fallback" and a["found_sources"] and any(s["slug"] == "art-21" for s in a["sources"])
    assert "not a government body" in a["disclaimer"]


# Journey J: AI provider fails -> rest keeps working
class Boom(AIProvider):
    name = "boom"

    def generate(self, system, messages, budget=None):
        raise AIUnavailable("quota exceeded")


class Fake(AIProvider):
    name = "fake"

    def generate(self, system, messages, budget=None):
        assert "SOURCE RECORDS" in messages[-1]["content"] and "Never invent" in system
        return "You may be able to apply [1]."


def test_ai_failure_falls_back(client, monkeypatch):
    monkeypatch.setattr(public, "get_provider", lambda: Boom())
    a = client.post("/api/assistant/ask", json={"question": "old age pension for my grandmother"}).json()
    assert a["mode"] == "fallback" and a["mode_reason"] == "quota exceeded" and a["sources"]
    assert client.get("/api/schemes").status_code == 200


def test_ai_success_is_grounded(client, monkeypatch):
    monkeypatch.setattr(public, "get_provider", lambda: Fake())
    a = client.post("/api/assistant/ask", json={"question": "free legal aid lawyer"}).json()
    assert a["mode"] == "ai" and a["sources"][0]["cited"] is True


def test_assistant_no_sources_says_so(client):
    a = client.post("/api/assistant/ask", json={"question": "qwxz zzkq plmn"}).json()
    assert not a["found_sources"] and "could not find" in a["answer"].lower()


# Journey G: Hindi search
def test_hindi_search(client):
    r = client.get("/api/search", params={"q": "किसान"}).json()["results"]
    assert any(x["slug"] == "pm-kisan-samman-nidhi" for x in r)
    assert client.get("/api/search", params={"q": "zzzzqqq"}).json()["suggestions"]


# Journey C: service -> official portal
def test_service_has_official_portal(client):
    d = client.get("/api/services/svc-rti").json()
    assert d["portal_url"].endswith(".gov.in") and d["fee"]
    assert client.get("/api/services/does-not-exist").status_code == 404


# Journey D: complaint draft + grievance instructions
def test_complaint_draft(client):
    g = client.get("/api/guides/complaint-consumer").json()
    assert any(a.get("url") for a in g["authorities"])
    d = client.post("/api/drafts/complaint", json={"authority": "Company grievance officer", "subject": "Refund for defective phone",
                                                   "facts": "I bought a phone on 1 Oct and it stopped working within a week.", "relief": "Refund or replacement",
                                                   "applicant_name": "Asha", "contact": "asha@example.com"}).json()
    assert d["submitted"] is False and d["draft"].startswith("DRAFT")
    bad = client.post("/api/drafts/complaint", json={"authority": "x"})
    assert bad.status_code == 422
    r = client.post("/api/drafts/rti", json={"public_authority": "Ministry of Education", "information_sought": ["Copy of rules"], "applicant_name": "A", "address": "Vellore, TN"}).json()
    assert "Section 6(1)" in r["draft"]


def test_reports(client):
    r = client.post("/api/reports", json={"item_type": "scheme", "item_slug": "pm-kisan-samman-nidhi", "kind": "outdated", "message": "Instalment info changed"})
    assert r.status_code == 201


# Accounts: save + delete personal data
def test_account_save_export_delete():
    c = TestClient(app)
    assert c.post("/api/auth/register", json={"email": "Citizen@Test.in", "password": "short"}, headers=H).status_code == 422
    r = c.post("/api/auth/register", json={"email": "citizen@test.in", "password": "a-long-password"}, headers=H)
    assert r.status_code == 201 and r.json()["role"] == "user"
    assert c.post("/api/me/saved", json={"item_type": "scheme", "item_slug": "atal-pension-yojana"}).status_code == 403  # CSRF header required
    s = c.post("/api/me/saved", json={"item_type": "scheme", "item_slug": "atal-pension-yojana"}, headers=H)
    assert s.status_code == 201 and s.json()["status_source"] == "user_entered"
    c.patch(f"/api/me/saved/{s.json()['id']}", json={"my_status": "applied"}, headers=H)
    c.post("/api/me/reminders", json={"title": "Renew", "due_date": "2027-01-01"}, headers=H)
    exp = c.get("/api/me/export").json()
    assert exp["saved"][0]["my_status"] == "applied" and exp["reminders"]
    assert c.delete("/api/auth/account", headers=H).json()["deleted"]
    c2 = TestClient(app)
    assert c2.post("/api/auth/login", json={"email": "citizen@test.in", "password": "a-long-password"}, headers=H).status_code == 401


def test_password_not_stored_plaintext():
    from app.db import SessionLocal
    from app.models import User
    db = SessionLocal()
    u = db.query(User).filter_by(email="admin@test.in").one()
    assert "admin-password-123" not in u.password_hash and u.password_hash.startswith("$2")
    db.close()


# Journey I: unauthorised admin access denied
def test_admin_requires_auth(client):
    assert client.get("/api/admin/overview").status_code == 401
    c = TestClient(app)
    c.post("/api/auth/register", json={"email": "plain@test.in", "password": "a-long-password"}, headers=H)
    assert c.get("/api/admin/overview").status_code == 403
    assert c.post("/api/admin/import", json={"kind": "scheme", "records": [{}]}, headers=H).status_code == 403


# Journey E: admin updates a scheme and checks publication workflow
def test_admin_workflow(admin_client, editor_client, client):
    new = {"slug": "test-scheme", "name": "Test Scheme", "summary": "A test", "ministry": "Test Ministry", "categories": ["education"],
           "sources": [{"url": "https://www.india.gov.in", "organisation": "NPI", "title": "x", "type": "official_portal"}]}
    r = editor_client.post("/api/admin/records/scheme", json={"data": new}, headers=H)
    assert r.status_code == 201 and r.json()["status"] == "draft"
    assert client.get("/api/schemes/test-scheme").status_code == 404  # drafts never public
    assert editor_client.post("/api/admin/records/scheme/test-scheme/transition", json={"to": "source_review"}, headers=H).status_code == 200
    # cannot verify without recording verification
    assert editor_client.post("/api/admin/records/scheme/test-scheme/transition", json={"to": "verified"}, headers=H).status_code == 409
    editor_client.post("/api/admin/records/scheme/test-scheme/verify", json={"verification_status": "verified", "last_verified": "2026-10-01", "note": "Checked official page"}, headers=H)
    assert editor_client.post("/api/admin/records/scheme/test-scheme/transition", json={"to": "verified"}, headers=H).status_code == 200
    # editor cannot approve/publish
    assert editor_client.post("/api/admin/records/scheme/test-scheme/transition", json={"to": "approved"}, headers=H).status_code == 403
    assert admin_client.post("/api/admin/records/scheme/test-scheme/transition", json={"to": "approved"}, headers=H).status_code == 200
    assert admin_client.post("/api/admin/records/scheme/test-scheme/transition", json={"to": "published"}, headers=H).status_code == 200
    assert client.get("/api/schemes/test-scheme").status_code == 200
    # editor edit of published record sends it back to review
    up = editor_client.put("/api/admin/records/scheme/test-scheme", json={"data": {"summary": "Changed"}, "note": "fix"}, headers=H).json()
    assert up["status"] == "source_review" and up["version"] == 2
    assert client.get("/api/schemes/test-scheme").status_code == 404
    hist = admin_client.get("/api/admin/records/scheme/test-scheme/history").json()["items"]
    assert [h["version"] for h in hist] == [2, 1]
    assert any(a["action"] == "transition" for a in admin_client.get("/api/admin/audit").json()["items"])
    assert editor_client.get("/api/admin/audit").status_code == 403
    # bad url rejected
    bad = editor_client.put("/api/admin/records/scheme/test-scheme", json={"data": {"apply_url": "https://apply-here.biz"}}, headers=H)
    assert bad.status_code == 422


def test_admin_import_lands_as_draft(editor_client, client):
    rec = {"slug": "imported-one", "name": "Imported", "summary": "x", "ministry": "M", "categories": ["housing"], "status": "published",
           "sources": [{"url": "https://www.india.gov.in", "organisation": "NPI", "title": "x"}]}
    r = editor_client.post("/api/admin/import", json={"kind": "scheme", "records": [rec, {"slug": "bad"}]}, headers=H).json()
    assert r["created"] == 1 and len(r["errors"]) == 1
    assert client.get("/api/schemes/imported-one").status_code == 404
    assert editor_client.get("/api/admin/imports").json()["items"]


def test_review_queue_lists_unverified(editor_client):
    items = editor_client.get("/api/admin/review-queue").json()["items"]
    assert any(i["slug"] == "pm-kisan-samman-nidhi" for i in items)
