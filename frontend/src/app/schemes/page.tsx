"use client";
import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ClipboardCheck, SlidersHorizontal } from "lucide-react";
import { Empty, ErrorBox, Notice, ResultCard, SkeletonCards } from "@/components/ui";
import { useApp } from "@/lib/providers";
import { useFetch } from "@/lib/useFetch";
import type { Card, Meta, Paged } from "@/lib/types";

function SchemesInner() {
  const { t, lang } = useApp();
  const sp = useSearchParams();
  const router = useRouter();
  const { data: meta } = useFetch<Meta>("/meta");
  const params = new URLSearchParams(sp.toString());
  if (!params.get("size")) params.set("size", "12");
  const { data, error, loading, reload } = useFetch<Paged<Card>>(`/schemes?${params.toString()}`);
  const [q, setQ] = useState(sp.get("q") || "");
  useEffect(() => setQ(sp.get("q") || ""), [sp]);

  const set = (k: string, v: string) => {
    const p = new URLSearchParams(sp.toString());
    if (v) p.set(k, v); else p.delete(k);
    if (k !== "page") p.delete("page");
    router.push(`/schemes?${p.toString()}`);
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-4xl text-navy-900">{t("nav_schemes")}</h1>
          <p className="mt-1 text-muted">Central and state programmes with eligibility, documents and official links.</p>
        </div>
        <Link href="/eligibility" className="btn btn-saffron"><ClipboardCheck size={18} aria-hidden />{t("cta_check")}</Link>
      </div>
      <div className="mt-4"><Notice tone="warn">{meta?.coverage_note || t("coverage_warning")} Records marked “Needs verification” must be confirmed on the official portal.</Notice></div>

      <form onSubmit={(e) => { e.preventDefault(); set("q", q.trim()); }} className="card mt-6 grid gap-3 p-4 md:grid-cols-[2fr_1fr_1fr_1fr_1fr]" aria-label="Filter schemes">
        <div>
          <label className="label" htmlFor="sq">Keyword</label>
          <input id="sq" className="input" value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. pension, छात्रवृत्ति, loan" />
        </div>
        <div>
          <label className="label" htmlFor="cat">Category</label>
          <select id="cat" className="input" value={sp.get("category") || ""} onChange={(e) => set("category", e.target.value)}>
            <option value="">All categories</option>
            {meta?.categories.filter((c) => c.count).map((c) => <option key={c.id} value={c.id}>{lang === "hi" ? c.hi : c.en} ({c.count})</option>)}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="st">State / UT</label>
          <select id="st" className="input" value={sp.get("state") || ""} onChange={(e) => set("state", e.target.value)}>
            <option value="">All (central + state)</option>
            {meta?.states.map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="lv">Government level</label>
          <select id="lv" className="input" value={sp.get("level") || ""} onChange={(e) => set("level", e.target.value)}>
            <option value="">Any</option><option value="central">Central</option><option value="state">State</option>
          </select>
        </div>
        <div>
          <label className="label" htmlFor="vf">Verification</label>
          <select id="vf" className="input" value={sp.get("verification") || ""} onChange={(e) => set("verification", e.target.value)}>
            <option value="">Any</option><option value="verified">Verified</option><option value="reviewed">Reviewed</option><option value="needs_verification">Needs verification</option>
          </select>
        </div>
        <div className="flex flex-wrap gap-2 md:col-span-5">
          <button className="btn btn-primary"><SlidersHorizontal size={16} aria-hidden />Apply</button>
          {sp.toString() && <button type="button" className="btn btn-ghost" onClick={() => router.push("/schemes")}>Clear filters</button>}
          <label className="ml-auto flex items-center gap-2 text-sm"><span className="font-semibold">Sort</span>
            <select className="input !min-h-10 w-auto" value={sp.get("sort") || "relevance"} onChange={(e) => set("sort", e.target.value)}>
              <option value="relevance">Verification first</option><option value="name">Name (A–Z)</option><option value="updated">Recently updated</option>
            </select>
          </label>
        </div>
      </form>

      <div className="mt-6">
        {loading && <SkeletonCards />}
        {error && <ErrorBox message={error} onRetry={reload} />}
        {data && data.items.length === 0 && <Empty title={t("no_results")}><p>Try removing a filter, or <Link className="underline" href="/ask">ask JanSaathi</Link>.</p></Empty>}
        {data && data.items.length > 0 && (
          <>
            <p className="mb-3 text-sm text-muted" role="status">{data.total} schemes</p>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{data.items.map((s) => <ResultCard key={s.slug} c={s} />)}</div>
            {data.pages > 1 && (
              <nav aria-label="Pagination" className="mt-6 flex items-center justify-center gap-2">
                <button className="btn btn-ghost" disabled={data.page <= 1} onClick={() => set("page", String(data.page - 1))}>Previous</button>
                <span className="text-sm">Page {data.page} of {data.pages}</span>
                <button className="btn btn-ghost" disabled={data.page >= data.pages} onClick={() => set("page", String(data.page + 1))}>Next</button>
              </nav>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function SchemesPage() {
  return <Suspense fallback={<div className="mx-auto max-w-7xl px-4 py-10"><SkeletonCards /></div>}><SchemesInner /></Suspense>;
}
