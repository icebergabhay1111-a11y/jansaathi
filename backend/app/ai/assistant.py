"""Grounded assistant (retrieval-augmented).

1. Retrieve the most relevant PUBLISHED records with the search engine.
2. If an AI provider is available, ask it to answer ONLY from those records.
3. Otherwise (no key, quota exhausted, error) return a deterministic answer built
   from the same records, clearly labelled as such.
Sources returned are always the retrieved records themselves — never model-invented links.
"""
from __future__ import annotations

import re

from ..search import search
from .provider import AIProvider, AIUnavailable

DISCLAIMER = ("JanSaathi is an independent information service, not a government body. This is general information, "
              "not legal advice or an official decision. Always confirm on the official source before acting.")
DISCLAIMER_HI = ("जनसाथी एक स्वतंत्र सूचना सेवा है, सरकारी संस्था नहीं। यह सामान्य जानकारी है, कानूनी सलाह या आधिकारिक निर्णय नहीं। "
                 "कोई भी कदम उठाने से पहले आधिकारिक स्रोत पर पुष्टि करें।")

SYSTEM = """You are JanSaathi, an independent civic-information assistant for people in India.
You are NOT a lawyer or a government official, and you are not affiliated with the Government of India.

STRICT RULES:
- Answer ONLY using the numbered SOURCE RECORDS provided. If they do not contain the answer, say clearly that you could not find it in JanSaathi's verified records and suggest which kind of official department or portal to check (use only URLs that appear in the records).
- Never invent schemes, amounts, deadlines, legal provisions, case names, phone numbers or URLs.
- Never guarantee eligibility, approval or a legal outcome. Use "you may be eligible" / "this may apply".
- If a record's status is "needs_verification" or "stale", say the user must confirm on the official site.
- Cite records inline like [1], [2] matching the record numbers.
- Distinguish constitutional rights, statutory rights, and scheme benefits.
- If important facts are missing (state, age, situation), ask 1–2 short clarifying questions at the end.
- Use simple, plain language. Short paragraphs or short bullet lists. For simple questions, answer briefly.
- For legal situations, recommend free legal aid (NALSA 15100) where the records mention it.
- Reply in {language}.
"""

LANG_NAMES = {"en": "English", "hi": "Hindi (Devanagari script, simple everyday words)",
              "ta": "Tamil (Tamil script, simple everyday words)"}
DISCLAIMER_TA = ("ஜன்சாதி ஒரு சுயாதீன தகவல் சேவை; அரசு அமைப்பு அல்ல. இது பொதுவான தகவல் மட்டுமே — சட்ட ஆலோசனையோ அதிகாரப்பூர்வ முடிவோ அல்ல. "
                 "எதையும் செய்வதற்கு முன் அதிகாரப்பூர்வ இணையதளத்தில் உறுதிப்படுத்தவும்.")
TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")
DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")

TRANSLATE_SYSTEM = ("Translate the user's question into a short list of English search keywords about Indian government "
                    "schemes, rights or services (e.g. 'old age pension Tamil Nadu documents'). Reply with the keywords only.")


def search_query_for(provider: AIProvider | None, question: str) -> tuple[str, str | None]:
    """Retrieval works on English/Hindi keywords. For Tamil (or any non-Latin, non-Devanagari) questions,
    ask the AI for English keywords; the original question is still what the AI answers."""
    if provider is None or not (TAMIL_RE.search(question) or (not question.isascii() and not DEVANAGARI_RE.search(question))):
        return question, None
    try:
        kw = provider.generate(TRANSLATE_SYSTEM, [{"role": "user", "content": question}]).strip().splitlines()[0][:300]
        return f"{question} {kw}", kw
    except AIUnavailable:
        return question, None


def _record_text(i: int, kind: str, o) -> tuple[str, dict]:
    if kind == "scheme":
        body = (f"SCHEME: {o.name}\nMinistry: {o.ministry}\nLevel: {o.level}; States: {', '.join(o.states)}\nSummary: {o.summary}\n"
                f"Eligibility: {'; '.join(o.eligibility_text)}\nExclusions: {'; '.join(o.exclusions)}\nBenefit: {o.benefit_amount or o.benefit_type + ' (amount not verified)'}\n"
                f"Documents: {'; '.join(o.documents)}\nHow to apply: {'; '.join(o.application_steps)}\nApply: {o.apply_url or 'see info link'}; Info: {o.info_url}")
        title, url, path = o.name, o.info_url or o.apply_url, f"/schemes/{o.slug}"
    elif kind == "right":
        body = (f"CONSTITUTION Article {o.article} — {o.title}\nApplies to: {o.applies_to}\nAgainst: {o.against_whom or ''}\nExplanation: {o.plain_en}\n"
                f"Limitations: {'; '.join(o.limitations)}\nRemedies: {'; '.join(o.remedies)}")
        title, url, path = f"Article {o.article}: {o.title}", (o.sources or [{}])[0].get("url"), f"/rights/{o.slug}"
    elif kind == "guide":
        laws = "; ".join(f"{x['law']} ({x['type']})" for x in o.law_basis)
        auth = "; ".join(f"{a['name']}{' ' + a['url'] if a.get('url') else ''}{' ☎ ' + a['phone'] if a.get('phone') else ''}" for a in o.authorities)
        body = (f"GUIDE: {o.title}\nSummary: {o.summary}\nLaw: {laws}\nImportant qualifications: {'; '.join(o.qualifications)}\n"
                f"Steps: {'; '.join(o.steps)}\nAuthorities: {auth}\nTime limits: {o.time_limits or 'not stated'}")
        title, url, path = o.title, next((a.get("url") for a in o.authorities if a.get("url")), None), f"/guides/{o.slug}"
    else:
        body = (f"SERVICE: {o.name}\nAuthority: {o.authority}\nSummary: {o.summary}\nWho: {o.who_can_use}\nOnline: {o.online}\nSteps: {'; '.join(o.steps)}\n"
                f"Fee: {o.fee or 'not stated'}\nProcessing time: {o.processing_time or 'not stated'}\nPortal: {o.portal_url}\nHelp: {o.help_channel or ''}")
        title, url, path = o.name, o.portal_url, f"/services/{o.slug}"
    status = o.verification_status
    lv = o.last_verified.isoformat() if o.last_verified else "not verified"
    text = f"[{i}] (status: {status}; last verified: {lv})\n{body}"
    meta = {"n": i, "kind": kind, "slug": o.slug, "title": title, "url": url, "path": path, "verification_status": status, "last_verified": None if not o.last_verified else lv}
    return text, meta


def retrieve(collections: dict, question: str, k: int = 6) -> list[dict]:
    hits = search(collections, question, limit=k)
    return [h for h in hits if h["score"] >= 2.0]


def suggested_followups(hits: list[dict], lang: str) -> list[str]:
    kinds = {h["kind"] for h in hits}
    out = []
    if "scheme" in kinds:
        out.append({"en": "Check my eligibility step by step", "hi": "मेरी पात्रता चरण-दर-चरण जाँचें", "ta": "என் தகுதியைப் படிப்படியாகச் சரிபார்க்கவும்"}[lang])
    if "right" in kinds or "guide" in kinds:
        out.append({"en": "How do I get free legal aid?", "hi": "मुझे मुफ़्त कानूनी सहायता कैसे मिलेगी?", "ta": "இலவச சட்ட உதவி எப்படிப் பெறுவது?"}[lang])
    out.append({"en": "Which documents will I need?", "hi": "मुझे कौन-से दस्तावेज़ चाहिए होंगे?", "ta": "எனக்கு என்ன ஆவணங்கள் தேவை?"}[lang])
    return out[:3]


def fallback_answer(hits: list[dict], metas: list[dict], lang: str, reason: str) -> str:
    if not hits:
        return {"en": "I could not find this in JanSaathi's records. Try different words, browse Schemes / Services, or check the National Government Services Portal (https://services.india.gov.in).",
                "hi": "मुझे यह जनसाथी के रिकॉर्ड में नहीं मिला। अलग शब्दों में खोजें, योजनाएँ/सेवाएँ देखें, या राष्ट्रीय सरकारी सेवा पोर्टल (https://services.india.gov.in) देखें।",
                "ta": "இதை ஜன்சாதி பதிவுகளில் கண்டுபிடிக்க முடியவில்லை. வேறு சொற்களில் தேடவும் அல்லது தேசிய அரசு சேவைகள் இணையதளத்தைப் (https://services.india.gov.in) பார்க்கவும். (I could not find this in JanSaathi's records.)"}[lang]
    head = {"en": "AI explanation is unavailable right now, so here are the most relevant records from JanSaathi's knowledge base:",
            "hi": "अभी AI व्याख्या उपलब्ध नहीं है, इसलिए जनसाथी के सबसे प्रासंगिक रिकॉर्ड दिए गए हैं:",
            "ta": "AI விளக்கம் இப்போது கிடைக்கவில்லை. தொடர்புடைய பதிவுகள் கீழே ஆங்கிலத்தில் உள்ளன. (AI is unavailable — records are shown in English.)"}[lang]
    lines = [head, ""]
    for h, m in zip(hits, metas):
        o = h["obj"]
        summary = getattr(o, "summary_hi", None) if lang == "hi" and getattr(o, "summary_hi", None) else (
            getattr(o, "plain_hi", None) if lang == "hi" and getattr(o, "plain_hi", None) else
            getattr(o, "summary", None) or getattr(o, "plain_en", ""))
        warn = " ⚠ needs official confirmation" if m["verification_status"] == "needs_verification" else ""
        lines.append(f"**[{m['n']}] {m['title']}**{warn}\n{summary}")
    return "\n\n".join(lines)


def answer(provider: AIProvider | None, collections: dict, question: str, history: list[dict], lang: str = "en") -> dict:
    lang = lang if lang in LANG_NAMES else "en"
    # retrieve on the question plus the last user turn for follow-ups like "what documents?"
    prev = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
    query, translated = search_query_for(provider, question)
    hits = retrieve(collections, f"{query} {prev}" if len(question.split()) < 5 and prev else query)
    blocks, metas = zip(*[_record_text(i + 1, h["kind"], h["obj"]) for i, h in enumerate(hits)]) if hits else ((), ())
    metas = list(metas)
    mode, reason, text = "fallback", None, None

    if provider and hits:
        ctx = "SOURCE RECORDS:\n\n" + "\n\n".join(blocks)
        msgs = [m for m in history[-6:] if m.get("role") in ("user", "assistant")]
        msgs.append({"role": "user", "content": f"{ctx}\n\nQUESTION: {question}"})
        try:
            text = provider.generate(SYSTEM.format(language=LANG_NAMES[lang]), msgs)
            mode = "ai"
        except AIUnavailable as e:
            reason = str(e)
    elif not provider:
        reason = "no AI provider configured"
    else:
        reason = "no matching records"

    if text is None:
        text = fallback_answer(list(hits), metas, lang, reason or "")

    cited = {int(n) for n in re.findall(r"\[(\d+)\]", text)}
    for m in metas:
        m["cited"] = m["n"] in cited
    return {
        "answer": text,
        "mode": mode,
        "mode_reason": reason,
        "provider": provider.name if (provider and mode == "ai") else None,
        "sources": metas,
        "found_sources": bool(hits),
        "followups": suggested_followups(list(hits), lang),
        "disclaimer": {"hi": DISCLAIMER_HI, "ta": DISCLAIMER_TA}.get(lang, DISCLAIMER),
        "search_keywords": translated,
    }
