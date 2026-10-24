# Testing

## Results at build time (23 Oct 2026)
| Suite | Result |
|---|---|
| Backend unit + integration (`backend/tests`), SQLite | **59 passed** |
| Same suite on PostgreSQL 16 | **59 passed** |
| Migration upgrade from the v0.1 schema on PostgreSQL (production path) | OK |
| Alembic migration + seed on SQLite and PostgreSQL | OK, 0 validation errors |
| Frontend `tsc`, `next build`, ESLint | Pass (7 lint warnings, 0 errors — see Known limitations) |
| Browser journeys (`e2e/journeys.py`, Playwright/Chromium) | **8 / 8 passed** |
| Feature tests (`e2e/features_v2.py`): eligibility brackets/category, voice ×2, checklist, tracker, quick cards/templates, office finder ×2 | **8 / 8 passed** |
| Mobile 390px overflow + page-error check, 18 pages | **18 / 18 passed** |

## Coverage of required journeys
| Journey | Test |
|---|---|
| A — student finds sourced scholarship recommendations | `test_student_scholarship_journey`, e2e A |
| B — constitutional article, grounded explanation | `test_article_search_and_assistant_fallback`, `test_ai_success_is_grounded`, e2e B |
| C — service → correct official portal | `test_service_has_official_portal`, e2e C |
| D — complaint draft + official grievance instructions | `test_complaint_draft`, e2e D |
| E — admin updates a scheme, publication workflow | `test_admin_workflow` (API) |
| F — guest browsing | `test_guest_can_browse_and_search`, e2e F+G |
| G — language selection + search | `test_hindi_search`, e2e F+G |
| H — unverified/stale record warning | `test_unverified_record_shows_warning`, `test_freshness_states`, e2e H |
| I — unauthorised admin access denied | `test_admin_requires_auth`, e2e I |
| J — AI provider unavailable, app keeps working | `test_ai_failure_falls_back`, `test_gemini_failures_raise_unavailable` |

Also: eligibility rule ops, jurisdiction, labels never say "eligible", relevant-question selection, sensitive questions optional, freshness/date logic, bilingual + fuzzy search, official-URL validation, every seed record validated, no unverified amounts, CSRF header, password hashing, export/delete, import-as-draft, review queue, Gemini adapter (mocked HTTP).

## Not tested (honest list)
- Voice input with a real microphone and real speech (tests use simulated speech recognition and a mocked transcription response).
- The live OpenStreetMap / Overpass and Nominatim services (mocked in tests; not reachable from the build environment).
- Real Tamil answer quality from Gemini.
- **Live Gemini API** — no key was available; the adapter is tested with mocked HTTP responses only.
- Journey E through the **browser** admin UI (tested at API level only).
- Screen-reader testing with NVDA/TalkBack; formal WCAG audit (only structural checks: labels, roles, focus styles, skip link).
- Load/performance testing; slow-network throttling.
- Safari / Firefox (only Chromium).
- Docker Compose stack (Dockerfiles written but not built in this environment).

## Running
```bash
cd backend && python -m pytest -q
TEST_DATABASE_URL=postgresql+psycopg://user@host:5432/jansaathi_test python -m pytest -q
# start API (:8000) and web (:3000), then:
pip install playwright && python -m playwright install chromium
python e2e/journeys.py && python e2e/overflow.py
```
