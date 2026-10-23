"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Search } from "lucide-react";
import { useApp } from "@/lib/providers";

const EXAMPLES = ["scholarship for college", "old age pension", "Article 21", "income certificate", "free legal aid", "किसान योजना"];

export function HomeSearch() {
  const { t } = useApp();
  const [q, setQ] = useState("");
  const router = useRouter();
  const go = (v: string) => v.trim() && router.push(`/search?q=${encodeURIComponent(v.trim())}`);
  return (
    <div>
      <form role="search" onSubmit={(e) => { e.preventDefault(); go(q); }} className="flex flex-col gap-2 rounded-2xl bg-white p-2 shadow-xl shadow-navy-950/30 sm:flex-row">
        <label htmlFor="home-q" className="sr-only">{t("search_placeholder")}</label>
        <div className="flex flex-1 items-center gap-2 px-3">
          <Search size={20} className="text-muted" aria-hidden />
          <input id="home-q" value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("search_placeholder")} className="h-12 w-full bg-transparent text-base text-ink outline-none placeholder:text-muted" autoComplete="off" />
        </div>
        <button className="btn btn-saffron px-6">{t("search")}</button>
      </form>
      <div className="mt-3 flex flex-wrap gap-2">
        {EXAMPLES.map((e) => (
          <button key={e} onClick={() => go(e)} className="rounded-full border border-white/25 px-3 py-1.5 text-sm text-white/90 hover:bg-white/10">{e}</button>
        ))}
      </div>
    </div>
  );
}
