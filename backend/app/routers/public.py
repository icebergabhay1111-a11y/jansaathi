"""Public, guest-accessible endpoints. Only PUBLISHED records are ever returned."""
from __future__ import annotations

import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import drafts
from ..ai.assistant import answer
from ..ai.provider import get_provider
from ..config import get_settings
from ..db import get_db
from ..eligibility import LABELS, QUESTIONS, match, relevant_questions
from ..models import Guide, Report, RightArticle, Scheme, Service
from ..search import search
from ..security import client_ip, limiter
from ..serialize import card, full

router = APIRouter(prefix="/api")

STATES = ["Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chandigarh", "Chhattisgarh",
          "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jammu and Kashmir",
          "Jharkhand", "Karnataka", "Kerala", "Ladakh", "Lakshadweep", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
          "Mizoram", "Nagaland", "Odisha", "Puducherry", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
          "Uttar Pradesh", "Uttarakhand", "West Bengal"]

CATEGORIES = {
    "education": ("Education & scholarships", "शिक्षा और छात्रवृत्ति"), "healthcare": ("Healthcare", "स्वास्थ्य"),
    "housing": ("Housing", "आवास"), "food_security": ("Food & ration", "भोजन और राशन"),
    "employment": ("Employment & skills", "रोज़गार और कौशल"), "agriculture": ("Agriculture & farmers", "कृषि और किसान"),
    "women_child": ("Women & children", "महिला और बाल"), "senior_citizens": ("Senior citizens", "वरिष्ठ नागरिक"),
    "disability": ("Disability", "दिव्यांगता"), "social_security": ("Social security & pensions", "सामाजिक सुरक्षा और पेंशन"),
    "financial_inclusion": ("Banking & insurance", "बैंकिंग और बीमा"), "entrepreneurship": ("Business & MSME", "व्यवसाय और MSME"),
    "labour": ("Workers & labour", "श्रमिक"), "rural_development": ("Rural development", "ग्रामीण विकास"),
    "urban_development": ("Urban development", "शहरी विकास"), "utilities": ("Electricity, gas & utilities", "बिजली, गैस और सुविधाएँ"),
    "sc_st_welfare": ("SC/ST welfare", "अनुसूचित जाति/जनजाति कल्याण"), "disaster_relief": ("Disaster relief", "आपदा राहत"),
    "youth": ("Youth & sports", "युवा और खेल"), "legal_aid": ("Legal aid", "विधिक सहायता"),
}


def published(db: Session, Model):
    return list(db.scalars(select(Model).where(Model.status == "published")))


def collections(db: Session) -> dict:
    return {"scheme": published(db, Scheme), "right": published(db, RightArticle), "guide": published(db, Guide), "service": published(db, Service)}


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "ok", "db": "ok", "ai_configured": get_provider() is not None}


@router.get("/meta")
def meta(db: Session = Depends(get_db)):
    schemes = published(db, Scheme)
    counts = {k: sum(1 for s in schemes if k in s.categories) for k in CATEGORIES}
    vcounts = {}
    for M in (Scheme, RightArticle, Guide, Service):
        for o in published(db, M):
            vcounts[o.verification_status] = vcounts.get(o.verification_status, 0) + 1
    return {
        "states": STATES,
        "categories": [{"id": k, "en": v[0], "hi": v[1], "count": counts[k]} for k, v in CATEGORIES.items()],
        "languages": [{"code": "en", "name": "English", "status": "supported"}, {"code": "hi", "name": "हिन्दी", "status": "supported"},
                      {"code": "ta", "name": "தமிழ்", "status": "planned"}],
        "ai_configured": get_provider() is not None,
        "labels": LABELS,
        "verification_counts": vcounts,
        "coverage_note": f"{len(schemes)} schemes currently listed. This is NOT a complete list of Indian government schemes.",
    }


def paginate(items: list, page: int, size: int) -> dict:
    total = len(items)
    pages = max(1, math.ceil(total / size))
    page = min(max(1, page), pages)
    return {"items": items[(page - 1) * size: page * size], "total": total, "page": page, "pages": pages, "size": size}


@router.get("/schemes")
def list_schemes(q: str | None = None, category: str | None = None, level: str | None = None, state: str | None = None,
                 verification: str | None = None, sort: str = "relevance", page: int = 1, size: int = Query(12, le=50), db: Session = Depends(get_db)):
    schemes = published(db, Scheme)
    if category:
        schemes = [s for s in schemes if category in s.categories]
    if level:
        schemes = [s for s in schemes if s.level == level]
    if state:
        schemes = [s for s in schemes if "ALL" in s.states or state in s.states]
    if verification:
        schemes = [s for s in schemes if s.verification_status == verification]
    why = {}
    if q:
        hits = search({"scheme": schemes}, q, limit=200)
        schemes = [h["obj"] for h in hits]
        why = {h["obj"].slug: h["why"] for h in hits}
    elif sort == "name":
        schemes.sort(key=lambda s: s.name)
    elif sort == "updated":
        schemes.sort(key=lambda s: s.updated_at, reverse=True)
    else:
        rank = {"verified": 0, "reviewed": 1, "needs_verification": 2}
        schemes.sort(key=lambda s: (rank.get(s.verification_status, 3), s.name))
    items = [{**card("scheme", s), "why": why.get(s.slug, [])} for s in schemes]
    return paginate(items, page, size)


def _get(db: Session, Model, slug: str):
    obj = db.scalar(select(Model).where(Model.slug == slug, Model.status == "published"))
    if not obj:
        raise HTTPException(404, "This record was not found or is not published.")
    return obj


@router.get("/schemes/{slug}")
def get_scheme(slug: str, db: Session = Depends(get_db)):
    s = _get(db, Scheme, slug)
    related = [card("scheme", o) for o in published(db, Scheme) if o.slug != s.slug and set(o.categories) & set(s.categories)][:4]
    return {**full(s), "related": related}


@router.get("/rights")
def list_rights(q: str | None = None, group: str | None = None, db: Session = Depends(get_db)):
    arts = sorted(published(db, RightArticle), key=lambda a: a.order)
    if group:
        arts = [a for a in arts if a.group == group]
    if q:
        arts = [h["obj"] for h in search({"right": arts}, q, limit=100)]
    groups = []
    for a in sorted(published(db, RightArticle), key=lambda a: a.order):
        if a.group not in groups:
            groups.append(a.group)
    return {"items": [card("right", a) for a in arts], "groups": groups}


@router.get("/rights/{slug}")
def get_right(slug: str, db: Session = Depends(get_db)):
    a = _get(db, RightArticle, slug)
    slugs = set(a.related)
    rel = [card("right", o) for o in published(db, RightArticle) if o.slug in slugs] + [card("guide", o) for o in published(db, Guide) if o.slug in slugs]
    return {**full(a), "related_items": rel}


@router.get("/guides")
def list_guides(kind: str | None = None, q: str | None = None, db: Session = Depends(get_db)):
    gs = published(db, Guide)
    if kind:
        gs = [g for g in gs if g.kind == kind]
    if q:
        gs = [h["obj"] for h in search({"guide": gs}, q, limit=100)]
    return {"items": [card("guide", g) for g in gs]}


@router.get("/guides/{slug}")
def get_guide(slug: str, db: Session = Depends(get_db)):
    return full(_get(db, Guide, slug))


@router.get("/services")
def list_services(q: str | None = None, online: str | None = None, level: str | None = None, page: int = 1, size: int = Query(24, le=50), db: Session = Depends(get_db)):
    ss = published(db, Service)
    if online:
        ss = [s for s in ss if s.online == online]
    if level:
        ss = [s for s in ss if s.level == level]
    why = {}
    if q:
        hits = search({"service": ss}, q, limit=200)
        ss = [h["obj"] for h in hits]
        why = {h["obj"].slug: h["why"] for h in hits}
    else:
        ss.sort(key=lambda s: (not s.popular, s.name))
    return paginate([{**card("service", s), "why": why.get(s.slug, [])} for s in ss], page, size)


@router.get("/services/{slug}")
def get_service(slug: str, db: Session = Depends(get_db)):
    return full(_get(db, Service, slug))


@router.get("/search")
def global_search(q: str = Query(..., min_length=1, max_length=200), type: str | None = None, db: Session = Depends(get_db)):
    cols = collections(db)
    if type:
        cols = {k: v for k, v in cols.items() if k == type}
    hits = search(cols, q, limit=30)
    results = [{**card(h["kind"], h["obj"]), "score": h["score"], "why": h["why"]} for h in hits]
    suggestions = [] if results else ["scholarship", "pension", "ration card", "Article 21", "free legal aid", "RTI", "income certificate"]
    return {"query": q, "results": results, "suggestions": suggestions}


@router.get("/updates")
def updates(db: Session = Depends(get_db)):
    items = []
    for kind, M in (("scheme", Scheme), ("service", Service), ("guide", Guide)):
        for o in published(db, M):
            if o.verification_status in ("verified", "reviewed") and o.last_verified:
                items.append({**card(kind, o), "note": o.verification_note})
    items.sort(key=lambda x: x["last_verified"] or "", reverse=True)
    return {"items": items[:6]}


# ---------------- Eligibility ----------------
@router.get("/eligibility/questions")
def eligibility_questions(categories: str | None = None, db: Session = Depends(get_db)):
    interests = [c for c in (categories or "").split(",") if c]
    return {"questions": relevant_questions(published(db, Scheme), interests)}


class MatchIn(BaseModel):
    answers: dict = Field(default_factory=dict)
    interests: list[str] = Field(default_factory=list)

    @field_validator("answers")
    @classmethod
    def clean_answers(cls, v: dict) -> dict:
        out = {}
        for k, val in v.items():
            if k not in QUESTIONS or val in (None, ""):
                continue
            q = QUESTIONS[k]
            if q["type"] == "number":
                try:
                    num = float(val)
                except (TypeError, ValueError):
                    raise ValueError(f"'{k}' must be a number")
                if not (q["min"] <= num <= q["max"]):
                    raise ValueError(f"'{k}' must be between {q['min']} and {q['max']}")
                out[k] = num
            elif q["type"] == "bool":
                if not isinstance(val, bool):
                    raise ValueError(f"'{k}' must be true or false")
                out[k] = val
            elif q["type"] == "choice":
                if val not in q["options"]:
                    raise ValueError(f"'{k}' has an invalid option")
                out[k] = val
            elif q["type"] == "state":
                if val not in STATES:
                    raise ValueError("Unknown state/UT")
                out[k] = val
        return out


@router.post("/eligibility/match")
def eligibility_match(body: MatchIn, db: Session = Depends(get_db)):
    results = match(published(db, Scheme), body.answers, body.interests)
    return {"results": results, "answers_used": body.answers,
            "note": "These are indications based on your answers and documented rules — not an official eligibility decision. Only the responsible government authority can decide eligibility."}


# ---------------- Assistant ----------------
class AskIn(BaseModel):
    question: str = Field(min_length=2, max_length=1500)
    history: list[dict] = Field(default_factory=list, max_length=12)
    lang: str = "en"


@router.post("/assistant/ask")
def ask(body: AskIn, request: Request, db: Session = Depends(get_db)):
    limiter.check(f"chat:{client_ip(request)}", get_settings().rate_limit_chat_per_min)
    history = [{"role": m.get("role"), "content": str(m.get("content", ""))[:3000]} for m in body.history if m.get("role") in ("user", "assistant")]
    return answer(get_provider(), collections(db), body.question.strip(), history, body.lang)


# ---------------- Drafts ----------------
class RTIIn(BaseModel):
    public_authority: str = Field(min_length=3, max_length=300)
    information_sought: list[str] = Field(min_length=1, max_length=10)
    applicant_name: str = Field(min_length=1, max_length=120)
    address: str = Field(min_length=5, max_length=400)
    bpl: bool = False


class ComplaintIn(BaseModel):
    authority: str = Field(min_length=3, max_length=300)
    subject: str = Field(min_length=3, max_length=200)
    facts: str = Field(min_length=20, max_length=4000)
    relief: str = Field(min_length=5, max_length=1500)
    applicant_name: str = Field(min_length=1, max_length=120)
    contact: str = Field(min_length=3, max_length=200)
    reference_numbers: str = Field(default="", max_length=300)


@router.post("/drafts/rti")
def draft_rti(body: RTIIn):
    return {"draft": drafts.rti_draft(**body.model_dump()), "submitted": False,
            "next_steps": "Review the draft. For central public authorities you can file it on https://rtionline.dopt.gov.in; for state authorities, use your state's RTI portal or send it by post to the PIO."}


@router.post("/drafts/complaint")
def draft_complaint(body: ComplaintIn):
    return {"draft": drafts.complaint_draft(**body.model_dump()), "submitted": False,
            "next_steps": "Review the draft, then submit it yourself through the official channel listed in the guide (e.g. https://pgportal.gov.in for central government bodies). Keep the acknowledgement number."}


# ---------------- Reports ----------------
class ReportIn(BaseModel):
    item_type: str = Field(pattern="^(scheme|service|right|guide|assistant)$")
    item_slug: str | None = Field(default=None, max_length=120)
    kind: str = Field(pattern="^(incorrect|outdated|ai_answer|other)$")
    message: str = Field(min_length=5, max_length=2000)


@router.post("/reports", status_code=201)
def create_report(body: ReportIn, request: Request, db: Session = Depends(get_db)):
    limiter.check(f"report:{client_ip(request)}", 10)
    r = Report(**body.model_dump())
    db.add(r)
    db.commit()
    return {"id": r.id, "status": "received", "message": "Thank you. An editor will review this report."}
