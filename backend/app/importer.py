"""Structured data import with validation. Used for seeding and the admin import endpoint.

Imported records keep the status given (seed uses 'published'); admin imports land as
'draft' unless the importer is an admin who explicitly requests otherwise.
"""
from __future__ import annotations

from datetime import date
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from .freshness import REVIEW_INTERVALS
from .models import CONTENT_MODELS, ImportRun, RecordVersion, VERIFICATION, WORKFLOW

# Official/primary domains for action links (apply/info/portal URLs).
OFFICIAL_SUFFIXES = (".gov.in", ".nic.in")
OFFICIAL_EXTRA = {"www.jansamarth.in", "www.mudra.org.in", "www.standupmitra.in", "www.pfrda.org.in", "jansamarth.in", "mudra.org.in", "standupmitra.in", "pfrda.org.in"}
# Secondary sources may be cited as provenance, but never used as action links.
SECONDARY_SOURCE_TYPES = {"news_secondary", "guideline_document"}

REQUIRED = {
    "scheme": ["slug", "name", "summary", "ministry", "categories"],
    "right": ["slug", "article", "title", "plain_en", "part", "group"],
    "guide": ["slug", "kind", "title", "summary"],
    "service": ["slug", "name", "summary", "authority"],
}
DATE_FIELDS = {"last_verified", "opens_on", "closes_on"}


def is_official_url(url: str | None) -> bool:
    if not url:
        return True
    p = urlparse(url)
    host = (p.hostname or "").lower()
    return p.scheme == "https" and (host.endswith(OFFICIAL_SUFFIXES) or host in OFFICIAL_EXTRA)


def validate_record(kind: str, data: dict) -> list[str]:
    errs = [f"missing field '{f}'" for f in REQUIRED[kind] if not data.get(f)]
    if data.get("status", "published") not in WORKFLOW:
        errs.append(f"invalid status '{data.get('status')}'")
    if data.get("verification_status", "needs_verification") not in VERIFICATION:
        errs.append(f"invalid verification_status '{data.get('verification_status')}'")
    for f in ("apply_url", "info_url", "portal_url"):
        if data.get(f) and not is_official_url(data[f]):
            errs.append(f"{f} is not an official https government domain: {data[f]}")
    srcs = data.get("sources") or []
    if not srcs:
        errs.append("at least one source is required")
    for s in srcs:
        if not s.get("url", "").startswith("https://"):
            errs.append(f"source url must be https: {s.get('url')}")
        elif s.get("type") not in SECONDARY_SOURCE_TYPES and not is_official_url(s["url"]):
            errs.append(f"non-official source must be typed news_secondary/guideline_document: {s['url']}")
        if not s.get("organisation"):
            errs.append("source missing organisation")
    if kind == "scheme":
        if data.get("benefit_amount") and data.get("verification_status") == "needs_verification":
            errs.append("benefit_amount must be empty until the scheme is verified/reviewed")
        for r in data.get("eligibility_rules") or []:
            if r.get("op") == "any":
                if not r.get("label") or not r.get("rules") or not all({"field", "op"} <= set(x) for x in r["rules"]):
                    errs.append(f"bad 'any' eligibility rule {r}")
            elif not {"field", "op", "label"} <= set(r):
                errs.append(f"bad eligibility rule {r}")
    if data.get("verification_status") in ("verified", "reviewed") and not data.get("last_verified"):
        errs.append("verified/reviewed records need last_verified")
    return errs


def _coerce(data: dict) -> dict:
    out = dict(data)
    for f in DATE_FIELDS:
        if isinstance(out.get(f), str):
            out[f] = date.fromisoformat(out[f])
    return out


def snapshot(obj) -> dict:
    d = {}
    for col in obj.__table__.columns:
        v = getattr(obj, col.name)
        d[col.name] = v.isoformat() if hasattr(v, "isoformat") else v
    return d


def import_records(db: Session, kind: str, records: list[dict], actor: str, default_status: str = "published") -> ImportRun:
    Model = CONTENT_MODELS[kind]
    cols = {c.name for c in Model.__table__.columns}
    run = ImportRun(actor=actor, entity_type=kind, created=0, updated=0, errors=[])
    errors = []
    for i, raw in enumerate(records):
        raw = {"status": default_status, "review_interval_days": REVIEW_INTERVALS[kind], **raw}
        errs = validate_record(kind, raw)
        if errs:
            errors.append({"index": i, "slug": raw.get("slug"), "errors": errs})
            continue
        data = {k: v for k, v in _coerce(raw).items() if k in cols and k != "id"}
        obj = db.scalar(select(Model).where(Model.slug == data["slug"]))
        if obj:
            for k, v in data.items():
                setattr(obj, k, v)
            obj.version = (obj.version or 1) + 1
            run.updated += 1
        else:
            obj = Model(**data, version=1)
            db.add(obj)
            run.created += 1
        obj.updated_by = actor
        db.flush()
        db.add(RecordVersion(entity_type=kind, entity_slug=obj.slug, version=obj.version, snapshot=snapshot(obj), changed_by=actor, note="import"))
    run.errors = errors
    db.add(run)
    db.commit()
    return run


def seed_all(db: Session) -> dict:
    from .seed.guides import GUIDES
    from .seed.rights import RIGHTS
    from .seed.schemes import SCHEMES
    from .seed.services import SERVICES

    result = {}
    for kind, recs in (("scheme", SCHEMES), ("right", RIGHTS), ("guide", GUIDES), ("service", SERVICES)):
        run = import_records(db, kind, recs, actor="seed")
        result[kind] = {"created": run.created, "updated": run.updated, "errors": run.errors}
    return result


def sync_seed(db: Session) -> dict:
    """Bring a live database up to date with the curated seed records.

    - new seed records are inserted (published, with their verification labels)
    - records last written by the seed are refreshed when the seed content changed
    - records edited by a person (updated_by != "seed") are never touched
    """
    from .seed.guides import GUIDES
    from .seed.rights import RIGHTS
    from .seed.schemes import SCHEMES
    from .seed.services import SERVICES

    summary = {}
    for kind, recs in (("scheme", SCHEMES), ("right", RIGHTS), ("guide", GUIDES), ("service", SERVICES)):
        Model = CONTENT_MODELS[kind]
        cols = {c.name for c in Model.__table__.columns}
        added = refreshed = kept = 0
        errors = []
        for raw in recs:
            raw = {"status": "published", "review_interval_days": REVIEW_INTERVALS[kind], **raw}
            errs = validate_record(kind, raw)
            if errs:
                errors.append({"slug": raw.get("slug"), "errors": errs})
                continue
            data = {k: v for k, v in _coerce(raw).items() if k in cols and k != "id"}
            obj = db.scalar(select(Model).where(Model.slug == data["slug"]))
            if obj is None:
                obj = Model(**data, version=1, updated_by="seed")
                db.add(obj)
                added += 1
            elif obj.updated_by not in (None, "seed"):
                kept += 1
                continue
            else:
                changed = [k for k, v in data.items() if k != "status" and getattr(obj, k) != v]
                if not changed:
                    continue
                for k in changed:
                    setattr(obj, k, data[k])
                obj.version = (obj.version or 1) + 1
                obj.updated_by = "seed"
                refreshed += 1
            db.flush()
            db.add(RecordVersion(entity_type=kind, entity_slug=obj.slug, version=obj.version, snapshot=snapshot(obj), changed_by="seed", note="seed sync"))
        summary[kind] = {"added": added, "refreshed": refreshed, "kept_human_edits": kept, "errors": errors}
    db.commit()
    return summary
