"use client";
import Link from "next/link";
import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Search } from "lucide-react";
import { Empty, ErrorBox, ResultCard, SkeletonCards } from "@/components/ui";
import { useApp } from "@/lib/providers";
import { useFetch } from "@/lib/useFetch";
import type { Card } from "@/lib/types";

const TYPES = [["", "All"], ["scheme", "Schemes"], ["right", "Constitution"], ["guide", "Guides"], ["service", "Services"]];

function SearchInner() {
  const { t } = useApp();
  const sp = useSearchParams();
  const router = useRouter();
  const q = sp.get("q") || "";
  const type = sp.get("type") || "";
  const [input, setInput] = useState(q);
  const { data, error, loading, reload } = useFetch<{ results: (Card & { score: number })[]; suggestions: string[] }>(
    q ? `/search?q=${encodeURIComponent(q)}${type ? `&type=${type}` : ""}` : null);
  const go = (nq: string, nt = type) => router.push(`/search?q=${encodeURIComponent(nq)}${nt ? `&type=${nt}` : ""}`);

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="font-display text-4xl text-navy-900">Search</h1>
      <form role="search" onSubmit={(e) => { e.preventDefault(); if (input.trim()) go(input.trim()); }} className="mt-5 flex gap-2">
        <label htmlFor="sq" className="sr-only">Search</label>
        <input id="sq" className="input" value={input} onChange={(e) => setInput(e.target.value)} placeholder={t("search_placeholder")} />
        <button className="btn btn-primary"><Search size={16} aria-hidden />{t("search")}</button>
      </form>
      <div className="mt-4 flex flex-wrap gap-2" role="group" aria-label="Filter by type">
        {TYPES.map(([v, l]) => (
          <button key={v} onClick={() => q && go(q, v)} aria-pressed={type === v} className={`rounded-full px-3.5 py-1.5 text-sm font-semibold ${type === v ? "bg-navy-900 text-white" : "border border-line bg-white text-navy-900"}`}>{l}</button>
        ))}
      </div>
      <div className="mt-6">
        {!q && <p className="text-muted">Type a question or keyword — in English or Hindi.</p>}
        {loading && <SkeletonCards />}
        {error && <ErrorBox message={error} onRetry={reload} />}
        {data && data.results.length === 0 && (
          <Empty title={t("no_results")}>
            <p>Try one of these, or ask the assistant in your own words:</p>
            <div className="mt-3 flex flex-wrap justify-center gap-2">
              {data.suggestions.map((s) => <button key={s} onClick={() => { setInput(s); go(s, ""); }} className="rounded-full border border-line px-3 py-1 text-sm">{s}</button>)}
            </div>
            <Link href={`/ask?q=${encodeURIComponent(q)}`} className="btn btn-primary mt-4">Ask JanSaathi</Link>
          </Empty>
        )}
        {data && data.results.length > 0 && (
          <>
            <p className="mb-3 text-sm text-muted" role="status">{data.results.length} results for “{q}”</p>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{data.results.map((r) => <ResultCard key={r.kind + r.slug} c={r} />)}</div>
          </>
        )}
      </div>
    </div>
  );
}

export default function SearchPage() {
  return <Suspense fallback={<SkeletonCards />}><SearchInner /></Suspense>;
}
