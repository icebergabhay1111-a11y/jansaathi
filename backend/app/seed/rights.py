"""Constitution of India — plain-language explainers.

Prepared from the text of the Constitution as amended. Hindi text is an
explanatory translation, NOT the official Hindi text of the Constitution.
verification_status = "reviewed": re-check against the Legislative Department's
current Constitution PDF before public launch.
"""

TODAY = "2026-10-23"
CONST_SRC = [
    {"url": "https://legislative.gov.in/constitution-of-india/", "organisation": "Legislative Department, Ministry of Law and Justice", "title": "The Constitution of India", "type": "primary_law", "retrieved": TODAY},
    {"url": "https://www.indiacode.nic.in", "organisation": "India Code (Ministry of Law and Justice)", "title": "India Code — central legislation", "type": "primary_law", "retrieved": TODAY},
]
COURTS = ["Supreme Court (Article 32)", "High Court (Article 226)"]
WRIT = "Writ petition in the High Court (Art. 226) or Supreme Court (Art. 32), usually with a lawyer; free legal aid is available to eligible persons through Legal Services Authorities."


def art(slug, article, part, group, title, title_hi, plain_en, plain_hi, protects, applies_to, against, limitations, examples, situations, remedies=None, authorities=None, related=None, order=0):
    return {
        "slug": slug, "article": article, "part": part, "group": group, "title": title, "title_hi": title_hi,
        "plain_en": plain_en, "plain_hi": plain_hi, "protects": protects, "applies_to": applies_to, "against_whom": against,
        "limitations": limitations, "examples": examples, "situations": situations,
        "remedies": remedies or [WRIT], "authorities": authorities or COURTS, "related": related or [], "order": order,
        "verification_status": "reviewed", "last_verified": TODAY, "review_interval_days": 365, "sources": CONST_SRC,
    }


STATE_NOTE = "Enforceable against 'the State' as defined in Article 12 — governments, legislatures, local authorities and other authorities under government control."

RIGHTS = [
    art("preamble", "Preamble", "Preamble", "Foundations", "The Preamble", "उद्देशिका (प्रस्तावना)",
        "The Preamble states who the Constitution comes from ('We, the people of India') and what it aims for: India as a sovereign, socialist, secular, democratic republic that secures justice (social, economic and political), liberty of thought, expression, belief, faith and worship, equality of status and opportunity, and fraternity assuring the dignity of the individual and the unity and integrity of the nation.",
        "उद्देशिका बताती है कि संविधान 'हम, भारत के लोग' द्वारा अपनाया गया है और भारत एक संप्रभु, समाजवादी, पंथनिरपेक्ष, लोकतांत्रिक गणराज्य है जो सभी को न्याय, स्वतंत्रता, समानता और बंधुता देने का लक्ष्य रखता है।",
        "Sets out the guiding values used to interpret the rest of the Constitution.", "Everyone (it is a statement of purpose)", None,
        ["The Preamble by itself is not directly enforceable in court; it guides interpretation.", "'Socialist', 'secular' and 'integrity' were added by the 42nd Amendment (1976)."],
        ["Courts refer to the Preamble's values when interpreting fundamental rights."], ["Understanding the purpose of the Constitution"],
        remedies=["Not directly enforceable; rights are enforced through specific Articles."], authorities=[], related=["art-14", "art-21"], order=0),

    art("art-14", "14", "Part III — Fundamental Rights", "Right to Equality (Arts. 14–18)", "Equality before law", "विधि के समक्ष समता",
        "The State cannot deny any person equality before the law or the equal protection of the laws within India. Laws and government action must not be arbitrary, and people in similar situations must be treated alike.",
        "राज्य भारत में किसी भी व्यक्ति को विधि के समक्ष समता या विधियों के समान संरक्षण से वंचित नहीं करेगा। सरकारी कार्रवाई मनमानी नहीं हो सकती।",
        "Protection against arbitrary and unequal treatment by the State.", "All persons — citizens and non-citizens", STATE_NOTE,
        ["Reasonable classification is allowed if it is based on an intelligible difference with a rational link to the law's objective (e.g. special provisions for children).", "It does not by itself cover private discrimination by individuals or private employers — other laws may."],
        ["A government tender rule that arbitrarily excludes some bidders may be challenged.", "Selection for a government benefit must follow published, non-arbitrary criteria."],
        ["Arbitrary denial of a government benefit", "Unequal treatment by a public authority"], related=["art-15", "art-16", "art-32"], order=14),

    art("art-15", "15", "Part III — Fundamental Rights", "Right to Equality (Arts. 14–18)", "Prohibition of discrimination on grounds of religion, race, caste, sex or place of birth", "धर्म, मूलवंश, जाति, लिंग या जन्मस्थान के आधार पर विभेद का प्रतिषेध",
        "The State must not discriminate against any citizen only because of religion, race, caste, sex, place of birth or any of these. No citizen can be barred, on these grounds, from shops, restaurants, hotels, places of public entertainment, or from wells, tanks, bathing ghats, roads and public places maintained by the State or dedicated to public use.",
        "राज्य किसी नागरिक के साथ केवल धर्म, मूलवंश, जाति, लिंग या जन्मस्थान के आधार पर भेदभाव नहीं करेगा। दुकानों, होटलों, सार्वजनिक कुओं, सड़कों आदि में प्रवेश से इन आधारों पर किसी को रोका नहीं जा सकता।",
        "Freedom from discrimination by the State, and equal access to public places.", "Citizens", "Mainly the State; clause 15(2) on access to shops, public places, wells etc. also applies to private persons.",
        ["The State may make special provisions for women and children (15(3)), for socially and educationally backward classes, SCs and STs (15(4), 15(5)), and for economically weaker sections (15(6), added in 2019)."],
        ["Being refused entry to a public well or a restaurant because of caste.", "A state rule giving benefits only to one religion's members without valid basis."],
        ["Caste-based denial of access", "Discrimination by a government office"], related=["art-14", "art-17", "guide-discrimination"], order=15),

    art("art-16", "16", "Part III — Fundamental Rights", "Right to Equality (Arts. 14–18)", "Equality of opportunity in public employment", "लोक नियोजन में अवसर की समता",
        "All citizens have equal opportunity in matters of employment or appointment to any office under the State. No citizen can be ineligible or discriminated against for such employment only on grounds of religion, race, caste, sex, descent, place of birth or residence.",
        "राज्य के अधीन नौकरियों में सभी नागरिकों को समान अवसर मिलेगा; धर्म, मूलवंश, जाति, लिंग, वंश, जन्मस्थान या निवास के आधार पर भेदभाव नहीं होगा।",
        "Fair access to government jobs.", "Citizens", STATE_NOTE,
        ["Reservation in appointments and promotions for backward classes, SCs/STs and economically weaker sections is permitted (16(4), 16(4A), 16(6)).", "Parliament may prescribe residence requirements for certain posts (16(3)).", "Does not apply to private-sector jobs."],
        ["A government recruitment notice that excludes women for no valid reason."], ["Government job recruitment", "Promotion in public service"], related=["art-14", "art-15"], order=16),

    art("art-17", "17", "Part III — Fundamental Rights", "Right to Equality (Arts. 14–18)", "Abolition of untouchability", "अस्पृश्यता का अंत",
        "'Untouchability' is abolished and its practice in any form is forbidden. Enforcing any disability arising out of untouchability is an offence punishable by law.",
        "'अस्पृश्यता' का अंत किया गया है और किसी भी रूप में उसका आचरण निषिद्ध है। इससे उत्पन्न किसी निर्योग्यता को लागू करना दंडनीय अपराध है।",
        "Freedom from untouchability practices.", "All persons", "Applies against everyone — the State and private individuals.",
        ["Enforced mainly through the Protection of Civil Rights Act, 1955 and the Scheduled Castes and Scheduled Tribes (Prevention of Atrocities) Act, 1989."],
        ["Being made to use separate utensils at a tea stall because of caste.", "Being denied entry to a temple or public place on caste grounds."],
        ["Caste-based exclusion"], remedies=["Report to the police (this is a criminal offence)", "Approach the National Commission for Scheduled Castes", WRIT],
        authorities=["Police", "National Commission for Scheduled Castes", "District Magistrate"], related=["art-15", "guide-discrimination"], order=17),

    art("art-19", "19", "Part III — Fundamental Rights", "Right to Freedom (Arts. 19–22)", "Protection of certain rights regarding freedom of speech, etc.", "वाक्-स्वातंत्र्य आदि विषयक कुछ अधिकारों का संरक्षण",
        "Every citizen has the right to: freedom of speech and expression; assemble peaceably and without arms; form associations, unions or co-operative societies; move freely throughout India; reside and settle in any part of India; and practise any profession or carry on any occupation, trade or business.",
        "प्रत्येक नागरिक को बोलने और अभिव्यक्ति, शांतिपूर्वक बिना हथियार इकट्ठा होने, संघ बनाने, देश में कहीं भी आने-जाने और बसने, तथा कोई भी पेशा या व्यापार करने की स्वतंत्रता है।",
        "Six basic freedoms of citizens.", "Citizens only (not non-citizens or companies as such)", STATE_NOTE,
        ["Each freedom is subject to 'reasonable restrictions' by law on grounds such as sovereignty and integrity of India, security of the State, public order, decency or morality, contempt of court, defamation and incitement to an offence (clauses 2–6).", "Can be suspended during a national emergency declared on grounds of war or external aggression (Article 358)."],
        ["Peaceful protest with police permission where required by law.", "A licensing rule for a trade must be reasonable, not a blanket ban."],
        ["Online posts and free speech", "Peaceful assembly", "Starting a business"], related=["art-14", "art-21"], order=19),

    art("art-20", "20", "Part III — Fundamental Rights", "Right to Freedom (Arts. 19–22)", "Protection in respect of conviction for offences", "अपराधों के लिए दोषसिद्धि के संबंध में संरक्षण",
        "(1) No one can be convicted for an act that was not an offence under the law in force when it was done, or given a heavier penalty than the law then allowed. (2) No one can be prosecuted and punished for the same offence more than once. (3) No one accused of an offence can be compelled to be a witness against themselves.",
        "(1) कोई व्यक्ति ऐसे कार्य के लिए दोषी नहीं ठहराया जाएगा जो करते समय अपराध नहीं था। (2) एक ही अपराध के लिए दो बार अभियोजन और दंड नहीं। (3) किसी अभियुक्त को अपने विरुद्ध गवाह बनने के लिए मजबूर नहीं किया जाएगा।",
        "Fair criminal process: no retrospective criminal punishment, no double jeopardy, no compelled self-incrimination.", "All persons, including non-citizens", "Mainly the State in criminal proceedings.",
        ["Protection against double jeopardy applies to prosecution AND punishment, typically before a court; departmental proceedings may still happen.", "Cannot be suspended even during an emergency (after the 44th Amendment, 1978)."],
        ["An accused person can refuse to answer questions that would incriminate them."], ["Police interrogation", "Criminal trial"], related=["art-21", "art-22", "guide-arrest"], order=20),

    art("art-21", "21", "Part III — Fundamental Rights", "Right to Freedom (Arts. 19–22)", "Protection of life and personal liberty", "प्राण और दैहिक स्वतंत्रता का संरक्षण",
        "No person can be deprived of their life or personal liberty except according to procedure established by law. The Supreme Court has held that this procedure must be fair, just and reasonable (Maneka Gandhi v. Union of India, 1978), and has read Article 21 to include the right to live with dignity, the right to privacy (K.S. Puttaswamy v. Union of India, 2017), speedy trial, free legal aid in criminal cases, and protection against custodial torture, among others.",
        "किसी भी व्यक्ति को उसके प्राण या दैहिक स्वतंत्रता से विधि द्वारा स्थापित प्रक्रिया के अनुसार ही वंचित किया जाएगा, अन्यथा नहीं। सर्वोच्च न्यायालय के अनुसार यह प्रक्रिया उचित, न्यायसंगत और तर्कसंगत होनी चाहिए; इसमें गरिमा के साथ जीने और निजता का अधिकार भी शामिल है।",
        "Life, liberty, dignity and privacy against unlawful State action.", "All persons — citizens and non-citizens", STATE_NOTE,
        ["Liberty can be restricted by a fair, just and reasonable law (e.g. lawful arrest).", "Many 'Article 21' rights recognised by courts depend on facts; a general claim like 'right to a job' is not automatically enforceable.", "Cannot be suspended during an emergency (after the 44th Amendment, 1978)."],
        ["Custodial torture violates Article 21.", "Unlawful detention without legal authority can be challenged by habeas corpus."],
        ["Arrest and detention", "Privacy", "Dignity in custody", "Delayed trial"],
        remedies=["Habeas corpus petition for unlawful detention", "Complaint to the National or State Human Rights Commission", WRIT],
        authorities=COURTS + ["National Human Rights Commission", "State Human Rights Commission"], related=["art-20", "art-22", "art-21a", "guide-arrest"], order=21),

    art("art-21a", "21A", "Part III — Fundamental Rights", "Right to Freedom (Arts. 19–22)", "Right to education", "शिक्षा का अधिकार",
        "The State must provide free and compulsory education to all children aged 6 to 14 years in the manner the State determines by law. That law is the Right of Children to Free and Compulsory Education Act, 2009 (RTE Act).",
        "राज्य 6 से 14 वर्ष के सभी बच्चों को कानून द्वारा निर्धारित तरीके से निःशुल्क और अनिवार्य शिक्षा देगा। यह कानून शिक्षा का अधिकार अधिनियम, 2009 है।",
        "Free and compulsory elementary education for children aged 6–14.", "Children aged 6–14", "The State (implemented through the RTE Act).",
        ["Inserted by the 86th Amendment (2002).", "Details — neighbourhood schools, the 25% admission quota for disadvantaged groups in private unaided schools, no capitation fee — come from the RTE Act, not from Article 21A alone."],
        ["A government school charging tuition fees to a 10-year-old.", "A private unaided school refusing admission under the RTE quota without valid reason."],
        ["School admission", "Fees for children 6–14"], remedies=["Complain to the local education authority", "Approach the State Commission for Protection of Child Rights", WRIT],
        authorities=["District Education Officer", "State Commission for Protection of Child Rights", "National Commission for Protection of Child Rights"], related=["art-21", "guide-education"], order=22),

    art("art-22", "22", "Part III — Fundamental Rights", "Right to Freedom (Arts. 19–22)", "Protection against arrest and detention in certain cases", "कुछ दशाओं में गिरफ्तारी और निरोध से संरक्षण",
        "A person who is arrested must be told the grounds of arrest as soon as possible, has the right to consult and be defended by a lawyer of their choice, and must be produced before the nearest magistrate within 24 hours of arrest (excluding travel time). They cannot be held in custody beyond that without a magistrate's order.",
        "गिरफ्तार व्यक्ति को जल्द से जल्द गिरफ्तारी के कारण बताए जाने चाहिए, उसे अपनी पसंद के वकील से सलाह लेने का अधिकार है, और उसे 24 घंटे के भीतर (यात्रा समय छोड़कर) निकटतम मजिस्ट्रेट के सामने पेश किया जाना चाहिए।",
        "Basic safeguards on arrest.", "All persons, with exceptions", "The State (police and other arresting authorities).",
        ["Clauses (1) and (2) do not apply to an enemy alien or to a person detained under a preventive detention law (22(3)).", "Preventive detention has its own safeguards in clauses (4)–(7), such as Advisory Board review for detention beyond three months.", "Detailed arrest procedure is in the Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS), which replaced the CrPC from 1 July 2024."],
        ["Being held at a police station for two days without being taken to a magistrate.", "Being refused access to a lawyer after arrest."],
        ["Arrest", "Detention", "Police custody"], remedies=["Ask for a lawyer; contact the Legal Services Authority (NALSA helpline 15100) for free legal aid", "Habeas corpus petition", WRIT],
        authorities=["Magistrate", "District Legal Services Authority"] + COURTS, related=["art-20", "art-21", "guide-arrest", "guide-police-questioning"], order=23),

    art("art-23", "23", "Part III — Fundamental Rights", "Right against Exploitation (Arts. 23–24)", "Prohibition of traffic in human beings and forced labour", "मानव के दुर्व्यापार और बलात्श्रम का प्रतिषेध",
        "Trafficking in human beings, begar (forced unpaid labour) and other similar forms of forced labour are prohibited, and any contravention is an offence punishable by law.",
        "मानव तस्करी, बेगार और इसी तरह का बलात्श्रम निषिद्ध है और इसका उल्लंघन दंडनीय अपराध है।",
        "Freedom from trafficking and forced labour.", "All persons", "Applies against the State and private persons.",
        ["The State may impose compulsory service for public purposes (e.g. in emergencies) without discrimination (23(2)).", "Paying less than the minimum wage has been treated by courts as a form of forced labour in some cases — facts matter."],
        ["Workers kept at a brick kiln to repay an 'advance' — bonded labour, banned by the Bonded Labour System (Abolition) Act, 1976."],
        ["Bonded labour", "Trafficking"], remedies=["Report to police or the District Magistrate (bonded labour)", "Call 112 in an emergency", WRIT],
        authorities=["Police", "District Magistrate", "National Human Rights Commission"], related=["art-24", "guide-wages"], order=24),

    art("art-24", "24", "Part III — Fundamental Rights", "Right against Exploitation (Arts. 23–24)", "Prohibition of employment of children in factories, etc.", "कारखानों आदि में बालकों के नियोजन का प्रतिषेध",
        "No child below 14 years can be employed to work in any factory or mine or engaged in any other hazardous employment.",
        "14 वर्ष से कम आयु के किसी बच्चे को कारखाने, खदान या किसी अन्य खतरनाक काम में नहीं लगाया जाएगा।",
        "Protection of children from hazardous work.", "Children below 14", "Applies to all employers.",
        ["The Child and Adolescent Labour (Prohibition and Regulation) Act, 1986 goes further: it generally prohibits employing children under 14 in any occupation (with limited exceptions like family enterprises after school hours) and adolescents (14–18) in hazardous work."],
        ["A 12-year-old working in a firecracker unit."], ["Child labour"], remedies=["Call Childline 1098", "Report to the labour department or police"],
        authorities=["Labour Department", "Police", "Child Welfare Committee"], related=["art-23", "art-21a"], order=25),

    art("art-25", "25", "Part III — Fundamental Rights", "Right to Freedom of Religion (Arts. 25–28)", "Freedom of conscience and free profession, practice and propagation of religion", "अंतःकरण की और धर्म के अबाध रूप से मानने, आचरण और प्रचार करने की स्वतंत्रता",
        "All persons are equally entitled to freedom of conscience and the right freely to profess, practise and propagate religion. Article 26 gives religious denominations rights to manage their own affairs; Article 27 bars taxes for promoting a particular religion; Article 28 limits religious instruction in State-funded educational institutions.",
        "सभी व्यक्तियों को अंतःकरण की स्वतंत्रता और धर्म को मानने, आचरण करने और प्रचार करने का समान अधिकार है।",
        "Freedom of belief and religious practice.", "All persons", STATE_NOTE,
        ["Subject to public order, morality, health and the other fundamental rights.", "The State may regulate secular activities associated with religion and make laws for social welfare and reform.", "'Propagate' does not include a right to forcibly convert."],
        ["Wearing religious symbols, subject to reasonable rules."], ["Religious practice"], related=["art-14", "art-29-30"], order=26),

    art("art-29-30", "29–30", "Part III — Fundamental Rights", "Cultural and Educational Rights (Arts. 29–30)", "Protection of interests of minorities; right of minorities to establish and administer educational institutions", "अल्पसंख्यकों के हितों का संरक्षण; शिक्षा संस्थाओं की स्थापना और प्रशासन का अधिकार",
        "Any section of citizens with a distinct language, script or culture has the right to conserve it (Art. 29(1)). No citizen can be denied admission to a State-run or State-aided educational institution only on grounds of religion, race, caste or language (Art. 29(2)). Religious and linguistic minorities have the right to establish and administer educational institutions of their choice (Art. 30).",
        "विशिष्ट भाषा, लिपि या संस्कृति वाले नागरिकों को उसे बचाए रखने का अधिकार है; धार्मिक और भाषाई अल्पसंख्यकों को अपनी पसंद की शिक्षा संस्थाएँ स्थापित करने और चलाने का अधिकार है।",
        "Cultural and educational rights of minorities and equal access to aided institutions.", "Citizens; Art. 30 — religious and linguistic minorities", STATE_NOTE,
        ["The State may regulate standards (e.g. qualifications of teachers) in minority institutions, but cannot destroy their minority character."],
        ["A State-aided college refusing admission to a student only because of their language."], ["School/college admission", "Running a minority institution"], related=["art-15", "art-25"], order=29),

    art("art-32", "32", "Part III — Fundamental Rights", "Right to Constitutional Remedies (Art. 32)", "Remedies for enforcement of rights", "संवैधानिक उपचारों का अधिकार",
        "You have the right to move the Supreme Court directly to enforce your fundamental rights. The Court can issue writs including habeas corpus (produce a detained person), mandamus (order an authority to do its legal duty), prohibition, certiorari (quash an unlawful decision) and quo warranto (challenge a person's right to hold public office). High Courts have similar and wider powers under Article 226.",
        "मौलिक अधिकारों को लागू कराने के लिए सीधे सर्वोच्च न्यायालय जाने का अधिकार। न्यायालय बंदी प्रत्यक्षीकरण, परमादेश, प्रतिषेध, उत्प्रेषण और अधिकार-पृच्छा जैसी रिट जारी कर सकता है। अनुच्छेद 226 के तहत उच्च न्यायालयों के पास भी ऐसी शक्तियाँ हैं।",
        "The right to go to court when a fundamental right is violated — itself a fundamental right.", "All persons whose fundamental rights are affected", STATE_NOTE,
        ["Only fundamental rights can be enforced under Article 32; other legal rights are usually pursued in the High Court under Article 226 or in ordinary courts/tribunals.", "Courts often expect you to use available statutory remedies first.", "Enforcement of specified rights may be suspended during an emergency (Article 359), but not Articles 20 and 21."],
        ["A habeas corpus petition when someone is detained illegally."], ["Any serious violation of a fundamental right by the State"],
        remedies=[WRIT, "Free legal aid through the Supreme Court Legal Services Committee or State/District Legal Services Authorities"],
        related=["art-21", "art-226", "art-39a"], order=32),

    art("art-226", "226", "Part VI — The States (High Courts)", "Right to Constitutional Remedies (Art. 32)", "Power of High Courts to issue certain writs", "कुछ रिट जारी करने की उच्च न्यायालयों की शक्ति",
        "Every High Court can issue writs to any person or authority within its territory, for enforcing fundamental rights and 'for any other purpose' — so it covers legal rights beyond fundamental rights.",
        "हर उच्च न्यायालय अपने क्षेत्र में मौलिक अधिकारों और 'किसी अन्य प्रयोजन' के लिए रिट जारी कर सकता है।",
        "Access to the High Court against unlawful action by public authorities.", "All persons", "Public authorities and, in some cases, private bodies performing public functions.",
        ["Not a fundamental right itself; the High Court has discretion and may ask you to use an alternative remedy first."],
        ["Challenging an illegal cancellation of a government licence."], ["Unlawful action by a public authority"], related=["art-32"], order=33),

    art("art-39a", "39A", "Part IV — Directive Principles of State Policy", "Directive Principles (Part IV)", "Equal justice and free legal aid", "समान न्याय और निःशुल्क विधिक सहायता",
        "The State must ensure that the legal system promotes justice on the basis of equal opportunity and must provide free legal aid so that no citizen is denied justice because of economic or other disabilities. This is implemented through the Legal Services Authorities Act, 1987 (NALSA, State, District and Taluk Legal Services Authorities).",
        "राज्य यह सुनिश्चित करेगा कि आर्थिक या अन्य कारणों से कोई नागरिक न्याय से वंचित न हो, और निःशुल्क विधिक सहायता देगा। यह विधिक सेवा प्राधिकरण अधिनियम, 1987 के माध्यम से लागू होता है।",
        "A directive for free legal aid and equal access to justice.", "Citizens (legal aid eligibility is set by the 1987 Act)", "A duty on the State.",
        ["Directive Principles are not directly enforceable in court (Article 37), but the right to free legal aid in criminal cases has been read into Article 21.", "Who gets free legal aid is decided by Section 12 of the Legal Services Authorities Act, 1987."],
        ["A worker who cannot afford a lawyer applies to the District Legal Services Authority."], ["Cannot afford a lawyer"],
        remedies=["Apply to the District Legal Services Authority or call NALSA helpline 15100"], authorities=["NALSA", "State Legal Services Authority", "District Legal Services Authority"],
        related=["art-21", "guide-legal-aid"], order=39),

    art("art-51a", "51A", "Part IVA — Fundamental Duties", "Fundamental Duties (Part IVA)", "Fundamental duties", "मूल कर्तव्य",
        "Every citizen has duties including to abide by the Constitution and respect its ideals, the National Flag and Anthem; uphold the sovereignty, unity and integrity of India; promote harmony and the dignity of women; protect the environment; develop scientific temper; safeguard public property and abjure violence; strive towards excellence; and, for parents/guardians, provide opportunities for education to children aged 6–14.",
        "प्रत्येक नागरिक का कर्तव्य है कि वह संविधान, राष्ट्रध्वज और राष्ट्रगान का सम्मान करे, देश की एकता बनाए रखे, सद्भाव और महिलाओं की गरिमा को बढ़ावा दे, पर्यावरण की रक्षा करे, सार्वजनिक संपत्ति सुरक्षित रखे और 6–14 वर्ष के बच्चों को शिक्षा का अवसर दे।",
        "Civic responsibilities of citizens.", "Citizens", None,
        ["Added by the 42nd Amendment (1976); the duty on parents regarding education was added by the 86th Amendment (2002).", "Not directly enforceable by courts, but used to interpret laws."],
        ["Not damaging public property during protests."], ["Civic responsibility"], remedies=["Not directly enforceable."], authorities=[], related=["preamble"], order=51),

    # --- Structure of government (overviews) ---
    art("overview-union-executive", "52–78", "Part V — The Union", "Union Government", "The President and the Union executive", "राष्ट्रपति और संघ की कार्यपालिका",
        "The President is the constitutional head of the Union. Executive power is exercised on the aid and advice of the Council of Ministers headed by the Prime Minister, which is collectively responsible to the Lok Sabha.",
        "राष्ट्रपति संघ के संवैधानिक प्रमुख हैं। कार्यपालिका शक्ति प्रधानमंत्री के नेतृत्व वाली मंत्रिपरिषद की सलाह पर प्रयोग की जाती है।",
        "Explains who runs the Union government.", "—", None, ["Overview only — see the Articles for exact powers."], [], ["Understanding government"], remedies=["—"], authorities=[], order=60),
    art("overview-parliament", "79–122", "Part V — The Union", "Parliament and Law-making", "Parliament and the legislative process", "संसद और विधायी प्रक्रिया",
        "Parliament consists of the President, the Rajya Sabha (Council of States) and the Lok Sabha (House of the People). A Bill becomes law after passing both Houses and receiving the President's assent; Money Bills can be introduced only in the Lok Sabha.",
        "संसद में राष्ट्रपति, राज्यसभा और लोकसभा शामिल हैं। विधेयक दोनों सदनों में पारित होकर राष्ट्रपति की स्वीकृति के बाद कानून बनता है।",
        "Explains how central laws are made.", "—", None, ["Overview only."], [], ["Understanding law-making"], remedies=["—"], authorities=[], order=61),
    art("overview-states", "152–237", "Part VI — The States", "State Governments", "State governments and legislatures", "राज्य सरकारें और विधानमंडल",
        "Each state has a Governor as constitutional head, a Council of Ministers headed by the Chief Minister, and a legislature (one or two Houses). The Seventh Schedule divides law-making subjects into Union, State and Concurrent Lists.",
        "प्रत्येक राज्य में राज्यपाल, मुख्यमंत्री के नेतृत्व में मंत्रिपरिषद और विधानमंडल होता है। सातवीं अनुसूची संघ, राज्य और समवर्ती सूचियों में विषय बाँटती है।",
        "Explains why many services (ration cards, certificates, land records) are run by states.", "—", None, ["Overview only."], [], ["Why services differ by state"], remedies=["—"], authorities=[], order=62),
    art("overview-judiciary", "124–147, 214–231", "Parts V & VI", "Judiciary", "The judiciary", "न्यायपालिका",
        "The Supreme Court is the highest court and guardian of fundamental rights. Each state or group of states has a High Court. Subordinate courts operate at district level. The judiciary can strike down laws and actions that violate the Constitution.",
        "सर्वोच्च न्यायालय देश का सर्वोच्च न्यायालय और मौलिक अधिकारों का संरक्षक है। राज्यों में उच्च न्यायालय और जिलों में अधीनस्थ न्यायालय हैं।",
        "Explains the court system.", "—", None, ["Overview only."], [], ["Going to court"], remedies=["—"], authorities=[], order=63),
    art("overview-constitutional-bodies", "148, 280, 315–323, 324, 338", "Various Parts", "Constitutional Bodies", "Constitutional bodies", "संवैधानिक निकाय",
        "Independent bodies set up by the Constitution include the Election Commission (Art. 324), the Comptroller and Auditor General (Art. 148), the Union and State Public Service Commissions (Arts. 315–323), the Finance Commission (Art. 280), and National Commissions for Scheduled Castes (Art. 338) and Scheduled Tribes (Art. 338A).",
        "संविधान द्वारा बनाए गए स्वतंत्र निकायों में निर्वाचन आयोग, नियंत्रक-महालेखा परीक्षक, लोक सेवा आयोग, वित्त आयोग और अनुसूचित जाति/जनजाति आयोग शामिल हैं।",
        "Explains independent oversight institutions.", "—", None, ["Overview only."], [], ["Knowing which body handles what"], remedies=["—"], authorities=[], order=64),
    art("overview-elections", "324–329", "Part XV — Elections", "Elections and Democratic Participation", "Elections and the right to vote", "चुनाव और मतदान",
        "Elections to Parliament and state legislatures are on the basis of adult suffrage: every citizen aged 18 or above who is not otherwise disqualified can register as a voter (Art. 326). The Election Commission superintends and conducts elections.",
        "संसद और विधानसभाओं के चुनाव वयस्क मताधिकार पर होते हैं: 18 वर्ष या उससे अधिक आयु का प्रत्येक योग्य नागरिक मतदाता बन सकता है।",
        "Explains voting rights.", "Citizens aged 18+", None, ["The voting age was lowered from 21 to 18 by the 61st Amendment (1988).", "The right to vote is a constitutional/statutory right, not a fundamental right."],
        [], ["Registering as a voter"], remedies=["Register or correct details through the Election Commission's voter portal"], authorities=["Election Commission of India"], related=["svc-voter-registration"], order=65),
    art("overview-amendments", "368", "Part XX — Amendment", "Constitutional Amendments", "Amending the Constitution", "संविधान का संशोधन",
        "Parliament can amend the Constitution under Article 368 by a special majority; some amendments affecting federal features also need ratification by half the state legislatures. Under the basic structure doctrine (Kesavananda Bharati, 1973), amendments cannot destroy the Constitution's basic structure.",
        "संसद अनुच्छेद 368 के तहत विशेष बहुमत से संविधान में संशोधन कर सकती है, लेकिन संविधान की मूल संरचना नष्ट नहीं की जा सकती।",
        "Explains how the Constitution changes.", "—", None, ["Overview only."], [], ["Understanding amendments"], remedies=["—"], authorities=[], order=66),
    art("overview-emergency", "352–360", "Part XVIII — Emergency Provisions", "Emergency Provisions", "Emergency provisions", "आपात उपबंध",
        "The Constitution provides for a national emergency (Art. 352, on war, external aggression or armed rebellion), failure of constitutional machinery in a state — President's Rule (Art. 356), and financial emergency (Art. 360). During a national emergency some rights can be restricted, but Articles 20 and 21 cannot be suspended.",
        "संविधान में राष्ट्रीय आपातकाल (अनु. 352), राज्य में राष्ट्रपति शासन (अनु. 356) और वित्तीय आपातकाल (अनु. 360) का प्रावधान है। आपातकाल में भी अनुच्छेद 20 और 21 निलंबित नहीं हो सकते।",
        "Explains emergency powers and their limits.", "—", None, ["Safeguards were strengthened by the 44th Amendment (1978)."], [], ["Understanding emergencies"], remedies=["—"], authorities=[], order=67),
    art("overview-local-government", "243–243ZG", "Parts IX & IXA", "Local Self-Government", "Panchayats and Municipalities", "पंचायत और नगरपालिकाएँ",
        "The 73rd and 74th Amendments (1992) gave constitutional status to Panchayats (rural) and Municipalities (urban), with regular elections, reserved seats including for women, and the Gram Sabha as the village assembly.",
        "73वें और 74वें संशोधन (1992) ने पंचायतों और नगरपालिकाओं को संवैधानिक दर्जा दिया; नियमित चुनाव, महिलाओं के लिए आरक्षण और ग्राम सभा का प्रावधान किया।",
        "Explains local government — often your first stop for certificates, water, sanitation and local schemes.", "—", None, ["Powers devolved vary by state law."], [], ["Local services", "Gram Sabha"], remedies=["—"], authorities=["Gram Panchayat", "Municipal Corporation / Council"], order=68),
]
