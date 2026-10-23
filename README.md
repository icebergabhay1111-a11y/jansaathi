# JanSaathi

**India's citizen-first guide to government schemes, constitutional rights and public services — with every answer linked to its official source.**

> "Tell us your situation. Discover your rights, benefits, and the official steps you can take."

JanSaathi is an **independent** information platform. It is **not** a Government of India service, is not affiliated with any government or political party, and never submits applications or complaints on anyone's behalf.

---

## What works today (vertical slice v0.1)

| Area | What you can do |
|---|---|
| **Scheme discovery** | Browse/search 22 real central & state schemes; filter by category, state, level, verification; paginate; sort |
| **Eligibility matcher** | Guided, privacy-first questionnaire (asks only questions relevant to chosen categories); deterministic rule engine explains satisfied / missing / failed conditions with careful labels ("Potential match", never "eligible") |
| **Know your rights** | 27 constitutional entries (Preamble, Arts. 14–32, 21A, 226, 39A, 51A + structure-of-government overviews) in plain English and explanatory Hindi; 11 everyday-rights guides |
| **Government services** | 22 service guides (RTI, CPGRAMS, passport, voter registration, birth/death certificate, UDID, e-Shram, Udyam, legal aid…) linking to official portals |
| **Complaints & legal aid** | 8 grievance guides with official channels and escalation; complaint-letter and RTI-application **draft** generators |
| **Ask JanSaathi** | Retrieval-grounded assistant (Gemini) answering only from published records, with numbered citations; works without AI (deterministic answers from the same records) |
| **Accounts (optional)** | Register/login (bcrypt + httpOnly JWT cookie), save items, user-entered application status, document checklists, reminders, data export, account deletion |
| **Admin** | Role-based (editor/admin) content management, Draft → Source review → Verified → Approved → Published workflow, verification recording, version history, review queue for stale/unverified records, citizen reports, validated JSON import, audit log |
| **Languages** | English and Hindi UI; Hindi search terms; Hindi AI answers. Tamil etc. are *planned*, not claimed |
| **Trust** | Every record shows source, verification status and date; unverified records hide benefit amounts and show warnings; links must be official `https` government domains |

See [`docs/FEATURES.md`](docs/FEATURES.md) for the complete list, including what still needs credentials.

## Architecture

```
Browser ──► Next.js 16 (React 19, TypeScript, Tailwind v4)
              │  SSR detail pages · /api/* proxied (same-origin cookies)
              ▼
           FastAPI (Python) ── SQLAlchemy 2 ── SQLite (dev) / PostgreSQL (prod), Alembic migrations
              │
              ├─ search.py       field-weighted, EN/HI synonyms, fuzzy (RapidFuzz)
              ├─ eligibility.py  deterministic rule engine
              ├─ ai/             provider abstraction → Gemini; RAG over published records; fallback
              └─ importer.py     validation (official URLs, sources, no unverified amounts)
```

## Quick start (local)

Prerequisites: Python 3.11+, Node 20+.

```bash
# 1. Backend
cd backend
pip install -r requirements-dev.txt
cp .env.example .env            # optional: add GEMINI_API_KEY
alembic upgrade head            # create tables
python -m app.cli seed          # load the curated, source-labelled records
ADMIN_PASSWORD='choose-a-long-password' python -m app.cli create-admin you@example.com
uvicorn app.main:app --reload --port 8000

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev                     # http://localhost:3000
```

API docs: http://localhost:8000/api/docs · Health: http://localhost:8000/api/health

### Using PostgreSQL
Set `DATABASE_URL=postgresql+psycopg://user:pass@host:5432/jansaathi`, then `alembic upgrade head && python -m app.cli seed`. Or run the whole stack with Docker:

```bash
echo "SECRET_KEY=$(python -c 'import secrets;print(secrets.token_urlsafe(48))')" > .env
docker compose up --build       # Postgres + API + web on :3000
```

### Enabling the AI assistant (Gemini)
1. Create a key at Google AI Studio.
2. Put `GEMINI_API_KEY=...` in `backend/.env` (never in the frontend). Optionally set `GEMINI_MODEL` (default `gemini-2.5-flash`).
3. Restart the backend. `/api/health` shows `"ai_configured": true`.

If the key is missing, the quota runs out, or Gemini errors, the assistant automatically returns record-based answers and labels them as such — search, the matcher and all pages keep working.

## Tests

```bash
cd backend && python -m pytest -q                       # 37 unit + integration tests (SQLite)
TEST_DATABASE_URL=postgresql+psycopg://... python -m pytest -q   # same suite on PostgreSQL
# with both servers running:
python e2e/journeys.py      # 8 browser journeys (Playwright)
python e2e/overflow.py      # mobile-width layout + page-error check on 15 pages
```

See [`docs/TESTING.md`](docs/TESTING.md) for what each test covers and what was **not** tested.

## Documentation
- [Features & integrations needing credentials](docs/FEATURES.md)
- [Data sources & limitations](docs/DATA_SOURCES.md)
- [Security & privacy checklist](docs/SECURITY_PRIVACY.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Testing](docs/TESTING.md)
- [Known limitations](docs/KNOWN_LIMITATIONS.md)

## Important
JanSaathi does not cover every scheme in India, is not government-approved, and has not had an independent security audit. General information only — not legal advice.
