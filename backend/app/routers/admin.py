"""Protected admin / editor endpoints: content management, publishing workflow, review queue, reports, audit."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..freshness import freshness
from ..importer import import_records, snapshot, validate_record, _coerce
from ..models import CONTENT_MODELS, VERIFICATION, AuditLog, ImportRun, RecordVersion, Report, User
from ..security import ROLE_RANK, audit, csrf_check, require_role
from ..serialize import full

router = APIRouter(prefix="/api/admin", dependencies=[Depends(csrf_check)])
editor = require_role("editor")
admin = require_role("admin")

# Allowed transitions and the minimum role needed.
TRANSITIONS = {
    ("draft", "source_review"): "editor",
    ("source_review", "verified"): "editor",
    ("source_review", "draft"): "editor",
    ("verified", "approved"): "admin",
    ("verified", "draft"): "editor",
    ("approved", "published"): "admin",
    ("approved", "draft"): "editor",
    ("published", "unpublished"): "admin",
    ("unpublished", "draft"): "editor",
    ("unpublished", "published"): "admin",
}


def _model(kind: str):
    if kind not in CONTENT_MODELS:
        raise HTTPException(404, "Unknown record type.")
    return CONTENT_MODELS[kind]


def _obj(db: Session, kind: str, slug: str):
    M = _model(kind)
    o = db.scalar(select(M).where(M.slug == slug))
    if not o:
        raise HTTPException(404, "Record not found.")
    return o


def _title(o) -> str:
    return getattr(o, "name", None) or getattr(o, "title", "")


@router.get("/overview")
def overview(user: User = Depends(editor), db: Session = Depends(get_db)):
    out = {}
    for kind, M in CONTENT_MODELS.items():
        rows = list(db.scalars(select(M)))
        by = {}
        for r in rows:
            by[r.status] = by.get(r.status, 0) + 1
        out[kind] = {"total": len(rows), "by_status": by}
    open_reports = len(list(db.scalars(select(Report).where(Report.status == "open"))))
    return {"records": out, "open_reports": open_reports, "role": user.role}


@router.get("/records")
def records(kind: str = "scheme", status: str | None = None, user: User = Depends(editor), db: Session = Depends(get_db)):
    M = _model(kind)
    q = select(M)
    if status:
        q = q.where(M.status == status)
    rows = list(db.scalars(q.order_by(M.updated_at.desc())))
    return {"items": [{"slug": r.slug, "title": _title(r), "status": r.status, "verification_status": r.verification_status,
                       "last_verified": r.last_verified.isoformat() if r.last_verified else None, "version": r.version,
                       "freshness": freshness(r.last_verified, r.review_interval_days, r.verification_status)["state"],
                       "updated_at": r.updated_at.isoformat(), "updated_by": r.updated_by} for r in rows]}


@router.get("/records/{kind}/{slug}")
def record(kind: str, slug: str, user: User = Depends(editor), db: Session = Depends(get_db)):
    return full(_obj(db, kind, slug))


class RecordIn(BaseModel):
    data: dict
    note: str | None = Field(default=None, max_length=500)


@router.post("/records/{kind}", status_code=201)
def create(kind: str, body: RecordIn, user: User = Depends(editor), db: Session = Depends(get_db)):
    M = _model(kind)
    data = {**body.data, "status": "draft"}  # new records always start as drafts
    errs = validate_record(kind, data)
    if errs:
        raise HTTPException(422, {"errors": errs})
    if db.scalar(select(M).where(M.slug == data["slug"])):
        raise HTTPException(409, "A record with this slug already exists.")
    cols = {c.name for c in M.__table__.columns} - {"id", "version", "created_at", "updated_at"}
    o = M(**{k: v for k, v in _coerce(data).items() if k in cols}, version=1, updated_by=user.email)
    db.add(o)
    db.flush()
    db.add(RecordVersion(entity_type=kind, entity_slug=o.slug, version=1, snapshot=snapshot(o), changed_by=user.email, note=body.note or "created"))
    audit(db, user.email, "create", f"{kind}:{o.slug}")
    db.commit()
    return full(o)


@router.put("/records/{kind}/{slug}")
def update(kind: str, slug: str, body: RecordIn, user: User = Depends(editor), db: Session = Depends(get_db)):
    o = _obj(db, kind, slug)
    merged = {**snapshot(o), **body.data, "slug": o.slug}
    merged.pop("id", None)
    errs = validate_record(kind, merged)
    if errs:
        raise HTTPException(422, {"errors": errs})
    protected = {"id", "slug", "status", "version", "created_at", "updated_at", "updated_by"}
    cols = {c.name for c in o.__table__.columns} - protected
    changed = []
    for k, v in _coerce(body.data).items():
        if k in cols and getattr(o, k) != v:
            setattr(o, k, v)
            changed.append(k)
    if not changed:
        return full(o)
    o.version += 1
    o.updated_by = user.email
    # Editing published content sends it back through review; it stays visible to citizens
    # only if an admin edits it (admin edits are treated as reviewed changes and logged).
    if o.status == "published" and ROLE_RANK[user.role] < ROLE_RANK["admin"]:
        o.status = "source_review"
    db.flush()
    db.add(RecordVersion(entity_type=kind, entity_slug=o.slug, version=o.version, snapshot=snapshot(o), changed_by=user.email, note=body.note))
    audit(db, user.email, "update", f"{kind}:{o.slug}", {"fields": changed, "status_after": o.status})
    db.commit()
    return full(o)


class TransitionIn(BaseModel):
    to: str
    note: str | None = Field(default=None, max_length=500)


@router.post("/records/{kind}/{slug}/transition")
def transition(kind: str, slug: str, body: TransitionIn, user: User = Depends(editor), db: Session = Depends(get_db)):
    o = _obj(db, kind, slug)
    need = TRANSITIONS.get((o.status, body.to))
    if not need:
        raise HTTPException(409, f"Cannot move from '{o.status}' to '{body.to}'.")
    if ROLE_RANK[user.role] < ROLE_RANK[need]:
        raise HTTPException(403, f"Moving to '{body.to}' requires the {need} role.")
    if body.to == "verified":
        if not o.sources:
            raise HTTPException(409, "Attach at least one official source before verification.")
        if o.verification_status == "needs_verification" or not o.last_verified:
            raise HTTPException(409, "Record the verification (status and date) before moving to 'verified'.")
    prev = o.status
    o.status = body.to
    o.updated_by = user.email
    audit(db, user.email, "transition", f"{kind}:{o.slug}", {"from": prev, "to": body.to, "note": body.note})
    db.commit()
    return {"slug": o.slug, "status": o.status}


class VerifyIn(BaseModel):
    verification_status: str
    last_verified: date
    note: str = Field(min_length=5, max_length=1000)


@router.post("/records/{kind}/{slug}/verify")
def verify(kind: str, slug: str, body: VerifyIn, user: User = Depends(editor), db: Session = Depends(get_db)):
    if body.verification_status not in VERIFICATION:
        raise HTTPException(422, "Invalid verification status.")
    if body.last_verified > date.today():
        raise HTTPException(422, "Verification date cannot be in the future.")
    o = _obj(db, kind, slug)
    o.verification_status, o.last_verified, o.verification_note = body.verification_status, body.last_verified, body.note
    o.updated_by = user.email
    audit(db, user.email, "verify", f"{kind}:{o.slug}", body.model_dump(mode="json"))
    db.commit()
    return full(o)


@router.get("/records/{kind}/{slug}/history")
def history(kind: str, slug: str, user: User = Depends(editor), db: Session = Depends(get_db)):
    rows = db.scalars(select(RecordVersion).where(RecordVersion.entity_type == kind, RecordVersion.entity_slug == slug).order_by(RecordVersion.version.desc()))
    return {"items": [{"version": r.version, "changed_by": r.changed_by, "changed_at": r.changed_at.isoformat(), "note": r.note} for r in rows]}


@router.get("/review-queue")
def review_queue(user: User = Depends(editor), db: Session = Depends(get_db)):
    """Published records whose review date has passed or that were never verified."""
    items = []
    for kind, M in CONTENT_MODELS.items():
        for o in db.scalars(select(M).where(M.status == "published")):
            f = freshness(o.last_verified, o.review_interval_days, o.verification_status)
            if f["state"] != "fresh":
                items.append({"kind": kind, "slug": o.slug, "title": _title(o), "state": f["state"], "review_due": f["review_due"], "note": o.verification_note})
    items.sort(key=lambda x: (x["state"] != "stale", x["review_due"] or "9999"))
    return {"items": items}


@router.get("/reports")
def reports(status: str = "open", user: User = Depends(editor), db: Session = Depends(get_db)):
    rows = db.scalars(select(Report).where(Report.status == status).order_by(Report.created_at.desc()))
    return {"items": [{"id": r.id, "item_type": r.item_type, "item_slug": r.item_slug, "kind": r.kind, "message": r.message, "status": r.status, "created_at": r.created_at.isoformat()} for r in rows]}


class ReportPatch(BaseModel):
    status: str = Field(pattern="^(open|resolved|dismissed)$")


@router.patch("/reports/{rid}")
def update_report(rid: int, body: ReportPatch, user: User = Depends(editor), db: Session = Depends(get_db)):
    r = db.get(Report, rid)
    if not r:
        raise HTTPException(404, "Not found.")
    r.status = body.status
    audit(db, user.email, "report_status", f"report:{rid}", {"status": body.status})
    db.commit()
    return {"ok": True}


class ImportIn(BaseModel):
    kind: str
    records: list[dict] = Field(min_length=1, max_length=500)


@router.post("/import")
def do_import(body: ImportIn, user: User = Depends(editor), db: Session = Depends(get_db)):
    _model(body.kind)
    # Imports never publish directly: they enter the workflow as drafts.
    recs = [{**r, "status": "draft"} for r in body.records]
    run = import_records(db, body.kind, recs, actor=user.email, default_status="draft")
    audit(db, user.email, "import", body.kind, {"created": run.created, "updated": run.updated, "errors": len(run.errors)})
    db.commit()
    return {"created": run.created, "updated": run.updated, "errors": run.errors}


@router.get("/imports")
def imports(user: User = Depends(editor), db: Session = Depends(get_db)):
    rows = db.scalars(select(ImportRun).order_by(ImportRun.at.desc()).limit(50))
    return {"items": [{"id": r.id, "actor": r.actor, "kind": r.entity_type, "created": r.created, "updated": r.updated, "errors": r.errors, "at": r.at.isoformat()} for r in rows]}


@router.get("/audit")
def audit_log(user: User = Depends(admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(AuditLog).order_by(AuditLog.at.desc()).limit(200))
    return {"items": [{"actor": r.actor, "action": r.action, "target": r.target, "detail": r.detail, "at": r.at.isoformat()} for r in rows]}


class RoleIn(BaseModel):
    email: str
    role: str = Field(pattern="^(user|editor|admin)$")


@router.post("/users/role")
def set_role(body: RoleIn, user: User = Depends(admin), db: Session = Depends(get_db)):
    target = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if not target:
        raise HTTPException(404, "User not found.")
    if target.id == user.id and body.role != "admin":
        raise HTTPException(409, "You cannot remove your own admin role.")
    target.role = body.role
    audit(db, user.email, "set_role", f"user:{target.email}", {"role": body.role})
    db.commit()
    return {"email": target.email, "role": target.role}
