"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { CheckCircle2, Circle, ExternalLink, FileText, Printer } from "lucide-react";
import { useApp } from "@/lib/providers";

export type ChecklistItem = {
  text: string;
  doc: { key: string; name: string; name_hi: string; how: string; how_hi: string; links: { label: string; href: string }[] } | null;
};

/** Interactive per-scheme checklist: tick what you have; ticks are kept only in this browser. */
export function DocumentChecklist({ slug, items }: { slug: string; items: ChecklistItem[] }) {
  const { lang } = useApp();
  const key = `js_docs_${slug}`;
  const [have, setHave] = useState<Record<number, boolean>>({});

  useEffect(() => {
    try { setHave(JSON.parse(localStorage.getItem(key) || "{}")); } catch { /* storage unavailable */ }
  }, [key]);

  const toggle = (i: number) => setHave((h) => {
    const n = { ...h, [i]: !h[i] };
    try { localStorage.setItem(key, JSON.stringify(n)); } catch { /* ignore */ }
    return n;
  });

  if (!items.length) return <p className="text-sm text-muted">Not documented in our records — check the official source.</p>;
  const done = items.filter((_, i) => have[i]).length;

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <div className="h-2 flex-1 overflow-hidden rounded-full bg-ivory-dark" aria-hidden>
          <div className="h-full rounded-full bg-leaf transition-all" style={{ width: `${(done / items.length) * 100}%` }} />
        </div>
        <span className="text-sm font-semibold text-navy-900" role="status">{done} of {items.length} ready</span>
        <button onClick={() => window.print()} className="no-print inline-flex items-center gap-1 rounded-lg px-2 py-1 text-sm font-semibold text-navy-700 hover:bg-ivory-dark"><Printer size={14} aria-hidden />Print checklist</button>
      </div>
      <ul className="divide-y divide-line rounded-xl border border-line">
        {items.map((it, i) => (
          <li key={i} className={`flex gap-3 p-3 ${have[i] ? "bg-leaf-50/60" : ""}`}>
            <button onClick={() => toggle(i)} aria-pressed={!!have[i]} aria-label={`${have[i] ? "Unmark" : "Mark"} "${it.text}" as ready`}
              className="mt-0.5 shrink-0 rounded-full text-leaf-dark">
              {have[i] ? <CheckCircle2 size={22} aria-hidden /> : <Circle size={22} className="text-muted" aria-hidden />}
            </button>
            <div className="min-w-0 flex-1">
              <p className={`font-semibold ${have[i] ? "text-leaf-dark" : "text-navy-900"}`}>{it.text}</p>
              {it.doc ? (
                <div className="mt-1 text-sm">
                  <p className="text-muted"><span className="font-semibold text-ink">Where to get it: </span>{lang === "hi" ? it.doc.how_hi : it.doc.how}</p>
                  {it.doc.links.length > 0 && (
                    <div className="mt-1.5 flex flex-wrap gap-2">
                      {it.doc.links.map((l) => (
                        <Link key={l.href} href={l.href} className="inline-flex items-center gap-1 rounded-full bg-navy-100 px-2.5 py-0.5 text-xs font-semibold text-navy-800 hover:bg-navy-900 hover:text-white">
                          {l.href.startsWith("http") ? <ExternalLink size={11} aria-hidden /> : <FileText size={11} aria-hidden />}{l.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <p className="mt-1 text-sm text-muted">Ask the office or bank handling your application, or check the official scheme page.</p>
              )}
            </div>
          </li>
        ))}
      </ul>
      <p className="mt-2 text-xs text-muted">Your ticks are saved only on this device. JanSaathi never asks you to upload documents — never share Aadhaar numbers, bank details or OTPs.</p>
    </div>
  );
}
