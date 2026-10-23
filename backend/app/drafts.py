"""Deterministic draft generators. Output is always a DRAFT for the user to review and submit
themselves — JanSaathi never submits anything on the user's behalf."""
from __future__ import annotations

from datetime import date

BANNER = "DRAFT — prepared by JanSaathi for your review. It has NOT been submitted anywhere. Check every detail before you send it."


def _clean(s: str | None, limit: int = 4000) -> str:
    return (s or "").strip()[:limit]


def rti_draft(public_authority: str, information_sought: list[str], applicant_name: str, address: str, bpl: bool = False, today: date | None = None) -> str:
    today = today or date.today()
    items = "\n".join(f"{i}. {_clean(q, 600)}" for i, q in enumerate(information_sought, 1) if q.strip())
    fee = ("I belong to the Below Poverty Line category and am exempt from the fee; a copy of my BPL certificate is attached."
           if bpl else "The application fee has been paid as applicable (₹10 for central public authorities; state rates may differ).")
    return f"""{BANNER}

To,
The Public Information Officer,
{_clean(public_authority, 300)}

Subject: Application under Section 6(1) of the Right to Information Act, 2005

Sir/Madam,

I request the following information under the Right to Information Act, 2005:

{items}

{fee}

If this information is held by another public authority, kindly transfer this application under Section 6(3) of the Act and inform me.

Please provide the information within the time limit under Section 7 of the Act.

Name: {_clean(applicant_name, 120)}
Address for correspondence: {_clean(address, 400)}
Date: {today.isoformat()}

Signature: ____________
"""


def complaint_draft(authority: str, subject: str, facts: str, relief: str, applicant_name: str, contact: str, reference_numbers: str = "", today: date | None = None) -> str:
    today = today or date.today()
    ref = f"\nReference / application number(s): {_clean(reference_numbers, 300)}\n" if reference_numbers.strip() else ""
    return f"""{BANNER}

To,
{_clean(authority, 300)}

Subject: {_clean(subject, 200)}
{ref}
Respected Sir/Madam,

I wish to bring the following matter to your attention:

{_clean(facts)}

I request that you kindly:
{_clean(relief, 1500)}

I am attaching copies of relevant documents. Please acknowledge receipt of this complaint and provide a reference number so that I can track it.

Yours faithfully,
{_clean(applicant_name, 120)}
Contact: {_clean(contact, 200)}
Date: {today.isoformat()}
"""
