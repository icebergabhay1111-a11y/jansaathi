"""Optional accounts: register/login/logout, saved items, reminders, export and deletion."""
from __future__ import annotations

import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..models import CONTENT_MODELS, Reminder, SavedItem, User
from ..security import COOKIE, client_ip, csrf_check, current_user_optional, hash_password, limiter, make_token, require_user, verify_password

router = APIRouter(prefix="/api", dependencies=[Depends(csrf_check)])
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Creds(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)

    @field_validator("email")
    @classmethod
    def v_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("Enter a valid email address")
        return v


def _set_cookie(resp: Response, user: User) -> None:
    s = get_settings()
    resp.set_cookie(COOKIE, make_token(user), httponly=True, samesite="lax", secure=s.cookie_secure, max_age=s.session_hours * 3600, path="/")


def _me(u: User) -> dict:
    return {"id": u.id, "email": u.email, "display_name": u.display_name, "role": u.role}


@router.post("/auth/register", status_code=201)
def register(body: Creds, request: Request, response: Response, db: Session = Depends(get_db)):
    limiter.check(f"auth:{client_ip(request)}", get_settings().rate_limit_auth_per_min)
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(409, "An account with this email already exists.")
    u = User(email=body.email, password_hash=hash_password(body.password), display_name=body.display_name, role="user")
    db.add(u)
    db.commit()
    _set_cookie(response, u)
    return _me(u)


@router.post("/auth/login")
def login(body: Creds, request: Request, response: Response, db: Session = Depends(get_db)):
    limiter.check(f"auth:{client_ip(request)}", get_settings().rate_limit_auth_per_min)
    u = db.scalar(select(User).where(User.email == body.email))
    if not u or not verify_password(body.password, u.password_hash):
        raise HTTPException(401, "Email or password is incorrect.")
    _set_cookie(response, u)
    return _me(u)


@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@router.get("/auth/me")
def me(user: User | None = Depends(current_user_optional)):
    return {"user": _me(user) if user else None}


@router.delete("/auth/account")
def delete_account(response: Response, user: User = Depends(require_user), db: Session = Depends(get_db)):
    db.delete(db.get(User, user.id))
    db.commit()
    response.delete_cookie(COOKIE, path="/")
    return {"deleted": True, "message": "Your account, saved items and reminders have been permanently deleted."}


@router.get("/me/export")
def export(user: User = Depends(require_user), db: Session = Depends(get_db)):
    return {"account": _me(user), "created_at": user.created_at.isoformat(),
            "saved": [{"item_type": s.item_type, "item_slug": s.item_slug, "my_status": s.my_status, "notes": s.notes,
                       "applied_on": s.applied_on.isoformat() if s.applied_on else None, "reference_no": s.reference_no} for s in user.saved],
            "reminders": [{"title": r.title, "due_date": r.due_date.isoformat(), "related_slug": r.related_slug, "enabled": r.enabled} for r in user.reminders]}


# ---------- saved items ----------
MY_STATUSES = ["interested", "preparing_documents", "applied", "approved", "rejected", "not_applying"]


class SaveIn(BaseModel):
    item_type: str = Field(pattern="^(scheme|service|right|guide)$")
    item_slug: str = Field(max_length=120)
    my_status: str = "interested"
    notes: str | None = Field(default=None, max_length=1000)
    applied_on: date | None = None
    reference_no: str | None = Field(default=None, max_length=80)

    @field_validator("my_status")
    @classmethod
    def v_status(cls, v):
        if v not in MY_STATUSES:
            raise ValueError("invalid status")
        return v


def _saved_view(db: Session, s: SavedItem) -> dict:
    M = CONTENT_MODELS[s.item_type]
    o = db.scalar(select(M).where(M.slug == s.item_slug))
    title = getattr(o, "name", None) or getattr(o, "title", None) if o else None
    links = {}
    if o is not None:
        links = {k: getattr(o, k) for k in ("apply_url", "info_url", "portal_url") if getattr(o, k, None)}
    reminders = [{"id": r.id, "title": r.title, "due_date": r.due_date.isoformat(), "enabled": r.enabled}
                 for r in db.scalars(select(Reminder).where(Reminder.user_id == s.user_id, Reminder.related_slug == s.item_slug))]
    return {"id": s.id, "item_type": s.item_type, "item_slug": s.item_slug, "title": title or s.item_slug, "my_status": s.my_status,
            "status_source": "user_entered", "notes": s.notes, "documents": getattr(o, "documents", []) if o else [], "links": links,
            "applied_on": s.applied_on.isoformat() if s.applied_on else None, "reference_no": s.reference_no, "reminders": reminders,
            "closes_on": o.closes_on.isoformat() if o is not None and getattr(o, "closes_on", None) else None,
            "available": bool(o and o.status == "published")}


@router.get("/me/saved")
def list_saved(user: User = Depends(require_user), db: Session = Depends(get_db)):
    return {"items": [_saved_view(db, s) for s in user.saved], "statuses": MY_STATUSES}


@router.post("/me/saved", status_code=201)
def save(body: SaveIn, user: User = Depends(require_user), db: Session = Depends(get_db)):
    M = CONTENT_MODELS[body.item_type]
    if not db.scalar(select(M).where(M.slug == body.item_slug, M.status == "published")):
        raise HTTPException(404, "That item does not exist.")
    s = SavedItem(user_id=user.id, **body.model_dump())
    db.add(s)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Already saved.")
    return _saved_view(db, s)


class SavePatch(BaseModel):
    my_status: str | None = None
    notes: str | None = Field(default=None, max_length=1000)
    applied_on: date | None = None
    clear_applied_on: bool = False
    reference_no: str | None = Field(default=None, max_length=80)


@router.patch("/me/saved/{sid}")
def update_saved(sid: int, body: SavePatch, user: User = Depends(require_user), db: Session = Depends(get_db)):
    s = db.get(SavedItem, sid)
    if not s or s.user_id != user.id:
        raise HTTPException(404, "Not found.")
    if body.my_status:
        if body.my_status not in MY_STATUSES:
            raise HTTPException(422, "invalid status")
        s.my_status = body.my_status
    if body.notes is not None:
        s.notes = body.notes
    if body.clear_applied_on:
        s.applied_on = None
    elif body.applied_on is not None:
        if body.applied_on > date.today():
            raise HTTPException(422, "The application date cannot be in the future.")
        s.applied_on = body.applied_on
    if body.reference_no is not None:
        s.reference_no = body.reference_no.strip() or None
    db.commit()
    return _saved_view(db, s)


@router.delete("/me/saved/{sid}")
def delete_saved(sid: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    s = db.get(SavedItem, sid)
    if not s or s.user_id != user.id:
        raise HTTPException(404, "Not found.")
    db.delete(s)
    db.commit()
    return {"deleted": True}


# ---------- reminders (user-created; never presented as official deadlines) ----------
class ReminderIn(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    due_date: date
    related_slug: str | None = Field(default=None, max_length=120)


@router.get("/me/reminders")
def list_reminders(user: User = Depends(require_user)):
    today = date.today()
    return {"items": sorted([{"id": r.id, "title": r.title, "due_date": r.due_date.isoformat(), "related_slug": r.related_slug, "enabled": r.enabled,
                              "kind": "user_created", "overdue": r.due_date < today, "days_left": (r.due_date - today).days} for r in user.reminders], key=lambda x: x["due_date"])}


@router.post("/me/reminders", status_code=201)
def add_reminder(body: ReminderIn, user: User = Depends(require_user), db: Session = Depends(get_db)):
    if body.due_date.year > date.today().year + 10:
        raise HTTPException(422, "Please choose a date within the next 10 years.")
    r = Reminder(user_id=user.id, **body.model_dump())
    db.add(r)
    db.commit()
    return {"id": r.id}


class ReminderPatch(BaseModel):
    enabled: bool


@router.patch("/me/reminders/{rid}")
def toggle_reminder(rid: int, body: ReminderPatch, user: User = Depends(require_user), db: Session = Depends(get_db)):
    r = db.get(Reminder, rid)
    if not r or r.user_id != user.id:
        raise HTTPException(404, "Not found.")
    r.enabled = body.enabled
    db.commit()
    return {"ok": True}


@router.delete("/me/reminders/{rid}")
def delete_reminder(rid: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    r = db.get(Reminder, rid)
    if not r or r.user_id != user.id:
        raise HTTPException(404, "Not found.")
    db.delete(r)
    db.commit()
    return {"deleted": True}
