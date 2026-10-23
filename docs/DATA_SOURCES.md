# Data sources and their limitations

## How records are labelled
| Label | Meaning | What the UI does |
|---|---|---|
| `verified` | Facts confirmed against an official guideline/document on `last_verified` | Green badge |
| `reviewed` | Prepared from authoritative sources and cross-checked with reputable secondary sources; the live official page was **not** re-read on that date | Blue badge + "re-confirm on the official site" |
| `needs_verification` | Official source identified; details not yet confirmed | Amber warning; **benefit amounts are blocked by validation** |

Each record stores sources as `{url, organisation, title, type, retrieved}`, plus `last_verified`, `review_interval_days`, `verification_note` and a version history. Records past `last_verified + review_interval_days` show a "review overdue" warning and appear in the admin review queue. Old ≠ false.

## Seed coverage (as of 23 Oct 2026)
| Type | Count | verified | reviewed | needs_verification |
|---|---|---|---|---|
| Schemes | 22 (21 central, 1 Tamil Nadu) | 1 | 7 | 14 |
| Constitution entries | 27 | 0 | 27 | 0 |
| Guides (rights + complaints) | 19 | 0 | 14 | 5 |
| Services | 22 | 0 | 17 | 5 |

**This is a curated starting set, not a complete catalogue of Indian schemes.**

## Why so few are "verified"
During the build, official `.gov.in` sites (pmkisan.gov.in, myscheme.gov.in, pfrda.org.in and others) refused automated fetching (allowlist/robots restrictions). Rather than present remembered facts as verified, records were labelled honestly:
- **Central Sector Scheme of Scholarships** — verified against the Ministry of Education scheme guidelines (copy hosted by NIT Kurukshetra).
- **APY, PMJJBY, PMSBY, PM-JAY, Vay Vandana 70+, MUDRA** — `reviewed`: figures cross-checked against bank scheme pages and news coverage.
- **VB-G RAM G** — `reviewed` from Outlook India / Business Standard reporting that it replaced MGNREGA from 1 July 2026 (125 days). Official operational guidelines not yet read.
- **Constitution** — written from the Constitution text as amended; re-check against the Legislative Department's current PDF before launch.

## Primary sources referenced
- Constitution & central Acts: Legislative Department (legislative.gov.in), India Code (indiacode.nic.in)
- Schemes: respective ministry/scheme portals linked on each record (scholarships.gov.in, nha.gov.in, pmkisan.gov.in, pmfby.gov.in, pmuy.gov.in, nfsa.gov.in, pmayg.nic.in, pmay-urban.gov.in, nsap.nic.in, pmsvanidhi.mohua.gov.in, pmvishwakarma.gov.in, jansuraksha.gov.in, mudra.org.in, standupmitra.in, pmjdy.gov.in, pminternship.mca.gov.in, rural.gov.in, tn.gov.in)
- Services & grievances: services.india.gov.in, pgportal.gov.in, rtionline.dopt.gov.in, cic.gov.in, passportindia.gov.in, voters.eci.gov.in, parivahan.gov.in, crsorgi.gov.in, swavlambancard.gov.in, eshram.gov.in, udyamregistration.gov.in, nalsa.gov.in, jeevanpramaan.gov.in, cybercrime.gov.in, consumerhelpline.gov.in, edaakhil.nic.in, digilocker.gov.in, samadhan.labour.gov.in, nhrc.nic.in, ncw.nic.in, ncsc.nic.in, ncpcr.gov.in

## Guardrails in code (`backend/app/importer.py`)
- Action links (`apply_url`, `info_url`, `portal_url`) must be `https` on `.gov.in` / `.nic.in` or an explicit allowlist — prevents fabricated or look-alike URLs.
- Non-government sources are allowed only as typed provenance (`news_secondary`, `guideline_document`), never as action links.
- Every record needs ≥1 source with an organisation.
- `benefit_amount` is rejected on `needs_verification` records.
- `verified`/`reviewed` records require `last_verified`.

## Before public launch
1. Have a reviewer open each official page and record verification through the admin UI.
2. Seek permission/terms for machine-readable feeds (myScheme, API Setu, NSP) and import via the validated endpoint.
3. Expand state-level coverage, starting with the states of your users.
