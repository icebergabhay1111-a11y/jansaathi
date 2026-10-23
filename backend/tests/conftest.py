import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_jansaathi.db")
os.environ["GEMINI_API_KEY"] = ""  # tests never call a real provider
os.environ["RATE_LIMIT_AUTH_PER_MIN"] = "1000"
os.environ["RATE_LIMIT_CHAT_PER_MIN"] = "1000"

from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.importer import seed_all  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402
from app.security import hash_password, limiter  # noqa: E402

H = {"x-requested-with": "jansaathi"}


@pytest.fixture(scope="session", autouse=True)
def database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    seed_all(db)
    db.add(User(email="admin@test.in", password_hash=hash_password("admin-password-123"), role="admin"))
    db.add(User(email="editor@test.in", password_hash=hash_password("editor-password-123"), role="editor"))
    db.commit()
    db.close()
    yield
    engine.dispose()
    try:
        os.remove("test_jansaathi.db")
    except FileNotFoundError:
        pass


@pytest.fixture(autouse=True)
def _reset_limiter():
    limiter.hits.clear()


@pytest.fixture
def client():
    return TestClient(app)


def login(client, email, pw):
    r = client.post("/api/auth/login", json={"email": email, "password": pw}, headers=H)
    assert r.status_code == 200, r.text
    return client


@pytest.fixture
def admin_client():
    return login(TestClient(app), "admin@test.in", "admin-password-123")


@pytest.fixture
def editor_client():
    return login(TestClient(app), "editor@test.in", "editor-password-123")
