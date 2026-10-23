# Security & privacy checklist

✅ = implemented · 🟡 = partial · ⏳ = operator task before launch

## Security
| Control | Status | Where |
|---|---|---|
| Passwords hashed with bcrypt (never plaintext) | ✅ tested | `security.py` |
| Session = signed HS256 JWT in `httpOnly`, `SameSite=Lax` cookie; `Secure` in production | ✅ | `routers/account.py` |
| `SECRET_KEY` mandatory in production (startup fails without it) | ✅ | `config.py` |
| CSRF: state-changing cookie-auth requests require `X-Requested-With: jansaathi` (not settable cross-site) | ✅ tested | `security.csrf_check` |
| Role-based authorization (user/editor/admin) on every admin endpoint; publish/approve admin-only | ✅ tested | `routers/admin.py` |
| Input validation (Pydantic, length limits, enums, eligibility answer whitelist) | ✅ tested | routers |
| SQL injection: ORM-parameterised queries only | ✅ | |
| Output encoding: React escapes all text; assistant output rendered without HTML | ✅ | `ask/page.tsx` `Rich` |
| Rate limiting on login/register, assistant, reports | 🟡 in-memory, per-process | `security.RateLimiter` — use Redis when scaled |
| Per-visitor IP for rate limits behind proxies | ✅ tested | `security.client_ip`: trusts `CF-Connecting-IP` / `True-Client-IP`, then the right-most public `X-Forwarded-For` hop — only when the request arrived from an internal (loopback/private) hop. On hosts **not** fronted by Cloudflare, strip `CF-Connecting-IP`/`True-Client-IP` at your proxy so clients cannot spoof them |
| Safe error messages (no stack traces to users; request IDs) | ✅ | `main.py` |
| Security headers (nosniff, frame DENY, referrer policy, permissions policy) | ✅ | `main.py`, `next.config.ts` |
| Audit log for create/update/transition/verify/import/role changes | ✅ tested | `AuditLog` |
| Secrets only on server; AI key sent via header, never in URL or frontend | ✅ tested | `ai/provider.py` |
| Open-redirect protection on `?next=` after login | ✅ | `login/page.tsx` |
| HTTPS | ⏳ | Terminate TLS at your host/proxy; set `COOKIE_SECURE=true` |
| Content-Security-Policy | ⏳ | Not yet set |
| Dependency vulnerability checks | 🟡 | `npm audit` clean at build time; add `pip-audit` + Dependabot |
| Password reset | ❌ | Needs an email provider |
| Account lockout / 2FA | ❌ | |
| Database backups & restore drills | ⏳ | See DEPLOYMENT.md |
| Independent penetration test | ⏳ | Not done |

## Privacy
| Principle | Implementation |
|---|---|
| Guest-first | Every information page, matcher and assistant work without an account |
| Minimum data | Accounts store email, password hash, optional display name, saved items, reminders |
| Never asked | Aadhaar, bank details, OTPs, other-service passwords, caste, religion, documents |
| Sensitive questions | Income and gender are optional, labelled "optional · private", with "why we ask" |
| Eligibility answers | Kept in sessionStorage; sent only to compute results; not stored server-side |
| Assistant | No server-side conversation storage; opt-in history in the user's browser only. When Gemini is configured, the question and retrieved public records are sent to Google — disclosed in the privacy notice |
| Reports | Stored without user identity |
| Export & deletion | Dashboard → "Download my data" / "Delete my account" (cascade deletes saved items and reminders) — tested |
| Logs | Method, path, status, duration, request ID. Query strings are not logged by the app middleware |
| Not official | Footer, About page, AI disclaimer and API description state independence |

## Before launch (operator)
- Legal review against the Digital Personal Data Protection Act, 2023 and IT Act rules; appoint a grievance officer if required.
- Review Gemini API data-use terms for your account tier; consider a paid tier with no training on inputs.
- Define log retention (suggested: 30 days) and backup retention.
- This checklist describes the software; it is **not** a claim of legal compliance.
