"use client";
import Link from "next/link";
import { AlertTriangle, CheckCircle2, ExternalLink, Info, Loader2, RefreshCw, SearchX, ShieldCheck } from "lucide-react";
import { useApp } from "@/lib/providers";
import { hrefFor, type Card, type Freshness, type Source, type VStatus } from "@/lib/types";

export function VerificationBadge({ status, freshness }: { status: VStatus; freshness?: Freshness["state"] }) {
  const { t } = useApp();
  if (freshness === "stale")
    return <span className="inline-flex items-center gap-1 rounded-full bg-saffron-50 px-2.5 py-0.5 text-xs font-semibold text-saffron-dark ring-1 ring-saffron/40"><AlertTriangle size={13} aria-hidden />{t("stale")}</span>;
  if (status === "verified")
    return <span className="inline-flex items-center gap-1 rounded-full bg-leaf-50 px-2.5 py-0.5 text-xs font-semibold text-leaf-dark ring-1 ring-leaf/30"><ShieldCheck size={13} aria-hidden />{t("verified")}</span>;
  if (status === "reviewed")
    return <span className="inline-flex items-center gap-1 rounded-full bg-navy-100 px-2.5 py-0.5 text-xs font-semibold text-navy-800 ring-1 ring-navy-700/20"><CheckCircle2 size={13} aria-hidden />{t("reviewed")}</span>;
  return <span className="inline-flex items-center gap-1 rounded-full bg-saffron-50 px-2.5 py-0.5 text-xs font-semibold text-saffron-dark ring-1 ring-saffron/40"><AlertTriangle size={13} aria-hidden />{t("needs_verification")}</span>;
}

export function FreshnessNotice({ f, status, note }: { f: Freshness; status: VStatus; note?: string | null }) {
  const warn = f.state !== "fresh";
  const tone = warn ? "bg-saffron-50 text-saffron-dark ring-1 ring-saffron/40" : status === "verified" ? "bg-leaf-50 text-leaf-dark ring-1 ring-leaf/25" : "bg-navy-100 text-navy-800 ring-1 ring-navy-700/20";
  return (
    <div role={warn ? "alert" : "status"} className={`flex gap-3 rounded-xl p-4 text-sm ${tone}`}>
      {warn ? <AlertTriangle className="mt-0.5 shrink-0" size={18} aria-hidden /> : <ShieldCheck className="mt-0.5 shrink-0" size={18} aria-hidden />}
      <div>
        <p className="font-semibold">
          {status === "verified" ? "Verified against an official source" : status === "reviewed" ? "Reviewed — re-confirm on the official site" : "Not yet verified"}
        </p>
        <p>{f.message}</p>
        {note && <p className="mt-1 opacity-90">{note}</p>}
      </div>
    </div>
  );
}

export function Loading({ label }: { label?: string }) {
  const { t } = useApp();
  return <div role="status" className="flex items-center gap-2 py-10 justify-center text-muted"><Loader2 className="animate-spin" size={20} aria-hidden />{label || t("loading")}</div>;
}

export function SkeletonCards({ n = 6 }: { n?: number }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-hidden>
      {Array.from({ length: n }).map((_, i) => <div key={i} className="card h-40 animate-pulse bg-white/60" />)}
    </div>
  );
}

export function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const { t } = useApp();
  return (
    <div role="alert" className="card flex flex-col items-start gap-3 border-red-200 bg-red-50 p-5 text-red-900">
      <p className="flex items-center gap-2 font-semibold"><AlertTriangle size={18} aria-hidden />{message}</p>
      {onRetry && <button className="btn btn-ghost bg-white" onClick={onRetry}><RefreshCw size={16} aria-hidden />{t("retry")}</button>}
    </div>
  );
}

export function Empty({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <div className="card flex flex-col items-center gap-2 p-10 text-center">
      <SearchX size={28} className="text-muted" aria-hidden />
      <p className="font-display text-xl text-navy-900">{title}</p>
      <div className="text-muted">{children}</div>
    </div>
  );
}

export function Notice({ children, tone = "info" }: { children: React.ReactNode; tone?: "info" | "warn" }) {
  return (
    <div className={`flex gap-2 rounded-xl p-3 text-sm ${tone === "warn" ? "bg-saffron-50 text-saffron-dark ring-1 ring-saffron/30" : "bg-navy-100 text-navy-800"}`}>
      <Info size={16} className="mt-0.5 shrink-0" aria-hidden /><div>{children}</div>
    </div>
  );
}

const KIND_LABEL: Record<string, string> = { scheme: "Scheme", right: "Constitution", guide: "Guide", service: "Service" };

export function ResultCard({ c }: { c: Card }) {
  const { lang } = useApp();
  const title = lang === "hi" && c.title_hi ? c.title_hi : c.title;
  const summary = lang === "hi" && c.summary_hi ? c.summary_hi : c.summary;
  return (
    <Link href={hrefFor(c)} className="card card-hover flex h-full flex-col gap-2 p-5">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="rounded-full bg-ivory-dark px-2 py-0.5 font-semibold uppercase tracking-wide text-muted">
          {c.kind === "right" && c.article ? `Art. ${c.article}` : KIND_LABEL[c.kind]}
        </span>
        {c.level === "state" && c.states && <span className="rounded-full bg-navy-100 px-2 py-0.5 font-semibold text-navy-800">{c.states.join(", ")}</span>}
        <VerificationBadge status={c.verification_status} freshness={c.freshness} />
      </div>
      <h3 className="font-display text-lg leading-snug text-navy-900">{title}</h3>
      <p className="line-clamp-3 text-sm text-muted">{summary}</p>
      {c.why && c.why.length > 0 && <p className="mt-auto pt-1 text-xs text-leaf-dark">Matched: {c.why.join(", ")}</p>}
    </Link>
  );
}

export function SourcesList({ sources, lastVerified }: { sources: Source[]; lastVerified: string | null }) {
  const { t } = useApp();
  return (
    <section aria-labelledby="sources-h" className="card p-5">
      <h2 id="sources-h" className="font-display text-xl text-navy-900">{t("sources")}</h2>
      <ul className="mt-3 space-y-2">
        {sources.map((s) => (
          <li key={s.url} className="text-sm">
            <a href={s.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 font-semibold text-navy-700 underline underline-offset-2">
              {s.title}<ExternalLink size={13} aria-hidden /><span className="sr-only">(opens in new tab)</span>
            </a>
            <span className="text-muted"> — {s.organisation}{s.type === "news_secondary" ? " (secondary source)" : ""}{s.retrieved ? `, retrieved ${s.retrieved}` : ""}</span>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-muted">{t("last_verified")}: {lastVerified || t("not_verified")}</p>
    </section>
  );
}

export function OfficialButton({ href, children, primary = true }: { href: string; children: React.ReactNode; primary?: boolean }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className={`btn ${primary ? "btn-saffron" : "btn-ghost"}`}>
      {children}<ExternalLink size={16} aria-hidden /><span className="sr-only">(official site, opens in new tab)</span>
    </a>
  );
}

export function List({ items, ordered }: { items: string[]; ordered?: boolean }) {
  if (!items?.length) return <p className="text-sm text-muted">Not documented in our records — check the official source.</p>;
  const Tag = ordered ? "ol" : "ul";
  return <Tag className={`${ordered ? "list-decimal" : "list-disc"} space-y-1.5 pl-5`}>{items.map((x, i) => <li key={i}>{x}</li>)}</Tag>;
}

export function Section({ title, children, id }: { title: string; children: React.ReactNode; id?: string }) {
  return (
    <section className="card p-5" aria-labelledby={id}>
      <h2 id={id} className="font-display text-xl text-navy-900">{title}</h2>
      <div className="mt-3 text-[15px]">{children}</div>
    </section>
  );
}
