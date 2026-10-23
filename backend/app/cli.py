"""Management commands.

  python -m app.cli bootstrap                 # deploy start-up: migrate + sync seed records + optional admin (one process)
  python -m app.cli seed                      # import/refresh the curated seed records
  python -m app.cli seed-if-empty             # seed only a fresh database
  python -m app.cli create-admin EMAIL        # create/promote an admin (prompts for password)
  python -m app.cli init-dev                  # create tables directly (dev only; prefer `alembic upgrade head`)

`bootstrap` reads optional ADMIN_EMAIL / ADMIN_PASSWORD env vars (hosts without a shell, e.g. Render free).
"""
from __future__ import annotations

import getpass
import json
import os
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Base, SessionLocal, engine
from .importer import seed_all, sync_seed
from .models import Scheme, User
from .security import hash_password

ADMIN_MIN_PASSWORD = 12


def migrate() -> None:
    from alembic import command
    from alembic.config import Config

    command.upgrade(Config(str(Path(__file__).resolve().parent.parent / "alembic.ini")), "head")


def seed_if_empty(db: Session) -> None:
    if db.scalar(select(Scheme.id).limit(1)) is None:
        print(json.dumps(seed_all(db)))
    else:
        print("database already has content; seed skipped")


def upsert_admin(db: Session, email: str, password: str) -> bool:
    email = email.strip().lower()
    if len(password) < ADMIN_MIN_PASSWORD:
        print(f"ADMIN_PASSWORD is shorter than {ADMIN_MIN_PASSWORD} characters — admin account NOT created/updated for {email}")
        return False
    u = db.scalar(select(User).where(User.email == email))
    if u:
        u.role, u.password_hash = "admin", hash_password(password)
    else:
        db.add(User(email=email, password_hash=hash_password(password), role="admin", display_name="Admin"))
    db.commit()
    print(f"admin ready: {email}")
    return True


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    cmd = argv[0]
    if cmd == "init-dev":
        Base.metadata.create_all(engine)
        print("tables created")
        return 0
    if cmd == "bootstrap":
        migrate()
    db = SessionLocal()
    try:
        if cmd == "bootstrap":
            print("seed sync:", json.dumps(sync_seed(db)))
            email, pw = os.getenv("ADMIN_EMAIL", ""), os.getenv("ADMIN_PASSWORD", "")
            if email and pw:
                upsert_admin(db, email, pw)  # a bad password is reported but never blocks start-up
            return 0
        if cmd == "seed":
            print(json.dumps(seed_all(db), indent=2))
            return 0
        if cmd == "seed-if-empty":
            seed_if_empty(db)
            return 0
        if cmd == "create-admin":
            pw = os.getenv("ADMIN_PASSWORD") or getpass.getpass(f"Password (min {ADMIN_MIN_PASSWORD} chars): ")
            return 0 if upsert_admin(db, argv[1], pw) else 1
    finally:
        db.close()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
