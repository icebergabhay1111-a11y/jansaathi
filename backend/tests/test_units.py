"""Unit tests: eligibility rules, jurisdiction, freshness, search, source validation."""
from datetime import date
from types import SimpleNamespace

from app.eligibility import _check, evaluate, jurisdiction_ok, match, relevant_questions
from app.freshness import application_window, freshness
from app.importer import is_official_url, validate_record
from app.search import expand, search
from app.seed.guides import GUIDES
from app.seed.rights import RIGHTS
from app.seed.schemes import SCHEMES
from app.seed.services import SERVICES


def scheme(**kw):
    base = dict(slug="s", name="S", name_hi=None, summary="", states=["ALL"], categories=["education"], eligibility_rules=[],
                verification_status="verified", opens_on=None, closes_on=None, info_url=None, apply_url=None)
    base.update(kw)
    return SimpleNamespace(**base)


def test_rule_ops():
    assert _check({"field": "age", "op": "between", "value": [18, 40]}, {"age": 30}) == "pass"
    assert _check({"field": "age", "op": "between", "value": [18, 40]}, {"age": 41}) == "fail"
    assert _check({"field": "age", "op": "gte", "value": 70}, {}) == "unknown"
    assert _check({"field": "annual_income", "op": "lte", "value": 450000}, {"annual_income": 450000}) == "pass"
    assert _check({"field": "x", "op": "is_false"}, {"x": True}) == "fail"
    assert _check({"field": "occupation", "op": "in", "value": ["a"]}, {"occupation": "b"}) == "fail"
    assert _check({"field": "listed", "op": "manual"}, {"listed": True}) == "unknown"  # manual can never be self-certified


def test_jurisdiction():
    assert jurisdiction_ok(["ALL"], None) == "pass"
    assert jurisdiction_ok(["Tamil Nadu"], "Tamil Nadu") == "pass"
    assert jurisdiction_ok(["Tamil Nadu"], "Kerala") == "fail"
    assert jurisdiction_ok(["Tamil Nadu"], None) == "unknown"


def test_labels_never_say_eligible():
    s = scheme(eligibility_rules=[{"field": "age", "op": "gte", "value": 18, "label": "adult"}])
    assert evaluate(s, {"age": 20})["label"] == "potential_match"
    assert evaluate(s, {"age": 10})["label"] == "appears_ineligible"
    assert evaluate(s, {})["label"] == "more_info"
    assert evaluate(scheme(verification_status="needs_verification", eligibility_rules=[]), {"state": "Delhi"})["label"] == "rules_need_verification"
    closed = scheme(closes_on=date(2020, 1, 1))
    assert evaluate(closed, {"state": "Delhi"})["label"] == "period_may_have_closed"
    for r in (evaluate(s, {"age": 20}),):
        assert "eligible" not in r["label_text"].lower().replace("ineligible", "")


def test_match_orders_and_explains():
    a = scheme(slug="a", name="A", eligibility_rules=[{"field": "age", "op": "gte", "value": 18, "label": "adult"}])
    b = scheme(slug="b", name="B", eligibility_rules=[{"field": "age", "op": "lte", "value": 10, "label": "child"}])
    res = match([a, b], {"age": 30}, ["education"])
    assert [r["slug"] for r in res] == ["a", "b"]
    assert res[0]["satisfied"] and res[1]["failed"]


def test_relevant_questions_only_asks_needed():
    a = scheme(categories=["agriculture"], eligibility_rules=[{"field": "land_owner", "op": "is_true", "label": "x"}])
    b = scheme(categories=["education"], eligibility_rules=[{"field": "study_level", "op": "in", "value": [], "label": "y"}])
    fields = [q["field"] for q in relevant_questions([a, b], ["agriculture"])]
    assert "land_owner" in fields and "study_level" not in fields and fields[0] == "state"


def test_sensitive_questions_are_optional_and_explained():
    from app.eligibility import QUESTIONS
    for q in QUESTIONS.values():
        assert q["why"]
    assert QUESTIONS["annual_income"]["sensitive"] and QUESTIONS["gender"]["sensitive"]
    assert "caste" not in QUESTIONS and "religion" not in QUESTIONS


def test_freshness_states():
    assert freshness(None, 90, "needs_verification")["state"] == "unverified"
    assert freshness(date(2026, 1, 1), 90, "verified", today=date(2026, 3, 1))["state"] == "fresh"
    stale = freshness(date(2026, 1, 1), 90, "verified", today=date(2026, 6, 1))
    assert stale["state"] == "stale" and "may have changed" in stale["message"]


def test_application_window():
    t = date(2026, 5, 1)
    assert application_window(None, date(2026, 4, 1), t) == "closed_maybe"
    assert application_window(date(2026, 6, 1), None, t) == "not_yet_open"
    assert application_window(None, None, t) == "unknown"


def test_search_bilingual_and_fuzzy():
    s1 = scheme(slug="x", name="Central Sector Scholarship", name_hi="छात्रवृत्ति योजना", aliases=[], summary="merit scholarship", summary_hi=None,
                ministry="Education", beneficiaries=[], eligibility_text=[], benefit_type="", documents=[])
    s2 = scheme(slug="y", name="Crop insurance", name_hi=None, aliases=[], summary="farmers", summary_hi=None,
                ministry="Agri", beneficiaries=[], eligibility_text=[], benefit_type="", documents=[], categories=["agriculture"])
    assert search({"scheme": [s1, s2]}, "छात्रवृत्ति")[0]["obj"].slug == "x"
    assert search({"scheme": [s1, s2]}, "scholarship")[0]["obj"].slug == "x"
    assert search({"scheme": [s1, s2]}, "scolarship")[0]["obj"].slug == "x"  # misspelling
    assert "__article_21" in expand("अनुच्छेद 21")


def test_official_url_validation():
    assert is_official_url("https://pmkisan.gov.in")
    assert is_official_url("https://nfsa.gov.in")
    assert not is_official_url("http://pmkisan.gov.in")
    assert not is_official_url("https://pmkisan-gov.in.example.com")
    assert not is_official_url("https://free-schemes-help.com")


def test_all_seed_records_pass_validation_and_no_unverified_amounts():
    for kind, recs in (("scheme", SCHEMES), ("right", RIGHTS), ("guide", GUIDES), ("service", SERVICES)):
        for r in recs:
            assert validate_record(kind, r) == [], (kind, r["slug"])
    for s in SCHEMES:
        if s["verification_status"] == "needs_verification":
            assert not s.get("benefit_amount"), s["slug"]


def test_validation_rejects_fabricated_links():
    bad = {**SCHEMES[0], "apply_url": "https://scholarship-apply-now.com"}
    assert any("not an official" in e for e in validate_record("scheme", bad))
    no_src = {**SCHEMES[0], "sources": []}
    assert validate_record("scheme", no_src)


def _req(peer, headers=None):
    from starlette.requests import Request
    hdrs = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    return Request({"type": "http", "client": (peer, 1234), "headers": hdrs})


def test_client_ip_behind_render_and_cloudflare():
    from app.security import client_ip
    # Cloudflare header wins (cannot be spoofed by the client when traffic passes Cloudflare)
    assert client_ip(_req("127.0.0.1", {"cf-connecting-ip": "49.36.10.5", "x-forwarded-for": "1.1.1.1, 49.36.10.5, 10.24.217.11"})) == "49.36.10.5"
    # Without it: right-most public hop, ignoring internal proxies and client-supplied prefixes
    assert client_ip(_req("127.0.0.1", {"x-forwarded-for": "8.8.8.8, 49.36.10.5, 10.24.217.11"})) == "49.36.10.5"
    # Private peer (load balancer / docker network) is treated as an internal hop too
    assert client_ip(_req("10.24.217.11", {"x-forwarded-for": "49.36.10.5"})) == "49.36.10.5"
    # A directly connected public client cannot spoof headers
    assert client_ip(_req("49.36.10.5", {"x-forwarded-for": "8.8.8.8", "cf-connecting-ip": "8.8.4.4"})) == "49.36.10.5"
    # Local development without any proxy
    assert client_ip(_req("127.0.0.1")) == "127.0.0.1"
    # Garbage headers are ignored
    assert client_ip(_req("127.0.0.1", {"cf-connecting-ip": "not-an-ip", "x-forwarded-for": "junk"})) == "127.0.0.1"


def test_admin_password_rule(capsys):
    from app.cli import upsert_admin
    from app.db import SessionLocal
    db = SessionLocal()
    assert upsert_admin(db, "short@test.in", "short") is False
    assert "NOT created" in capsys.readouterr().out
    db.close()
