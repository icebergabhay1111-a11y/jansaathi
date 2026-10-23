"""Management commands.

  python -m app.cli seed                      # import/refresh the curated seed records
  python -m app.cli seed-if-empty             # seed only a fresh database (used on deploy)
  python -m app.cli create-admin EMAIL        # create/promote an admin (prompts for password)
  python -m app.cli init-dev                  # create tables directly (dev only; prefer `alembic upgrade head`)
"""
from __future__ import annotations

import getpass
import json
import os
import sys

from sqlalchemy import select

from .db import Base, SessionLocal, engine
from .importer import seed_all
from .models import Scheme, User
from .security import hash_password


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    cmd = argv[0]
    if cmd == "init-dev":
        Base.metadata.create_all(engine)
        print("tables created")
        return 0
    db = SessionLocal()
    try:
        if cmd == "seed":
            print(json.dumps(seed_all(db), indent=2))
            return 0
        if cmd == "seed-if-empty":  # used at container start: never overwrites edited content
            if db.scalar(select(Scheme.id).limit(1)) is None:
                print(json.dumps(seed_all(db), indent=2))
            else:
                print("database already has content; seed skipped")
            return 0
        if cmd == "create-admin":
            email = argv[1].strip().lower()
            pw = os.getenv("ADMIN_PASSWORD") or getpass.getpass("Password (min 12 chars): ")
            if len(pw) < 12:
                print("Password must be at least 12 characters")
                return 1
            u = db.scalar(select(User).where(User.email == email))
            if u:
                u.role, u.password_hash = "admin", hash_password(pw)
            else:
                db.add(User(email=email, password_hash=hash_password(pw), role="admin", display_name="Admin"))
            db.commit()
            print(f"admin ready: {email}")
            return 0
    finally:
        db.close()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
