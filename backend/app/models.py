"""Relational schema.

Every public content record (Scheme, RightArticle, Guide, Service) shares the
ContentMixin: a publishing workflow status, a verification status, provenance
(sources), freshness metadata and a version counter. Change history lives in
RecordVersion; privileged actions in AuditLog.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Publishing workflow: draft -> source_review -> verified -> approved -> published (-> unpublished)
WORKFLOW = ["draft", "source_review", "verified", "approved", "published", "unpublished"]
# How far the facts have been checked against official sources
VERIFICATION = ["verified", "reviewed", "needs_verification"]


class ContentMixin:
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    verification_status: Mapped[str] = mapped_column(String(24), default="needs_verification")
    verification_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_verified: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_interval_days: Mapped[int] = mapped_column(Integer, default=90)
    sources: Mapped[list] = mapped_column(JSON, default=list)  # [{url, organisation, title, type, retrieved}]
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Scheme(ContentMixin, Base):
    __tablename__ = "schemes"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    name_hi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    summary: Mapped[str] = mapped_column(Text)
    summary_hi: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    ministry: Mapped[str] = mapped_column(String(255))
    level: Mapped[str] = mapped_column(String(20), default="central", index=True)  # central | state | district
    states: Mapped[list] = mapped_column(JSON, default=lambda: ["ALL"])
    categories: Mapped[list] = mapped_column(JSON, default=list)
    beneficiaries: Mapped[list] = mapped_column(JSON, default=list)
    eligibility_text: Mapped[list] = mapped_column(JSON, default=list)
    eligibility_rules: Mapped[list] = mapped_column(JSON, default=list)
    exclusions: Mapped[list] = mapped_column(JSON, default=list)
    documents: Mapped[list] = mapped_column(JSON, default=list)
    benefit_type: Mapped[str] = mapped_column(String(80), default="")
    benefit_amount: Mapped[str | None] = mapped_column(Text, nullable=True)  # only when verified/reviewed
    application_steps: Mapped[list] = mapped_column(JSON, default=list)
    apply_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    info_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    opens_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    closes_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    renewal: Mapped[str | None] = mapped_column(Text, nullable=True)
    selection_process: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reasons: Mapped[list] = mapped_column(JSON, default=list)
    grievance: Mapped[str | None] = mapped_column(Text, nullable=True)
    faqs: Mapped[list] = mapped_column(JSON, default=list)


class RightArticle(ContentMixin, Base):
    __tablename__ = "right_articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    article: Mapped[str] = mapped_column(String(60), index=True)
    part: Mapped[str] = mapped_column(String(120))
    group: Mapped[str] = mapped_column(String(120), index=True)
    title: Mapped[str] = mapped_column(String(255))
    title_hi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plain_en: Mapped[str] = mapped_column(Text)
    plain_hi: Mapped[str | None] = mapped_column(Text, nullable=True)
    protects: Mapped[str] = mapped_column(Text, default="")
    applies_to: Mapped[str] = mapped_column(String(255), default="")
    against_whom: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations: Mapped[list] = mapped_column(JSON, default=list)
    examples: Mapped[list] = mapped_column(JSON, default=list)
    situations: Mapped[list] = mapped_column(JSON, default=list)
    remedies: Mapped[list] = mapped_column(JSON, default=list)
    authorities: Mapped[list] = mapped_column(JSON, default=list)
    related: Mapped[list] = mapped_column(JSON, default=list)
    order: Mapped[int] = mapped_column(Integer, default=0)


class Guide(ContentMixin, Base):
    """Everyday-rights questions and complaint/grievance guidance."""
    __tablename__ = "guides"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(30), index=True)  # rights_question | complaint
    title: Mapped[str] = mapped_column(String(255))
    title_hi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    law_basis: Mapped[list] = mapped_column(JSON, default=list)  # [{law, type: constitutional|statutory|administrative, note}]
    qualifications: Mapped[list] = mapped_column(JSON, default=list)
    steps: Mapped[list] = mapped_column(JSON, default=list)
    authorities: Mapped[list] = mapped_column(JSON, default=list)  # [{name, url?, phone?}]
    documents: Mapped[list] = mapped_column(JSON, default=list)
    time_limits: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalation: Mapped[list] = mapped_column(JSON, default=list)
    emergency: Mapped[bool] = mapped_column(Boolean, default=False)
    keywords: Mapped[list] = mapped_column(JSON, default=list)


class Service(ContentMixin, Base):
    __tablename__ = "services"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    name_hi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    summary: Mapped[str] = mapped_column(Text)
    who_can_use: Mapped[str] = mapped_column(Text, default="")
    authority: Mapped[str] = mapped_column(String(255))
    level: Mapped[str] = mapped_column(String(20), default="central")
    states: Mapped[list] = mapped_column(JSON, default=lambda: ["ALL"])
    online: Mapped[str] = mapped_column(String(20), default="varies")  # yes | partial | no | varies
    in_person: Mapped[str | None] = mapped_column(Text, nullable=True)
    documents: Mapped[list] = mapped_column(JSON, default=list)
    steps: Mapped[list] = mapped_column(JSON, default=list)
    fee: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_time: Mapped[str | None] = mapped_column(Text, nullable=True)
    tracking: Mapped[str | None] = mapped_column(Text, nullable=True)
    correction: Mapped[str | None] = mapped_column(Text, nullable=True)
    appeal: Mapped[str | None] = mapped_column(Text, nullable=True)
    portal_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    help_channel: Mapped[str | None] = mapped_column(Text, nullable=True)
    popular: Mapped[bool] = mapped_column(Boolean, default=False)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="user")  # user | editor | admin
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    saved: Mapped[list["SavedItem"]] = relationship(cascade="all, delete-orphan", passive_deletes=True)
    reminders: Mapped[list["Reminder"]] = relationship(cascade="all, delete-orphan", passive_deletes=True)


class SavedItem(Base):
    __tablename__ = "saved_items"
    __table_args__ = (UniqueConstraint("user_id", "item_type", "item_slug"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    item_type: Mapped[str] = mapped_column(String(20))  # scheme | service | right | guide
    item_slug: Mapped[str] = mapped_column(String(120))
    my_status: Mapped[str] = mapped_column(String(30), default="interested")  # user-entered, never synced
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Reminder(Base):
    __tablename__ = "reminders"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    due_date: Mapped[date] = mapped_column(Date)
    related_slug: Mapped[str | None] = mapped_column(String(120), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Report(Base):
    """Citizen feedback: incorrect / outdated information."""
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_type: Mapped[str] = mapped_column(String(20))
    item_slug: Mapped[str | None] = mapped_column(String(120), nullable=True)
    kind: Mapped[str] = mapped_column(String(20))  # incorrect | outdated | ai_answer | other
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RecordVersion(Base):
    __tablename__ = "record_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(20), index=True)
    entity_slug: Mapped[str] = mapped_column(String(120), index=True)
    version: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict] = mapped_column(JSON)
    changed_by: Mapped[str] = mapped_column(String(255))
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(60))
    target: Mapped[str] = mapped_column(String(200))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ImportRun(Base):
    __tablename__ = "import_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(255))
    entity_type: Mapped[str] = mapped_column(String(20))
    created: Mapped[int] = mapped_column(Integer, default=0)
    updated: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


CONTENT_MODELS = {"scheme": Scheme, "right": RightArticle, "guide": Guide, "service": Service}
