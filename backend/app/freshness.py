"""Information-freshness rules. Old != false: stale records get a warning and a review queue entry."""
from __future__ import annotations

from datetime import date, timedelta

# Default review intervals (days) by how fast the information tends to change.
REVIEW_INTERVALS = {"scheme": 90, "service": 120, "guide": 180, "right": 365}


def freshness(last_verified: date | None, interval_days: int, verification_status: str, today: date | None = None) -> dict:
    today = today or date.today()
    if verification_status == "needs_verification" or last_verified is None:
        return {"state": "unverified", "review_due": None, "message": "Not yet confirmed against the official source. Check the official link before acting."}
    due = last_verified + timedelta(days=interval_days)
    if today > due:
        return {"state": "stale", "review_due": due.isoformat(), "message": f"Last verified {last_verified.isoformat()}; review was due {due.isoformat()}. Details may have changed — confirm on the official site."}
    return {"state": "fresh", "review_due": due.isoformat(), "message": f"Last verified {last_verified.isoformat()}."}


def application_window(opens_on: date | None, closes_on: date | None, today: date | None = None) -> str:
    """open | closed_maybe | not_yet_open | unknown. 'closed_maybe' because official extensions are common."""
    today = today or date.today()
    if closes_on and today > closes_on:
        return "closed_maybe"
    if opens_on and today < opens_on:
        return "not_yet_open"
    if opens_on or closes_on:
        return "open"
    return "unknown"
