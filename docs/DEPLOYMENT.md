# Deployment

## Components
| Component | Runtime | Port | Health |
|---|---|---|---|
| API | FastAPI / Uvicorn (Python 3.11+) | 8000 | `GET /api/health` → `{status, db, ai_configured}` |
| Web | Next.js 16 (Node 20+) | 3000 | `GET /` |
| DB | PostgreSQL 14+ (16 tested) | 5432 | |

The web app proxies `/api/*` to `BACKEND_URL`, so browsers only talk to one origin (keeps the session cookie first-party).

## Environment variables
Backend — see `backend/.env.example`. Required in production: `JANSAATHI_ENV=production`, `DATABASE_URL`, `SECRET_KEY`, `COOKIE_SECURE=true`. Optional: `GEMINI_API_KEY`, `GEMINI_MODEL`, rate limits.
Frontend: `BACKEND_URL` (e.g. `http://api:8000` or your API's internal URL).

## Option R — Render (one click, free tier)
The repo includes `render.yaml` (Blueprint) and a root `Dockerfile` that runs the website and API in one container (`start.sh`), plus a free PostgreSQL database.
1. Render Dashboard → **New → Blueprint** → connect GitHub → pick `jansaathi` → Apply.
2. When prompted, optionally fill `GEMINI_API_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` (**at least 12 characters** — a shorter password is rejected and no admin is created; the deploy log says so). Leave blank to skip. You can change them later under the service's **Environment** tab; saving restarts the service and applies them.
3. First deploy builds the image (~3–10 min). On every start, `start.sh` runs `python -m app.cli bootstrap` (migrations, seed if the database is empty, admin from env) in one process, starts the API, waits until `/api/health` answers, and only then opens the website port — so visitors never reach the site before its data service is ready. Served on `https://<service>.onrender.com`.
Notes: free web services sleep after ~15 min idle (first request takes ~1 min); Render's free PostgreSQL expires after 30 days unless upgraded; every push to `main` redeploys. `DATABASE_URL` from Render (`postgres://…`) is converted to the psycopg driver automatically. Seeding runs only on an empty database, so admin edits are never overwritten.

## Option A — Docker Compose (single VM)
```bash
cat > .env <<EOF
SECRET_KEY=$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')
POSTGRES_PASSWORD=$(python3 -c 'import secrets;print(secrets.token_urlsafe(24))')
COOKIE_SECURE=true
GEMINI_API_KEY=
EOF
docker compose up -d --build
docker compose exec api sh -c "ADMIN_PASSWORD='long-password' python -m app.cli create-admin you@example.com"
```
Put Caddy or Nginx in front of port 3000 for HTTPS.

## Option B — Managed services
- **DB:** any managed PostgreSQL (Neon, Supabase, RDS, Cloud SQL).
- **API:** Render / Railway / Fly.io / Cloud Run using `backend/Dockerfile` (runs `alembic upgrade head` and the idempotent seed at start).
- **Web:** Vercel (set `BACKEND_URL`) or the `frontend/Dockerfile`.

## Migrations
```bash
cd backend
alembic upgrade head                                 # apply
alembic revision --autogenerate -m "describe change" # after model changes
```
The initial migration was verified on both SQLite and PostgreSQL 16.

## Production build (without Docker)
```bash
cd backend && pip install -r requirements.txt && alembic upgrade head && python -m app.cli seed
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --proxy-headers
cd frontend && npm ci && npm run build && BACKEND_URL=http://127.0.0.1:8000 npx next start -p 3000
```
Note: the in-memory rate limiter is per process; with several workers/instances use a shared store (Redis).

## Logging & monitoring
- API logs one line per request with a request ID (also returned as `X-Request-ID`).
- Unhandled exceptions are logged and return a generic message. To add Sentry, initialise it in `app/main.py` where the "hook point" comment is.

## Backups
- Enable daily automated PostgreSQL backups with point-in-time recovery on your provider; keep ≥7 days.
- Self-hosted: `pg_dump -Fc jansaathi > jansaathi-$(date +%F).dump`, copy off-host, and test `pg_restore` monthly.
- Content history is also kept in `record_versions`, but that is not a substitute for backups.
