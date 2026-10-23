"""Deterministic eligibility engine.

Each scheme carries a list of documented rules: {field, op, value, label}.
A rule evaluates to pass / fail / unknown (when the user did not answer).
The engine never declares anyone "eligible" — only a government process can.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .freshness import application_window

LABELS = {
    "potential_match": "Potential match",
    "more_info": "More information required",
    "appears_ineligible": "Appears ineligible based on the available information",
    "rules_need_verification": "Eligibility rules need verification",
    "period_may_have_closed": "Application period may have closed",
}

# Question bank. Sensitive questions are optional and explain why they are asked.
QUESTIONS: dict[str, dict[str, Any]] = {
    "state": {"q": "Which state or Union Territory do you live in?", "q_hi": "आप किस राज्य या केंद्र शासित प्रदेश में रहते हैं?", "type": "state", "why": "Some schemes are run only by particular states.", "sensitive": False},
    "age": {"q": "What is your age?", "q_hi": "आपकी आयु क्या है?", "type": "number", "min": 0, "max": 120, "why": "Many schemes have age limits.", "sensitive": False},
    "gender": {"q": "Gender (optional)", "q_hi": "लिंग (वैकल्पिक)", "type": "choice", "options": ["female", "male", "other"], "why": "A few schemes are only for women or girls. Skip if you prefer.", "sensitive": True},
    "occupation": {"q": "What best describes your current situation?", "q_hi": "आपकी वर्तमान स्थिति क्या है?", "type": "choice", "options": ["student", "farmer", "unorganised_worker", "salaried", "self_employed", "street_vendor", "artisan", "unemployed", "homemaker", "retired"], "why": "Schemes target specific groups such as students, farmers or workers.", "sensitive": False},
    "area": {"q": "Do you live in a rural or urban area?", "q_hi": "आप ग्रामीण क्षेत्र में रहते हैं या शहरी?", "type": "choice", "options": ["rural", "urban"], "why": "Some programmes are only for rural or only for urban households.", "sensitive": False},
    "annual_income": {"q": "Approximate annual household income — optional", "q_hi": "परिवार की अनुमानित वार्षिक आय — वैकल्पिक", "type": "number", "min": 0, "max": 100000000, "why": "Some schemes have income limits. Pick a range — we never ask for documents or exact figures.", "sensitive": True},
    "social_category": {"q": "Social category (optional)", "q_hi": "सामाजिक श्रेणी (वैकल्पिक)", "type": "choice", "options": ["general", "obc", "sc", "st"], "why": "Only a few schemes are reserved for SC/ST or OBC applicants. This is optional — skip it and those schemes will show as 'more information required'. Your answer is not stored.", "sensitive": True},
    "income_tax_payer": {"q": "Are you (or have you been) an income-tax payer?", "q_hi": "क्या आप आयकरदाता हैं या रहे हैं?", "type": "bool", "why": "Some schemes exclude income-tax payers.", "sensitive": True},
    "land_owner": {"q": "Does your family own cultivable land?", "q_hi": "क्या आपके परिवार के पास खेती योग्य भूमि है?", "type": "bool", "why": "Some farmer schemes require landholding.", "sensitive": False},
    "has_bank_account": {"q": "Do you have a savings bank or post office account?", "q_hi": "क्या आपका बचत बैंक या डाकघर खाता है?", "type": "bool", "why": "Several schemes pay benefits only into a bank account.", "sensitive": False},
    "study_level": {"q": "What are you studying?", "q_hi": "आप क्या पढ़ रहे हैं?", "type": "choice", "options": ["school", "undergraduate_regular", "postgraduate_regular", "diploma", "distance"], "why": "Scholarships depend on the course and mode of study.", "sensitive": False},
    "class12_top20": {"q": "Were you above the 80th percentile of successful candidates in your Class 12 board stream?", "q_hi": "क्या कक्षा 12 में आप अपने बोर्ड की स्ट्रीम में 80वें पर्सेंटाइल से ऊपर थे?", "type": "bool", "why": "Some merit scholarships use board percentiles.", "sensitive": False},
    "other_scholarship": {"q": "Are you already receiving another scholarship or fee waiver?", "q_hi": "क्या आपको पहले से कोई अन्य छात्रवृत्ति या शुल्क माफ़ी मिल रही है?", "type": "bool", "why": "Some scholarships cannot be combined with others.", "sensitive": False},
    "repaid_tarun": {"q": "Have you previously taken and fully repaid a MUDRA 'Tarun' loan?", "q_hi": "क्या आपने पहले मुद्रा 'तरुण' ऋण लेकर पूरा चुकाया है?", "type": "bool", "why": "Needed only for the higher MUDRA loan category.", "sensitive": False},
}


def _check(rule: dict, answers: dict) -> str:
    if rule["op"] == "any":  # pass if any sub-rule passes; fail only if all fail
        results = [_check(r, answers) for r in rule.get("rules", [])]
        if "pass" in results:
            return "pass"
        return "fail" if results and all(r == "fail" for r in results) else "unknown"
    field, op, val = rule["field"], rule["op"], rule.get("value")
    if field not in answers or answers[field] in (None, ""):
        return "unknown"
    a = answers[field]
    try:
        if op == "eq":
            ok = a == val
        elif op == "in":
            ok = a in val
        elif op == "not_in":
            ok = a not in val
        elif op == "gte":
            ok = float(a) >= float(val)
        elif op == "lte":
            ok = float(a) <= float(val)
        elif op == "between":
            ok = float(val[0]) <= float(a) <= float(val[1])
        elif op == "is_true":
            ok = a is True
        elif op == "is_false":
            ok = a is False
        else:
            return "unknown"
    except (TypeError, ValueError):
        return "unknown"
    return "pass" if ok else "fail"


def jurisdiction_ok(scheme_states: list[str], user_state: str | None) -> str:
    if not scheme_states or "ALL" in scheme_states:
        return "pass"
    if not user_state:
        return "unknown"
    return "pass" if user_state in scheme_states else "fail"


def evaluate(scheme: Any, answers: dict, interests: list[str] | None = None, today: date | None = None) -> dict:
    satisfied, missing, failed = [], [], []
    j = jurisdiction_ok(scheme.states, answers.get("state"))
    jl = "Available in your state/UT" if "ALL" not in (scheme.states or ["ALL"]) else "Central scheme (all states/UTs)"
    {"pass": satisfied, "fail": failed, "unknown": missing}[j].append({"field": "state", "label": jl if j != "fail" else "Not offered in your state/UT"})

    for rule in scheme.eligibility_rules or []:
        r = _check(rule, answers)
        item = {"field": rule.get("field") or ",".join(x["field"] for x in rule.get("rules", [])), "label": rule["label"]}
        {"pass": satisfied, "fail": failed, "unknown": missing}[r].append(item)

    window = application_window(scheme.opens_on, scheme.closes_on, today)
    if failed:
        label = "appears_ineligible"
    elif window == "closed_maybe":
        label = "period_may_have_closed"
    elif missing:
        label = "more_info"
    elif scheme.verification_status == "needs_verification":
        label = "rules_need_verification"
    else:
        label = "potential_match"

    total = len(satisfied) + len(missing) + len(failed)
    fit = len(satisfied) / total if total else 0.0
    relevance = 1.0 if interests and set(interests) & set(scheme.categories or []) else 0.0
    score = round(fit * 0.7 + relevance * 0.3 - (1.0 if failed else 0.0), 3)

    return {
        "slug": scheme.slug,
        "name": scheme.name,
        "name_hi": scheme.name_hi,
        "summary": scheme.summary,
        "categories": scheme.categories,
        "label": label,
        "label_text": LABELS[label],
        "satisfied": satisfied,
        "missing": missing,
        "failed": failed,
        "missing_fields": sorted({f for m in missing for f in m["field"].split(",")}),
        "verification_status": scheme.verification_status,
        "info_url": scheme.info_url,
        "apply_url": scheme.apply_url,
        "score": score,
    }


ORDER = {"potential_match": 0, "rules_need_verification": 1, "more_info": 2, "period_may_have_closed": 3, "appears_ineligible": 4}


def match(schemes: list, answers: dict, interests: list[str] | None = None, include_ineligible: bool = True, today: date | None = None) -> list[dict]:
    pool = [s for s in schemes if not interests or set(interests) & set(s.categories or [])] or schemes
    results = [evaluate(s, answers, interests, today) for s in pool]
    if not include_ineligible:
        results = [r for r in results if r["label"] != "appears_ineligible"]
    results.sort(key=lambda r: (ORDER[r["label"]], -r["score"], r["name"]))
    return results


def relevant_questions(schemes: list, interests: list[str] | None) -> list[dict]:
    """Ask only questions used by schemes in the selected categories (plus state)."""
    pool = [s for s in schemes if not interests or set(interests) & set(s.categories or [])] or schemes
    used = ["state"]
    for s in pool:
        for r in s.eligibility_rules or []:
            for f in ([x["field"] for x in r.get("rules", [])] if r["op"] == "any" else [r["field"]]):
                if f not in used:
                    used.append(f)
    order = list(QUESTIONS)
    used.sort(key=lambda f: order.index(f) if f in order else 999)
    return [{"field": f, **QUESTIONS[f]} for f in used if f in QUESTIONS]
