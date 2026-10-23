"use client";
import Link from "next/link";
import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Globe, MapPin, Search } from "lucide-react";
import { Empty, ErrorBox, SkeletonCards, VerificationBadge } from "@/components/ui";
import { useApp } from "@/lib/providers";
import { useFetch } from "@/lib/useFetch";
import type { Card, Paged } from "@/lib/types";

const ONLINE: Record<string, string> = { yes: "Online", partial: "Online + visit", no: "In person", varies: "Varies by state" };

function ServicesInner() {
  const { t, lang } = useApp();
  const sp = useSearchParams();
  const router = useRouter();
  const [q, setQ] = useState(sp.get("q") || "");
  const { data, error, loading, reload } = useFetch<Paged<Card>>(`/services?${sp.toString()}`);
  const set = (k: string, v: string) => { const p = new URLSearchParams(sp.toString()); if (v) p.set(k, v); else p.delete(k); router.push(`/services?${p}`); };

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="font-display text-4xl text-navy-900">{t("nav_services")}</h1>
      <p className="mt-2 max-w-3xl text-muted">Certificates, registrations and public services — who provides them, what you need, and the official portal. JanSaathi does not issue any document.</p>
      <form className="card mt-6 grid gap-3 p-4 md:grid-cols-[2fr_1fr_1fr_auto]" onSubmit={(e) => { e.preventDefault(); set("q", q.trim()); }}>
        <div><label className="label" htmlFor="sq">Find a service or document</label><input id="sq" className="input" value={q} onChange={(e) => setQ(e.target.value)} placeholder="income certificate, passport, राशन कार्ड…" /></div>
        <div><label className="label" htmlFor="on">How to apply</label>
          <select id="on" className="input" value={sp.get("online") || ""} onChange={(e) => set("online", e.target.value)}>
            <option value="">Any</option>{Object.entries(ONLINE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select></div>
        <div><label className="label" htmlFor="lv">Provided by</label>
          <select id="lv" className="input" value={sp.get("level") || ""} onChange={(e) => set("level", e.target.value)}>
            <option value="">Any</option><option value="central">Central government</option><option value="state">State government</option>
          </select></div>
        <button className="btn btn-primary self-end"><Search size={16} aria-hidden />{t("search")}</button>
      </form>
      <div className="mt-6">
        {loading && <SkeletonCards />}
        {error && <ErrorBox message={error} onRetry={reload} />}
        {data && data.items.length === 0 && <Empty title={t("no_results")}><p>Try a different word, or check the <a className="underline" href="https://services.india.gov.in" target="_blank" rel="noopener noreferrer">National Government Services Portal</a>.</p></Empty>}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data?.items.map((s) => (
            <Link key={s.slug} href={`/services/${s.slug}`} className="card card-hover flex flex-col gap-2 p-5">
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="inline-flex items-center gap-1 rounded-full bg-ivory-dark px-2 py-0.5 font-semibold text-muted">{s.level === "state" ? <MapPin size={12} aria-hidden /> : <Globe size={12} aria-hidden />}{s.level === "state" ? "State" : "Central"}</span>
                <span className="rounded-full bg-navy-100 px-2 py-0.5 font-semibold text-navy-800">{ONLINE[s.online || "varies"]}</span>
                <VerificationBadge status={s.verification_status} freshness={s.freshness} />
              </div>
              <h2 className="font-display text-lg leading-snug text-navy-900">{lang === "hi" && s.title_hi ? s.title_hi : s.title}</h2>
              <p className="line-clamp-2 text-sm text-muted">{s.summary}</p>
              <p className="mt-auto text-xs text-muted">{s.authority}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function ServicesPage() {
  return <Suspense fallback={<div className="mx-auto max-w-7xl px-4 py-10"><SkeletonCards /></div>}><ServicesInner /></Suspense>;
}
