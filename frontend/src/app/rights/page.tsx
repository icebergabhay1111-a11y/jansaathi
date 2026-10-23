"use client";
import Link from "next/link";
import { useState } from "react";
import { Gavel, HelpCircle, Search } from "lucide-react";
import { Empty, ErrorBox, Notice, SkeletonCards, VerificationBadge } from "@/components/ui";
import { useApp } from "@/lib/providers";
import { useFetch } from "@/lib/useFetch";
import { QuickCards } from "@/components/QuickCards";
import type { Card } from "@/lib/types";

const PROCEDURES = [
  ["Complaint", "Telling an authority (police, a department, a regulator) that something wrong happened, so it can act."],
  ["Grievance", "An administrative request to fix a service problem — e.g. on CPGRAMS or a state portal."],
  ["RTI request", "Asking a public authority for information or records under the RTI Act, 2005. It does not by itself fix the problem."],
  ["Administrative review / appeal", "Asking a higher officer in the same department to reconsider a decision."],
  ["Statutory authority", "Approaching a body created by law — e.g. Consumer Commission, Human Rights Commission, Information Commission."],
  ["Legal aid", "Free legal advice or a lawyer from a Legal Services Authority, for eligible people."],
  ["Court petition", "Filing a case in court, e.g. a writ petition under Article 226 or 32. Usually needs a lawyer."],
];

export default function RightsPage() {
  const { lang } = useApp();
  const [q, setQ] = useState("");
  const [active, setActive] = useState("");
  const rights = useFetch<{ items: Card[]; groups: string[] }>(`/rights${active ? `?q=${encodeURIComponent(active)}` : ""}`);
  const guides = useFetch<{ items: Card[] }>("/guides?kind=rights_question");

  const groups = rights.data ? rights.data.groups.filter((g) => rights.data!.items.some((i) => i.group === g)) : [];
  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="font-display text-4xl text-navy-900">Know your rights</h1>
      <p className="mt-2 max-w-3xl text-muted">The Constitution of India explained in plain language — with who each right protects, its limits, and what you can do.</p>
      <div className="mt-4"><Notice>General information, not legal advice. Hindi text is an explanatory translation, not the official Hindi text of the Constitution.</Notice></div>

      <form role="search" className="mt-6 flex gap-2" onSubmit={(e) => { e.preventDefault(); setActive(q.trim()); }}>
        <label htmlFor="rq" className="sr-only">Search rights</label>
        <input id="rq" className="input" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search: Article 21, arrest, equality, शिक्षा, अनुच्छेद 14…" />
        <button className="btn btn-primary"><Search size={16} aria-hidden />Search</button>
        {active && <button type="button" className="btn btn-ghost" onClick={() => { setQ(""); setActive(""); }}>Clear</button>}
      </form>

      <section aria-labelledby="qc" className="mt-10">
        <h2 id="qc" className="font-display text-3xl text-navy-900">Quick help — what to do right now</h2>
        <div className="mt-4"><QuickCards /></div>
      </section>

      <section aria-labelledby="ev" className="mt-12">
        <h2 id="ev" className="font-display text-3xl text-navy-900">Everyday questions</h2>
        {guides.loading && <SkeletonCards n={3} />}
        {guides.error && <ErrorBox message={guides.error} onRetry={guides.reload} />}
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {guides.data?.items.map((g) => (
            <Link key={g.slug} href={`/guides/${g.slug}`} className="card card-hover flex items-start gap-3 p-4">
              <HelpCircle size={20} className="mt-0.5 shrink-0 text-saffron-dark" aria-hidden />
              <span><span className="block font-semibold text-navy-900">{lang === "hi" && g.title_hi ? g.title_hi : g.title}</span><VerificationBadge status={g.verification_status} freshness={g.freshness} /></span>
            </Link>
          ))}
        </div>
      </section>

      <section aria-labelledby="const" className="mt-12">
        <h2 id="const" className="font-display text-3xl text-navy-900">The Constitution, article by article</h2>
        {rights.loading && <SkeletonCards />}
        {rights.error && <ErrorBox message={rights.error} onRetry={rights.reload} />}
        {rights.data && rights.data.items.length === 0 && <Empty title="No matching provisions"><p>Try another word, or <Link href={`/ask?q=${encodeURIComponent(active)}`} className="underline">ask JanSaathi</Link>.</p></Empty>}
        {groups.map((g) => (
          <div key={g} className="mt-6">
            <h3 className="text-sm font-bold uppercase tracking-wider text-saffron-dark">{g}</h3>
            <div className="mt-2 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {rights.data!.items.filter((i) => i.group === g).map((a) => (
                <Link key={a.slug} href={`/rights/${a.slug}`} className="card card-hover p-4">
                  <span className="text-xs font-bold text-muted">{a.article === "Preamble" ? "Preamble" : `Article ${a.article}`}</span>
                  <span className="mt-0.5 block font-display text-lg leading-snug text-navy-900">{lang === "hi" && a.title_hi ? a.title_hi : a.title}</span>
                  {a.applies_to && a.applies_to !== "—" && <span className="mt-1 block text-xs text-leaf-dark">Applies to: {a.applies_to}</span>}
                </Link>
              ))}
            </div>
          </div>
        ))}
      </section>

      <section aria-labelledby="proc" className="card mt-12 p-6">
        <h2 id="proc" className="flex items-center gap-2 font-display text-2xl text-navy-900"><Gavel size={22} aria-hidden />These routes are not the same</h2>
        <dl className="mt-4 grid gap-4 md:grid-cols-2">
          {PROCEDURES.map(([k, v]) => <div key={k}><dt className="font-semibold text-navy-900">{k}</dt><dd className="text-sm text-muted">{v}</dd></div>)}
        </dl>
      </section>
    </div>
  );
}
