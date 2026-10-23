// Interface strings. English and Hindi are implemented; other languages are planned and NOT claimed as supported.
export type Lang = "en" | "hi";

const en = {
  skip: "Skip to main content",
  brandTag: "Independent citizen information",
  nav_home: "Home", nav_schemes: "Government Schemes", nav_rights: "Know Your Rights", nav_services: "Government Services",
  nav_complaints: "Complaints & Legal Aid", nav_ask: "Ask JanSaathi", nav_dashboard: "My Dashboard", nav_admin: "Admin",
  signin: "Sign in", signout: "Sign out", menu: "Menu", close: "Close",
  hero_title: "Know Your Rights. Discover Your Benefits.",
  hero_sub: "Tell us your situation. Discover your rights, benefits, and the official steps you can take.",
  search_placeholder: "Tell us what you need help with…", search: "Search",
  cta_schemes: "Find Government Schemes", cta_rights: "Understand My Rights", cta_ask: "Ask JanSaathi",
  cta_check: "Check what I may qualify for",
  popular_services: "Popular government services", browse_category: "Browse schemes by category", state_specific: "State-specific services",
  updates: "Recently verified information", how_it_works: "How JanSaathi works", transparency: "How we verify information",
  view_all: "View all",
  verified: "Verified", reviewed: "Reviewed", needs_verification: "Needs verification",
  stale: "Review overdue",
  official_link: "Official website", apply_official: "Apply on official portal",
  sources: "Official sources", last_verified: "Last verified", not_verified: "Not yet verified",
  save: "Save", saved: "Saved", report: "Report a problem",
  loading: "Loading…", retry: "Try again", no_results: "No results found",
  offline: "You are offline. Information shown may be out of date.",
  disclaimer: "JanSaathi is an independent information platform. It is not a Government of India website and is not affiliated with any government. Information is general guidance, not legal advice or an official decision.",
  ask_placeholder: "Ask about schemes, rights, certificates or complaints…",
  send: "Send", new_chat: "New conversation",
  eligibility: "Eligibility check", footer_privacy: "Privacy", footer_access: "Accessibility", footer_about: "About & sources", footer_contact: "Contact",
  coverage_warning: "This is not a complete list of government schemes. Coverage is growing; always check the official portal.",
};

const hi: typeof en = {
  skip: "मुख्य सामग्री पर जाएँ",
  brandTag: "स्वतंत्र नागरिक सूचना",
  nav_home: "मुखपृष्ठ", nav_schemes: "सरकारी योजनाएँ", nav_rights: "अपने अधिकार जानें", nav_services: "सरकारी सेवाएँ",
  nav_complaints: "शिकायत और कानूनी सहायता", nav_ask: "जनसाथी से पूछें", nav_dashboard: "मेरा डैशबोर्ड", nav_admin: "एडमिन",
  signin: "साइन इन", signout: "साइन आउट", menu: "मेन्यू", close: "बंद करें",
  hero_title: "अपने अधिकार जानें। अपने लाभ खोजें।",
  hero_sub: "अपनी स्थिति बताइए। अपने अधिकार, लाभ और आधिकारिक कदम जानिए।",
  search_placeholder: "बताइए आपको किस बारे में मदद चाहिए…", search: "खोजें",
  cta_schemes: "सरकारी योजनाएँ खोजें", cta_rights: "मेरे अधिकार समझें", cta_ask: "जनसाथी से पूछें",
  cta_check: "देखें मैं किन योजनाओं के लिए योग्य हो सकता/सकती हूँ",
  popular_services: "लोकप्रिय सरकारी सेवाएँ", browse_category: "श्रेणी के अनुसार योजनाएँ", state_specific: "राज्य-विशेष सेवाएँ",
  updates: "हाल में सत्यापित जानकारी", how_it_works: "जनसाथी कैसे काम करता है", transparency: "हम जानकारी कैसे सत्यापित करते हैं",
  view_all: "सभी देखें",
  verified: "सत्यापित", reviewed: "समीक्षित", needs_verification: "सत्यापन बाकी",
  stale: "समीक्षा लंबित",
  official_link: "आधिकारिक वेबसाइट", apply_official: "आधिकारिक पोर्टल पर आवेदन करें",
  sources: "आधिकारिक स्रोत", last_verified: "अंतिम सत्यापन", not_verified: "अभी सत्यापित नहीं",
  save: "सहेजें", saved: "सहेजा गया", report: "समस्या बताएँ",
  loading: "लोड हो रहा है…", retry: "फिर कोशिश करें", no_results: "कोई परिणाम नहीं मिला",
  offline: "आप ऑफ़लाइन हैं। दिखाई गई जानकारी पुरानी हो सकती है।",
  disclaimer: "जनसाथी एक स्वतंत्र सूचना मंच है। यह भारत सरकार की वेबसाइट नहीं है और किसी सरकार से संबद्ध नहीं है। यह सामान्य मार्गदर्शन है, कानूनी सलाह या आधिकारिक निर्णय नहीं।",
  ask_placeholder: "योजनाओं, अधिकारों, प्रमाण पत्रों या शिकायतों के बारे में पूछें…",
  send: "भेजें", new_chat: "नई बातचीत",
  eligibility: "पात्रता जाँच", footer_privacy: "गोपनीयता", footer_access: "सुगम्यता", footer_about: "परिचय और स्रोत", footer_contact: "संपर्क",
  coverage_warning: "यह सभी सरकारी योजनाओं की पूरी सूची नहीं है। हमेशा आधिकारिक पोर्टल पर जाँच करें।",
};

export const DICT = { en, hi };
export type Key = keyof typeof en;
export const t = (lang: Lang, k: Key) => DICT[lang][k] ?? DICT.en[k];
