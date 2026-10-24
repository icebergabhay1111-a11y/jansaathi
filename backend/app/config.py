"""Runtime configuration, read from environment variables (see .env.example)."""
from __future__ import annotations

import os
import secrets
from functools import lru_cache
from pathlib import Path


def _load_dotenv() -> None:
    """Load backend/.env if present (real environment variables always win)."""
    p = Path(__file__).resolve().parent.parent / ".env"
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.env = os.getenv("JANSAATHI_ENV", "development")
        # SQLite for local dev; set postgresql+psycopg://user:pass@host/db in production.
        url = os.getenv("DATABASE_URL", "sqlite:///./jansaathi.db")
        # Hosts like Render/Heroku give postgres:// or postgresql:// — use the installed psycopg 3 driver.
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                url = "postgresql+psycopg://" + url[len(prefix):]
        self.database_url = url
        secret = os.getenv("SECRET_KEY")
        if not secret:
            if self.env == "production":
                raise RuntimeError("SECRET_KEY must be set in production")
            secret = secrets.token_urlsafe(32)  # ephemeral dev key: sessions reset on restart
        self.secret_key = secret
        self.session_hours = int(os.getenv("SESSION_HOURS", "72"))
        self.cookie_secure = os.getenv("COOKIE_SECURE", "false" if self.env != "production" else "true") == "true"
        self.cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]

        # AI provider. Only "gemini" is implemented; anything else (or no key) = deterministic fallback.
        self.ai_provider = os.getenv("AI_PROVIDER", "gemini")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        # tried in order if the main model is not available to this API key
        self.gemini_fallback_models = [m.strip() for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.6-flash,gemini-3.5-flash-lite,gemini-2.5-flash").split(",") if m.strip()]
        # Total time an answer may wait for the AI (all models together), and the cap per model attempt.
        self.ai_timeout_seconds = float(os.getenv("AI_TIMEOUT_SECONDS", "25"))
        self.ai_model_timeout_seconds = float(os.getenv("AI_MODEL_TIMEOUT_SECONDS", "12"))

        self.rate_limit_chat_per_min = int(os.getenv("RATE_LIMIT_CHAT_PER_MIN", "12"))
        self.rate_limit_auth_per_min = int(os.getenv("RATE_LIMIT_AUTH_PER_MIN", "10"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
