# Features

Status key: ✅ implemented and tested · 🟡 implemented, partially tested / limited · ⏳ requires external credentials or integration · ❌ not implemented

## Citizen features
| Feature | Status | Notes |
|---|---|---|
| Guest browsing of all information pages | ✅ | Journey F |
| Scheme directory: search, category/state/level/verification filters, sort, pagination | ✅ | |
| Scheme detail: eligibility, exclusions, benefits, documents, steps, renewal, rejection reasons, grievance, FAQs, sources, version, related | ✅ | Amounts hidden when unverified |
| Application-window logic (closed / not yet open) | ✅ | No seeded scheme currently has verified dates |
| Guided eligibility matcher with 5 required labels, reasons, missing info, disqualifiers | ✅ | Journey A |
| Only relevant questions asked; sensitive questions optional with "why we ask" | ✅ | Never asks caste/religion/Aadhaar |
| Correct answers / print / download results | ✅ | Answers kept in sessionStorage only |
| Constitution module (Preamble, Fundamental Rights, 21A, 22, 32, 226, 39A, 51A, structure overviews) | ✅ | Applies-to (persons vs citizens), against whom, limits, remedies |
| Everyday-rights explorer (arrest, police questioning, legal aid, RTI, wages, discrimination, education, tenants, public authority, service denied, emergency) | ✅ | Distinguishes constitutional / statutory / administrative / contractual |
| "Routes are not the same" (complaint vs grievance vs RTI vs appeal vs court) | ✅ | |
| Government services directory and detail pages | ✅ | Journey C |
| Complaint guides (8 categories) + escalation | ✅ | |
| Complaint letter & RTI application drafts (labelled DRAFT, never submitted) | ✅ | Journey D |
| Ask JanSaathi — RAG answers with citations, follow-ups, suggested questions, copy, download, report incorrect answer, language choice, new/clear conversation | ✅ | Tested with mocked provider + fallback |
| Opt-in on-device conversation history | 🟡 | localStorage, manual test only |
| Unified search (schemes, rights, guides, services) with EN/HI synonyms and misspellings | ✅ | Journey G |
| Report outdated / incorrect information | ✅ | |
| English + Hindi interface | ✅ | Navigation, key labels, summaries |
| Optional accounts, saved items, user-entered status, document checklist, reminders, export, delete | ✅ | Account journey |
| Offline banner; PWA manifest | 🟡 | No service worker / offline cache (deliberate — avoids showing stale data as fresh) |
| Emergency helplines (112, 1930, 1098, 181, 15100) | ✅ | |

## Admin features
| Feature | Status |
|---|---|
| Role-based access (user / editor / admin), denied for others | ✅ Journey I |
| Create, edit (JSON editor), validate records | ✅ |
| Publishing workflow Draft → Source review → Verified → Approved → Published → Unpublished | ✅ Journey E |
| Editor edits to published records send them back to review | ✅ |
| Record verification (status, date, note) | ✅ |
| Version history per record | ✅ |
| Review queue (stale / never-verified published records) | ✅ |
| Citizen reports triage | ✅ |
| Structured JSON import with per-record errors; imports always land as drafts | ✅ |
| Import history | ✅ |
| Audit log; user role management (admin only) | ✅ |
| Preview a draft before publishing | 🟡 Admin can view the full record; public preview of unpublished drafts not implemented |
| Manage categories / jurisdictions in the UI | ❌ Defined in code (`routers/public.py`) |

## Requires external credentials or integrations (⏳)
| Integration | What exists | What is needed |
|---|---|---|
| Gemini AI | Provider adapter, retries to fallback, prompt grounding, tests with mocked HTTP | `GEMINI_API_KEY`. **Not tested against the live Gemini API** in this build (no key available) |
| Other AI providers | `AIProvider` interface | An adapter class + key |
| Email (password reset, reminder emails) | Reminders stored and shown in dashboard | SMTP/email service; password reset **not implemented** |
| SMS / push notifications | — | Provider (e.g. SMS gateway) |
| myScheme / NSP / UMANG / API Setu data feeds | Validated import endpoint | Official API access & terms approval |
| Government application-status sync | Explicitly not implied; status is user-entered | Authorised government integration |
| Error monitoring (Sentry etc.) | Hook point in `main.py` middleware | DSN |
| Distributed rate limiting | In-memory limiter | Redis for multi-instance deployments |
