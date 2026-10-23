"use client";
import Link from "next/link";
import { BadgeIndianRupee, FileSearch, Gavel, Phone, ShieldAlert, ShoppingBag, Siren } from "lucide-react";
import { useApp } from "@/lib/providers";

type QC = {
  id: string; icon: typeof Siren; tone: string;
  title: string; title_hi: string;
  steps: string[]; steps_hi: string[];
  guide: string; template?: { href: string; label: string; label_hi: string };
  call?: { number: string; label: string };
};

const CARDS: QC[] = [
  {
    id: "fir", icon: ShieldAlert, tone: "bg-red-50 text-red-800",
    title: "Police refuse to register your FIR", title_hi: "पुलिस FIR दर्ज न करे",
    steps: ["For a cognizable offence the police must register it — at any police station (Zero FIR).", "If refused, send your complaint in writing to the Superintendent of Police (BNSS s.173(4)).", "Still no action? Apply to the Magistrate (BNSS s.175(3)). Free legal aid: 15100."],
    steps_hi: ["संज्ञेय अपराध में पुलिस को FIR दर्ज करनी होती है — किसी भी थाने में (ज़ीरो FIR)।", "मना करने पर पुलिस अधीक्षक (SP) को लिखित शिकायत भेजें (BNSS धारा 173(4))।", "फिर भी कार्रवाई न हो तो मजिस्ट्रेट के पास जाएँ (धारा 175(3))। मुफ़्त कानूनी सहायता: 15100।"],
    guide: "/guides/guide-fir-refusal", template: { href: "/complaints?draft=fir#draft", label: "Letter to the SP", label_hi: "SP को पत्र" }, call: { number: "112", label: "Emergency" },
  },
  {
    id: "rti", icon: FileSearch, tone: "bg-navy-100 text-navy-800",
    title: "Get information with RTI", title_hi: "RTI से जानकारी पाएँ",
    steps: ["Write a specific question to the Public Information Officer — no reason needed.", "Fee ₹10 for central bodies (BPL exempt); reply due in 30 days.", "No reply? First appeal within 30 days, then the Information Commission."],
    steps_hi: ["लोक सूचना अधिकारी से स्पष्ट प्रश्न पूछें — कारण बताना ज़रूरी नहीं।", "केंद्रीय कार्यालयों के लिए ₹10 शुल्क (BPL मुक्त); 30 दिन में जवाब।", "जवाब न मिले तो 30 दिन में प्रथम अपील, फिर सूचना आयोग।"],
    guide: "/guides/guide-rti", template: { href: "/complaints?draft=rti#draft", label: "RTI application", label_hi: "RTI आवेदन" },
  },
  {
    id: "consumer", icon: ShoppingBag, tone: "bg-saffron-50 text-saffron-dark",
    title: "Defective product or bad service", title_hi: "ख़राब सामान या सेवा",
    steps: ["Write to the company first and keep proof (bill, messages).", "Not solved? Register on the National Consumer Helpline — call 1915.", "Then file online on e-Daakhil, generally within 2 years."],
    steps_hi: ["पहले कंपनी को लिखें और सबूत (बिल, संदेश) रखें।", "हल न हो तो राष्ट्रीय उपभोक्ता हेल्पलाइन 1915 पर शिकायत करें।", "फिर ई-दाखिल पर ऑनलाइन केस करें, आमतौर पर 2 साल के भीतर।"],
    guide: "/guides/complaint-consumer", template: { href: "/complaints?draft=consumer#draft", label: "Letter to the company", label_hi: "कंपनी को पत्र" }, call: { number: "1915", label: "Consumer helpline" },
  },
  {
    id: "arrest", icon: Gavel, tone: "bg-navy-100 text-navy-800",
    title: "If you are arrested", title_hi: "गिरफ़्तारी होने पर",
    steps: ["You must be told why, and can inform a family member or friend.", "You can talk to a lawyer; ask for free legal aid if needed.", "You must be taken to a magistrate within 24 hours."],
    steps_hi: ["आपको कारण बताया जाना चाहिए; परिवार/मित्र को सूचना दे सकते हैं।", "आप वकील से बात कर सकते हैं; ज़रूरत हो तो मुफ़्त कानूनी सहायता माँगें।", "24 घंटे में मजिस्ट्रेट के सामने पेश करना ज़रूरी है।"],
    guide: "/guides/guide-arrest", call: { number: "15100", label: "Free legal aid" },
  },
  {
    id: "cyber", icon: BadgeIndianRupee, tone: "bg-red-50 text-red-800",
    title: "Lost money to an online fraud", title_hi: "ऑनलाइन धोखाधड़ी में पैसे गए",
    steps: ["Call 1930 immediately — fast reporting can freeze the money.", "File on cybercrime.gov.in and keep the acknowledgement number.", "Tell your bank to block the card/UPI. No real officer does a 'digital arrest'."],
    steps_hi: ["तुरंत 1930 पर कॉल करें — जल्दी शिकायत से पैसा रोका जा सकता है।", "cybercrime.gov.in पर शिकायत करें और नंबर सँभालें।", "बैंक से कार्ड/UPI बंद कराएँ। 'डिजिटल अरेस्ट' जैसा कुछ नहीं होता।"],
    guide: "/guides/complaint-cyber-fraud", call: { number: "1930", label: "Cyber fraud" },
  },
];

export function QuickCards({ compact = false }: { compact?: boolean }) {
  const { lang } = useApp();
  const hi = lang === "hi";
  const cards = compact ? CARDS.slice(0, 3) : CARDS;
  return (
    <div className={`grid gap-4 ${compact ? "md:grid-cols-3" : "sm:grid-cols-2 lg:grid-cols-3"}`}>
      {cards.map((c) => {
        const I = c.icon;
        return (
          <article key={c.id} className="card flex flex-col p-5" aria-labelledby={`qc-${c.id}`}>
            <div className="flex items-center gap-3">
              <span className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${c.tone}`}><I size={20} aria-hidden /></span>
              <h3 id={`qc-${c.id}`} className="font-display text-lg leading-snug text-navy-900">{hi ? c.title_hi : c.title}</h3>
            </div>
            <ol className="mt-3 flex-1 list-decimal space-y-1.5 pl-5 text-sm">
              {(hi ? c.steps_hi : c.steps).map((st) => <li key={st}>{st}</li>)}
            </ol>
            <div className="mt-4 flex flex-wrap gap-2">
              <Link href={c.guide} className="btn btn-ghost !min-h-9 !px-3 text-sm">{hi ? "पूरी जानकारी" : "Full guide"}</Link>
              {c.template && <Link href={c.template.href} className="btn btn-primary !min-h-9 !px-3 text-sm">{hi ? c.template.label_hi : c.template.label}</Link>}
              {c.call && <a href={`tel:${c.call.number}`} className="btn btn-ghost !min-h-9 !px-3 text-sm"><Phone size={14} aria-hidden />{c.call.number}<span className="sr-only"> — {c.call.label}</span></a>}
            </div>
          </article>
        );
      })}
    </div>
  );
}
