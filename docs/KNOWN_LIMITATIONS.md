# Known limitations

## Data
- **Coverage is small**: 22 schemes (one state scheme), 22 services, 27 constitutional entries, 19 guides. India has thousands of schemes.
- **Verification**: only 1 scheme is `verified`; most are `reviewed` or `needs_verification` because official portals blocked automated fetching during the build. Benefit amounts for 14 schemes are deliberately hidden.
- No district-level or municipal records yet.
- No application opening/closing dates are seeded (none were verified), so deadline features have nothing official to show yet.
- Hindi content is explanatory translation of summaries and constitutional explainers; full scheme detail pages are English with Hindi names/summaries.

## Product
- Only English and Hindi. Architecture supports more (`i18n-dict.ts`, `*_hi` fields) but no other language is implemented.
- Reminders are displayed in the dashboard only — no email/SMS/push delivery.
- No password reset (needs email provider), no 2FA.
- Application status is what the user enters; there is no government system integration.
- Admin editing uses a JSON editor rather than a form per field; categories and states are defined in code.
- Unpublished drafts cannot be previewed on the public page layout.
- No service worker / offline cache (intentional for now: avoids showing stale information as current).

## Technical
- Search is computed in Python over published records — fine for hundreds of records; for thousands, move to PostgreSQL full-text (`tsvector`) + `pg_trgm`.
- Rate limiting is in-memory per process.
- SSR detail pages cache backend responses for 60 seconds, so admin edits can take up to a minute to appear.
- Seven `react-hooks/set-state-in-effect` lint warnings (data-fetching effects); migrate to a data library or server components.
- Live Gemini responses were not tested (no key); prompt behaviour with real model output needs review, especially Hindi.
- No CSP header yet; no independent security review.
