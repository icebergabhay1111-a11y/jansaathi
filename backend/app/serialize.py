from __future__ import annotations

from datetime import date
from typing import Any

from .freshness import application_window, freshness

SKIP = {"id", "updated_by"}


def _val(v: Any):
    return v.isoformat() if hasattr(v, "isoformat") else v


def full(obj, today: date | None = None) -> dict:
    d = {c.name: _val(getattr(obj, c.name)) for c in obj.__table__.columns if c.name not in SKIP}
    d["freshness"] = freshness(obj.last_verified, obj.review_interval_days, obj.verification_status, today)
    if hasattr(obj, "closes_on"):
        d["application_window"] = application_window(obj.opens_on, obj.closes_on, today)
    return d


def card(kind: str, obj, today: date | None = None) -> dict:
    base = {"kind": kind, "slug": obj.slug, "verification_status": obj.verification_status,
            "freshness": freshness(obj.last_verified, obj.review_interval_days, obj.verification_status, today)["state"],
            "last_verified": _val(obj.last_verified)}
    if kind == "scheme":
        base.update(title=obj.name, title_hi=obj.name_hi, summary=obj.summary, summary_hi=obj.summary_hi, level=obj.level,
                    states=obj.states, categories=obj.categories, ministry=obj.ministry, benefit_type=obj.benefit_type,
                    application_window=application_window(obj.opens_on, obj.closes_on, today))
    elif kind == "right":
        base.update(title=obj.title, title_hi=obj.title_hi, summary=obj.plain_en, summary_hi=obj.plain_hi, article=obj.article, group=obj.group, part=obj.part, applies_to=obj.applies_to)
    elif kind == "guide":
        base.update(title=obj.title, title_hi=obj.title_hi, summary=obj.summary, guide_kind=obj.kind, emergency=obj.emergency)
    else:
        base.update(title=obj.name, title_hi=obj.name_hi, summary=obj.summary, authority=obj.authority, level=obj.level, online=obj.online, portal_url=obj.portal_url, popular=obj.popular)
    return base
