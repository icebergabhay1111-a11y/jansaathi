import type { Metadata } from "next";

export const metadata: Metadata = { title: "About, sources & privacy" };

const SOURCES = [
  ["The Constitution of India", "Legislative Department, Ministry of Law and Justice", "https://legislative.gov.in/constitution-of-india/"],
  ["India Code (central Acts)", "Ministry of Law and Justice", "https://www.indiacode.nic.in"],
  ["National Government Services Portal", "National Portal of India", "https://services.india.gov.in"],
  ["National Scholarships Portal", "Government of India", "https://scholarships.gov.in"],
  ["National Legal Services Authority", "NALSA", "https://nalsa.gov.in"],
  ["CPGRAMS public grievances", "DARPG", "https://pgportal.gov.in"],
  ["Ministry and scheme portals", "Linked on each record", ""],
];

export default function About() {
  return (
    <div className="mx-auto max-w-4xl space-y-10 px-4 py-10">
      <header>
        <h1 className="font-display text-4xl text-navy-900">About JanSaathi</h1>
        <p className="mt-3 text-lg">JanSaathi is an <strong>independent</strong>, non-partisan information platform. It is <strong>not</strong> a Government of India website, is not affiliated with any government, political party or campaign, and cannot approve applications, issue certificates or take government action.</p>
      </header>

      <section id="sources" aria-labelledby="sh">
        <h2 id="sh" className="font-display text-2xl text-navy-900">Sources and how we verify</h2>
        <p className="mt-2">Every record stores its source URL, organisation, retrieval date, verification status and last verification date. Records move through a review workflow (Draft → Source review → Verified → Approved → Published) before citizens see them.</p>
        <ul className="mt-3 list-disc space-y-1 pl-5">
          <li><strong>Verified</strong> — checked against an official document on the date shown.</li>
          <li><strong>Reviewed</strong> — prepared from authoritative sources and cross-checked, but not re-confirmed on the live official page on that date. Confirm before acting.</li>
          <li><strong>Needs verification</strong> — official source identified, details not yet confirmed. Benefit amounts are deliberately hidden.</li>
          <li>Records past their review date show a warning and enter the editors’ review queue. Old does not mean wrong.</li>
        </ul>
        <table className="mt-4 w-full overflow-hidden rounded-xl border border-line bg-white text-sm">
          <thead className="bg-ivory-dark text-left"><tr><th className="p-2">Source</th><th className="p-2">Organisation</th></tr></thead>
          <tbody>{SOURCES.map(([n, o, u]) => <tr key={n} className="border-t border-line"><td className="p-2">{u ? <a className="text-navy-700 underline" href={u} target="_blank" rel="noopener noreferrer">{n}</a> : n}</td><td className="p-2">{o}</td></tr>)}</tbody>
        </table>
        <h3 className="mt-5 font-semibold text-navy-900">Known limitations</h3>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>Coverage is a curated starting set — far from every central, state or district scheme in India.</li>
          <li>Many official portals could not be machine-read during preparation, so several records are labelled “Needs verification”.</li>
          <li>Hindi explanations are explanatory translations, not official translations. Only English and Hindi interfaces are available today.</li>
          <li>Application status shown in your dashboard is what you enter; it is not synced with any government system.</li>
        </ul>
      </section>

      <section id="privacy" aria-labelledby="ph">
        <h2 id="ph" className="font-display text-2xl text-navy-900">Privacy notice</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>You can use every information page, the eligibility check and the assistant <strong>without an account</strong>.</li>
          <li>We never ask for Aadhaar numbers, bank details, OTPs, passwords for other services, caste, religion or identity documents.</li>
          <li>Eligibility answers stay in your browser tab (session storage) and are sent to our server only to compute results; they are not saved.</li>
          <li>Assistant conversations are not stored on our servers. If you turn on “keep history”, it is stored only in your browser. When an AI provider is configured, your question and the retrieved public records are sent to that provider to generate the answer.</li>
          <li><strong>Voice input:</strong> in Chrome/Edge your speech is converted to text by the browser’s own speech service. In other browsers a short recording is sent to Google’s Gemini API only to convert it to text; JanSaathi does not store the audio.</li>
          <li><strong>Office finder:</strong> if you allow location (or type a place), it is sent from your browser directly to OpenStreetMap services to find nearby offices. JanSaathi’s server never receives your location.</li>
          <li>Document checklist ticks are saved only in your browser.</li>
          <li>If you create an account we store your email, a bcrypt-hashed password, your saved items and reminders. You can download or permanently delete them from your dashboard.</li>
          <li>Reports you send about wrong information are stored without your identity.</li>
          <li>Server logs keep request paths and timings for security and debugging; we do not sell data or use it for advertising.</li>
        </ul>
        <p className="mt-2 text-sm text-muted">This notice describes how the software behaves. It is not a claim of legal compliance; operators must review applicable Indian law (including the Digital Personal Data Protection Act, 2023) before launch.</p>
      </section>

      <section id="accessibility" aria-labelledby="ah">
        <h2 id="ah" className="font-display text-2xl text-navy-900">Accessibility</h2>
        <p className="mt-2">We aim to follow WCAG 2.2 AA: keyboard navigation, visible focus, skip link, labelled forms with clear errors, sufficient contrast, reduced-motion support and text-first layouts that work on slow connections and small screens. Please report barriers using “Report a problem” on any page.</p>
      </section>

      <section id="contact" aria-labelledby="ch">
        <h2 id="ch" className="font-display text-2xl text-navy-900">Contact</h2>
        <p className="mt-2">Use “Report a problem” on any record to flag errors. For your individual case, contact the responsible department through the official links on each page, or free legal aid at NALSA (15100).</p>
      </section>
    </div>
  );
}
