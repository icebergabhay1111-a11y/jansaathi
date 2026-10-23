"""Document registry: turns a scheme's free-text document list into a checklist that says
WHERE to get each document. Links point to JanSaathi service guides (which carry the official
portal + verification status) or directly to official portals."""
from __future__ import annotations

# Order matters: the first matching entry wins, so specific documents come before generic ones.
DOCUMENTS: list[dict] = [
    {"key": "aadhaar", "name": "Aadhaar", "name_hi": "आधार",
     "keywords": ["aadhaar", "e-kyc", "ekyc", "biometric verification"],
     "how": "Issued free by UIDAI at Aadhaar enrolment centres (many banks and post offices). Update or download e-Aadhaar online. Never share your Aadhaar number or OTP with anyone offering to 'help' with a scheme.",
     "how_hi": "UIDAI द्वारा आधार केंद्रों (कई बैंक और डाकघर) पर निःशुल्क बनता है। ई-आधार ऑनलाइन डाउनलोड करें। आधार नंबर या OTP किसी को न दें।",
     "links": [{"label": "Aadhaar guide", "href": "/services/svc-aadhaar"}]},
    {"key": "income_certificate", "name": "Income certificate", "name_hi": "आय प्रमाण पत्र",
     "keywords": ["income certificate", "income affidavit", "income declaration", "income proof"],
     "how": "Issued by your state Revenue Department (tehsil/taluk office) — apply on your state's e-District portal or at a Common Service Centre.",
     "how_hi": "राज्य राजस्व विभाग (तहसील कार्यालय) जारी करता है — राज्य के ई-डिस्ट्रिक्ट पोर्टल या जन सेवा केंद्र पर आवेदन करें।",
     "links": [{"label": "Income certificate guide", "href": "/services/svc-income-certificate"}, {"label": "Find an office near me", "href": "/offices"}]},
    {"key": "caste_certificate", "name": "Caste / community certificate", "name_hi": "जाति प्रमाण पत्र",
     "keywords": ["caste certificate", "community certificate", "sc/st certificate"],
     "how": "Issued by the competent state authority (usually the tehsil/taluk office). Apply on the state e-District portal or at a CSC.",
     "how_hi": "राज्य के सक्षम अधिकारी (आमतौर पर तहसील) द्वारा जारी। ई-डिस्ट्रिक्ट पोर्टल या जन सेवा केंद्र पर आवेदन करें।",
     "links": [{"label": "Caste certificate guide", "href": "/services/svc-caste-certificate"}]},
    {"key": "domicile", "name": "Domicile / residence certificate", "name_hi": "निवास प्रमाण पत्र",
     "keywords": ["domicile", "residence certificate", "nativity"],
     "how": "Issued by the state Revenue Department through the e-District portal or tehsil office.",
     "how_hi": "राज्य राजस्व विभाग द्वारा ई-डिस्ट्रिक्ट पोर्टल या तहसील से जारी।",
     "links": [{"label": "Domicile certificate guide", "href": "/services/svc-domicile"}]},
    {"key": "disability_certificate", "name": "Disability certificate / UDID card", "name_hi": "दिव्यांगता प्रमाण पत्र / UDID",
     "keywords": ["disability certificate", "udid"],
     "how": "Apply on the national UDID portal; a medical board at a designated hospital assesses and issues it.",
     "how_hi": "UDID पोर्टल पर आवेदन करें; निर्धारित अस्पताल का मेडिकल बोर्ड जाँच कर जारी करता है।",
     "links": [{"label": "UDID guide", "href": "/services/svc-udid"}]},
    {"key": "ration_card", "name": "Ration card", "name_hi": "राशन कार्ड",
     "keywords": ["ration card", "nfsa card", "phh", "antyodaya"],
     "how": "Issued by your state Food & Civil Supplies Department — apply on the state portal, at the food office or a CSC.",
     "how_hi": "राज्य खाद्य एवं नागरिक आपूर्ति विभाग द्वारा जारी — राज्य पोर्टल, खाद्य कार्यालय या जन सेवा केंद्र पर आवेदन करें।",
     "links": [{"label": "Ration card guide", "href": "/services/svc-ration-card"}]},
    {"key": "bpl", "name": "BPL proof", "name_hi": "बीपीएल प्रमाण",
     "keywords": ["bpl"],
     "how": "Below-poverty-line status is decided under state criteria — ask your Gram Panchayat / municipal office or state social welfare department; an AAY/priority ration card is often accepted.",
     "how_hi": "बीपीएल स्थिति राज्य मानदंडों से तय होती है — ग्राम पंचायत/नगर कार्यालय या समाज कल्याण विभाग से पूछें।",
     "links": [{"label": "Ration card guide", "href": "/services/svc-ration-card"}]},
    {"key": "birth_certificate", "name": "Birth certificate / age proof", "name_hi": "जन्म प्रमाण पत्र / आयु प्रमाण",
     "keywords": ["birth certificate", "age proof", "date of birth"],
     "how": "Issued by the local Registrar of Births and Deaths (municipality / panchayat). Free if registered within 21 days.",
     "how_hi": "स्थानीय जन्म-मृत्यु रजिस्ट्रार (नगर पालिका/पंचायत) द्वारा जारी। 21 दिन में पंजीकरण निःशुल्क।",
     "links": [{"label": "Birth certificate guide", "href": "/services/svc-birth-certificate"}]},
    {"key": "land_records", "name": "Land record / tenancy proof", "name_hi": "भूमि अभिलेख",
     "keywords": ["land record", "tenancy", "sowing certificate", "sowing declaration", "khatauni", "patta"],
     "how": "Copies of land records come from the state Revenue Department's land-records portal or the tehsil/patwari office.",
     "how_hi": "भूमि अभिलेख राज्य राजस्व विभाग के पोर्टल या तहसील/पटवारी से मिलते हैं।",
     "links": [{"label": "Land records guide", "href": "/services/svc-land-records"}]},
    {"key": "bank_account", "name": "Savings bank / post office account", "name_hi": "बचत बैंक / डाकघर खाता",
     "keywords": ["bank account", "savings bank", "post office account", "savings account", "bank statement", "account in the student"],
     "how": "Open a zero-balance basic savings account at any bank or Bank Mitra under PM Jan Dhan Yojana, or a post office savings account. Link it with Aadhaar at your bank if the scheme pays by DBT.",
     "how_hi": "किसी भी बैंक में जन धन योजना के तहत शून्य-शेष खाता या डाकघर बचत खाता खोलें। DBT के लिए बैंक में आधार लिंक कराएँ।",
     "links": [{"label": "Jan Dhan account", "href": "/schemes/pm-jan-dhan-yojana"}]},
    {"key": "marksheet", "name": "Marksheet / educational certificate", "name_hi": "अंकतालिका",
     "keywords": ["marksheet", "mark sheet", "class 12", "educational certificate"],
     "how": "Get it from your school/board; many boards issue digital marksheets in DigiLocker.",
     "how_hi": "स्कूल/बोर्ड से लें; कई बोर्ड डिजीलॉकर में डिजिटल अंकतालिका देते हैं।",
     "links": [{"label": "DigiLocker guide", "href": "/services/svc-digilocker"}]},
    {"key": "admission_proof", "name": "Admission / bonafide certificate", "name_hi": "प्रवेश / बोनाफाइड प्रमाण पत्र",
     "keywords": ["admission proof", "bonafide", "institution"],
     "how": "Ask your college or school office for a bonafide or admission certificate.",
     "how_hi": "अपने कॉलेज/स्कूल कार्यालय से बोनाफाइड या प्रवेश प्रमाण पत्र लें।", "links": []},
    {"key": "job_card", "name": "Job card", "name_hi": "जॉब कार्ड",
     "keywords": ["job card"],
     "how": "Issued and renewed (with e-KYC) by your Gram Panchayat.",
     "how_hi": "ग्राम पंचायत जारी और नवीनीकरण (ई-केवाईसी सहित) करती है।",
     "links": [{"label": "Find a panchayat office", "href": "/offices"}]},
    {"key": "vending_certificate", "name": "Certificate of vending / ULB recommendation", "name_hi": "वेंडिंग प्रमाण पत्र",
     "keywords": ["certificate of vending", "letter of recommendation", "vending"],
     "how": "Issued by your Urban Local Body (municipal corporation / council) — the town vending committee.",
     "how_hi": "नगर निकाय (नगर निगम/परिषद) की टाउन वेंडिंग कमेटी जारी करती है।", "links": []},
    {"key": "identity_proof", "name": "Identity & address proof (KYC)", "name_hi": "पहचान और पता प्रमाण (KYC)",
     "keywords": ["identity", "kyc", "address proof", "id card", "officially valid"],
     "how": "Commonly accepted: Aadhaar, voter ID, passport, driving licence or NREGA job card. Show it to the bank/office directly.",
     "how_hi": "सामान्यतः मान्य: आधार, मतदाता पहचान पत्र, पासपोर्ट, ड्राइविंग लाइसेंस। सीधे बैंक/कार्यालय में दिखाएँ।",
     "links": [{"label": "Voter ID", "href": "/services/svc-voter-registration"}, {"label": "Aadhaar", "href": "/services/svc-aadhaar"}]},
    {"key": "business_plan", "name": "Business plan / quotations", "name_hi": "व्यवसाय योजना / कोटेशन",
     "keywords": ["business plan", "quotation"],
     "how": "Prepare it yourself: what you will sell, costs, and supplier quotations for items to buy. Bank staff or a District Industries Centre can guide you.",
     "how_hi": "स्वयं तैयार करें: क्या बेचेंगे, लागत, और खरीदने वाले सामान के कोटेशन। बैंक या जिला उद्योग केंद्र मदद कर सकते हैं।", "links": []},
]


def classify(text: str) -> dict | None:
    t = (text or "").lower()
    for d in DOCUMENTS:
        if any(k in t for k in d["keywords"]):
            return {k: d[k] for k in ("key", "name", "name_hi", "how", "how_hi", "links")}
    return None


def checklist(documents: list[str]) -> list[dict]:
    """[{text, doc|None}] — duplicates of the same document type are merged."""
    out, seen = [], set()
    for text in documents or []:
        doc = classify(text)
        if doc and doc["key"] in seen:
            continue
        if doc:
            seen.add(doc["key"])
        out.append({"text": text, "doc": doc})
    return out
