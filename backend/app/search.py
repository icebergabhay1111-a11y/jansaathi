"""Search across published content.

Field-weighted keyword scoring + bilingual (EN/HI) synonym expansion + fuzzy
matching for misspellings (RapidFuzz). Runs in Python so it works identically
on SQLite and PostgreSQL; at larger scale swap in PostgreSQL tsvector/pg_trgm.
"""
from __future__ import annotations

import re
from typing import Any

from rapidfuzz import fuzz

# Synonym groups: any term in a group expands to the whole group.
SYNONYMS = [
    {"scholarship", "scholarships", "छात्रवृत्ति", "स्कॉलरशिप", "vazhippu", "fellowship", "உதவித்தொகை", "கல்வி உதவித்தொகை"},
    {"pension", "पेंशन", "old age", "retirement", "वृद्धावस्था", "ஓய்வூதியம்", "முதியோர்"},
    {"farmer", "farmers", "kisan", "किसान", "agriculture", "कृषि", "crop", "फसल", "விவசாயி", "விவசாயம்", "பயிர்"},
    {"health", "स्वास्थ्य", "hospital", "अस्पताल", "medical", "treatment", "इलाज", "ayushman", "மருத்துவம்", "மருத்துவமனை", "சுகாதாரம்", "சிகிச்சை"},
    {"house", "housing", "home", "आवास", "घर", "awas", "shelter", "வீடு", "வீட்டுவசதி"},
    {"ration", "राशन", "food", "भोजन", "anna", "अन्न", "grain", "ரேஷன்", "உணவு", "அரிசி"},
    {"loan", "ऋण", "लोन", "credit", "mudra", "business", "கடன்", "தொழில்"},
    {"insurance", "बीमा", "bima", "cover", "காப்பீடு"},
    {"certificate", "प्रमाण पत्र", "प्रमाणपत्र", "praman", "சான்றிதழ்"},
    {"complaint", "grievance", "शिकायत", "problem", "समस्या", "புகார்"},
    {"rights", "right", "अधिकार", "adhikar", "உரிமை", "உரிமைகள்"},
    {"arrest", "गिरफ्तारी", "police", "पुलिस", "detention", "custody", "हिरासत", "கைது", "காவல்துறை", "போலீஸ்"},
    {"article", "अनुच्छेद", "anuchhed", "art"},
    {"equality", "समानता", "discrimination", "भेदभाव"},
    {"education", "शिक्षा", "school", "स्कूल", "college", "student", "छात्र", "विद्यार्थी", "கல்வி", "பள்ளி", "கல்லூரி", "மாணவர்"},
    {"job", "employment", "रोज़गार", "रोजगार", "work", "काम", "naukri", "नौकरी", "wage", "मजदूरी", "வேலை", "கூலி", "சம்பளம்"},
    {"women", "woman", "महिला", "girl", "बेटी", "daughter", "பெண்கள்", "பெண்", "மகள்"},
    {"lpg", "gas", "गैस", "cylinder", "ujjwala", "எரிவாயு", "சிலிண்டர்"},
    {"legal aid", "free lawyer", "विधिक सहायता", "कानूनी सहायता", "lawyer", "वकील", "சட்ட உதவி", "வழக்கறிஞர்"},
    {"rti", "right to information", "सूचना का अधिकार", "information", "தகவல் அறியும் உரிமை"},
    {"birth", "जन्म", "பிறப்பு"}, {"death", "मृत्यु", "இறப்பு"}, {"income", "आय", "வருமானம்"},
    {"voter", "मतदाता", "election", "चुनाव", "vote", "வாக்காளர்", "தேர்தல்"},
    {"passport", "पासपोर्ट", "கடவுச்சீட்டு", "பாஸ்போர்ட்"}, {"driving licence", "driving license", "ड्राइविंग लाइसेंस", "dl"},
    {"vendor", "street vendor", "रेहड़ी", "ठेला", "hawker"},
    {"cyber", "online fraud", "साइबर", "scam", "धोखाधड़ी", "fraud", "மோசடி", "சைபர்"},
    {"consumer", "उपभोक्ता", "refund", "defective", "நுகர்வோர்"},
    {"fir", "first information report", "एफआईआर", "प्राथमिकी", "முதல் தகவல் அறிக்கை", "எஃப்ஐஆர்"},
    {"aadhaar", "आधार", "ஆதார்", "uidai"},
    {"office", "कार्यालय", "அலுவலகம்", "csc", "e-sevai", "இ-சேவை", "taluk", "तहसील", "தாலுகா"},
]

FIELD_WEIGHTS = {"title": 5.0, "aliases": 4.0, "article": 6.0, "summary": 2.0, "body": 1.0}
TOKEN_RE = re.compile(r"[\w\u0900-\u097F\u0B80-\u0BFF]+", re.UNICODE)  # Latin, Devanagari, Tamil (incl. vowel signs)


def normalize(text: str) -> str:
    return " ".join(TOKEN_RE.findall((text or "").lower()))


def expand(query: str) -> list[str]:
    q = normalize(query)
    terms = set(q.split())
    padded = f" {q} "
    for group in SYNONYMS:
        if any(f" {normalize(g)} " in padded for g in group):
            terms |= {normalize(g) for g in group}
    # "article 21" / "अनुच्छेद 21" / "art21"
    for num in re.findall(r"(?:article|art|अनुच्छेद)\s*(\d+[a-z]?)", q):
        terms.add(f"__article_{num}")
    return [t for t in terms if t]


def _doc_fields(kind: str, obj: Any) -> dict[str, str]:
    if kind == "scheme":
        return {"title": f"{obj.name} {obj.name_hi or ''}", "aliases": " ".join(obj.aliases or []),
                "summary": f"{obj.summary} {obj.summary_hi or ''}",
                "body": " ".join([obj.ministry, " ".join(obj.categories), " ".join(obj.beneficiaries), " ".join(obj.eligibility_text), obj.benefit_type, " ".join(obj.documents)])}
    if kind == "right":
        return {"title": f"{obj.title} {obj.title_hi or ''}", "aliases": obj.group, "article": obj.article,
                "summary": f"{obj.plain_en} {obj.plain_hi or ''}",
                "body": " ".join([obj.protects, obj.applies_to, " ".join(obj.situations), " ".join(obj.examples)])}
    if kind == "guide":
        return {"title": f"{obj.title} {obj.title_hi or ''}", "aliases": " ".join(obj.keywords or []), "summary": obj.summary,
                "body": " ".join([" ".join(x.get("law", "") for x in obj.law_basis), " ".join(obj.steps), " ".join(a.get("name", "") for a in obj.authorities)])}
    return {"title": f"{obj.name} {obj.name_hi or ''}", "aliases": " ".join(obj.aliases or []), "summary": obj.summary,
            "body": " ".join([obj.authority, obj.who_can_use, " ".join(obj.documents)])}


def score_doc(kind: str, obj: Any, terms: list[str], raw_query: str) -> tuple[float, list[str]]:
    fields = {k: normalize(v) for k, v in _doc_fields(kind, obj).items()}
    score, why = 0.0, []
    for name, text in fields.items():
        if not text:
            continue
        tokens = set(text.split())
        hits = 0
        for t in terms:
            if t.startswith("__article_"):
                if name == "article" and text == t.removeprefix("__article_"):
                    score += 20
                    why.append(f"Article {text}")
                continue
            if (" " in t and t in text) or t in tokens:
                hits += 1
        if hits:
            score += FIELD_WEIGHTS[name] * hits
            why.append(name)
    # fuzzy: misspellings like "scolarship", "ayushmaan"
    nq = normalize(raw_query)
    if nq and len(nq) >= 4:
        f = max(fuzz.partial_ratio(nq, fields["title"]), fuzz.partial_ratio(nq, fields.get("aliases", "")))
        if f >= 85:
            score += (f - 80) / 4
            why.append("similar name")
    return score, sorted(set(why))


def search(collections: dict[str, list], query: str, limit: int = 20) -> list[dict]:
    terms = expand(query)
    if not terms:
        return []
    out = []
    for kind, objs in collections.items():
        for obj in objs:
            s, why = score_doc(kind, obj, terms, query)
            if s > 0:
                # prefer verified sources slightly (source quality)
                s += {"verified": 1.0, "reviewed": 0.5}.get(obj.verification_status, 0.0)
                out.append({"kind": kind, "obj": obj, "score": round(s, 2), "why": why})
    out.sort(key=lambda r: -r["score"])
    return out[:limit]
