"""Auth: bcrypt password hashes, signed JWT in an httpOnly SameSite=Lax cookie,
role checks, CSRF header check for cookie-authenticated writes, rate limiting."""
from __future__ import annotations

import ipaddress
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db
from .models import AuditLog, User

COOKIE = "js_session"
ROLE_RANK = {"user": 0, "editor": 1, "admin": 2}


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode()[:72], hashed.encode())
    except ValueError:
        return False


def make_token(user: User) -> str:
    s = get_settings()
    payload = {"sub": str(user.id), "role": user.role, "exp": datetime.now(timezone.utc) + timedelta(hours=s.session_hours)}
    return jwt.encode(payload, s.secret_key, algorithm="HS256")


def current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    try:
        data = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    return db.get(User, int(data["sub"]))


def require_user(user: User | None = Depends(current_user_optional)) -> User:
    if not user:
        raise HTTPException(401, "Please sign in to use this feature.")
    return user


def require_role(role: str):
    def dep(user: User = Depends(require_user)) -> User:
        if ROLE_RANK.get(user.role, -1) < ROLE_RANK[role]:
            raise HTTPException(403, "You do not have permission to do this.")
        return user
    return dep


def csrf_check(request: Request) -> None:
    """Cookie-authenticated state changes must carry a custom header a cross-site form cannot set."""
    if request.method in ("POST", "PUT", "PATCH", "DELETE") and request.headers.get("x-requested-with") != "jansaathi":
        raise HTTPException(403, "Missing CSRF header.")


def audit(db: Session, actor: str, action: str, target: str, detail: dict | None = None) -> None:
    db.add(AuditLog(actor=actor, action=action, target=target, detail=detail or {}))


class RateLimiter:
    """In-memory sliding window. For multi-instance deployments, back this with Redis."""

    def __init__(self) -> None:
        self.hits: dict[str, deque] = defaultdict(deque)

    def check(self, key: str, limit: int, window: float = 60.0) -> None:
        now = time.monotonic()
        q = self.hits[key]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(429, "Too many requests. Please wait a minute and try again.")
        q.append(now)


limiter = RateLimiter()


def _ip(value: str):
    try:
        return ipaddress.ip_address(value.strip())
    except ValueError:
        return None


def client_ip(request: Request) -> str:
    """Best-effort visitor IP for rate limiting.

    Forwarding headers are only trusted when the request reached us from an internal hop
    (loopback / private network, e.g. the Next.js proxy or a Render/Docker load balancer).
    Order: CF-Connecting-IP / True-Client-IP (set by Cloudflare, which fronts Render and
    overwrites client-sent values), then the right-most *public* address in X-Forwarded-For
    (entries further left can be supplied by the client), then the socket address.
    """
    peer = request.client.host if request.client else ""
    p = _ip(peer)
    if p is None or not p.is_global:
        for name in ("cf-connecting-ip", "true-client-ip"):
            v = _ip(request.headers.get(name, ""))
            if v is not None:
                return str(v)
        chain = [ip for ip in (_ip(x) for x in request.headers.get("x-forwarded-for", "").split(",")) if ip is not None]
        for ip in reversed(chain):
            if ip.is_global:
                return str(ip)
        if chain:
            return str(chain[-1])
    return peer or "unknown"
