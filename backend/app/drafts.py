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


def fir_refusal_draft(district: str, police_station: str, incident_date: str, incident_place: str, facts: str,
                      refusal_details: str, applicant_name: str, address: str, contact: str, today: date | None = None) -> str:
    today = today or date.today()
    return f"""{BANNER}

To,
The Superintendent of Police,
District {_clean(district, 120)}

Subject: Request to register an FIR under Section 173(4) of the Bharatiya Nagarik Suraksha Sanhita, 2023 — refusal by {_clean(police_station, 160)} Police Station

Respected Sir/Madam,

I, {_clean(applicant_name, 120)}, resident of {_clean(address, 400)}, wish to report the following:

1. On {_clean(incident_date, 40)}, at {_clean(incident_place, 200)}, the following happened:
{_clean(facts)}

2. I approached {_clean(police_station, 160)} Police Station to give this information and request registration of an FIR. {_clean(refusal_details, 1500)}

3. The facts stated above disclose a cognizable offence. Under Section 173 of the BNSS, information relating to a cognizable offence is required to be recorded, and the Supreme Court in Lalita Kumari v. Government of Uttar Pradesh (2013) held that registration of an FIR is mandatory in such cases.

I therefore request you to register an FIR on the above information, or to direct its registration and investigation under Section 173(4) of the BNSS, and to provide me a copy of the FIR free of cost.

I am enclosing copies of the documents and evidence available with me.

Yours faithfully,
{_clean(applicant_name, 120)}
Address: {_clean(address, 400)}
Contact: {_clean(contact, 200)}
Date: {today.isoformat()}

Signature: ____________

Enclosures: (list documents, photos, medical report, etc.)
"""


def consumer_notice_draft(company: str, company_address: str, product: str, purchase_date: str, order_ref: str, amount: str,
                          problem: str, relief: str, days: int, applicant_name: str, contact: str, today: date | None = None) -> str:
    today = today or date.today()
    ref = f"Order / invoice reference: {_clean(order_ref, 120)}\n" if order_ref.strip() else ""
    amt = f"Amount paid: {_clean(amount, 40)}\n" if amount.strip() else ""
    addr = f"\n{_clean(company_address, 400)}" if company_address.strip() else ""
    return f"""{BANNER}

To,
The Grievance Officer / Customer Care,
{_clean(company, 200)}{addr}

Subject: Complaint regarding {_clean(product, 200)} — request for resolution within {days} days

{ref}{amt}Date of purchase / service: {_clean(purchase_date, 40)}

Dear Sir/Madam,

I purchased / availed {_clean(product, 200)} from you on {_clean(purchase_date, 40)}. I am facing the following problem:

{_clean(problem)}

This amounts to a defect in goods / deficiency in service under the Consumer Protection Act, 2019.

I request you to: {_clean(relief, 1000)}

Please resolve this within {days} days of receiving this letter and confirm in writing. If it is not resolved, I will register a grievance with the National Consumer Helpline and may approach the appropriate Consumer Commission, for which I will rely on this letter.

Yours faithfully,
{_clean(applicant_name, 120)}
Contact: {_clean(contact, 200)}
Date: {today.isoformat()}
"""
