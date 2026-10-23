"use client";
import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AlertTriangle, ArrowLeft, Check, CircleHelp, Download, ExternalLink, Lock, Printer, X } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useApp } from "@/lib/providers";
import { useFetch } from "@/lib/useFetch";
import { ErrorBox, Loading, Notice, VerificationBadge } from "@/components/ui";
import type { Meta, VStatus } from "@/lib/types";

type Q = { field: string; q: string; q_hi: string; type: "state" | "number" | "choice" | "bool"; options?: string[]; why: string; sensitive: boolean; min?: number; max?: number };
type Item = { field: string; label: string };
type Result = { slug: string; name: string; name_hi: string | null; summary: string; label: string; label_text: string; satisfied: Item[]; missing: Item[]; failed: Item[]; verification_status: VStatus; info_url: string | null; apply_url: string | null };
type Answers = Record<string, string | number | boolean>;

const OPT: Record<string, string> = {
  student: "Student", farmer: "Farmer", unorganised_worker: "Unorganised / daily-wage worker", salaried: "Salaried employee", self_employed: "Self-employed / small business",
  street_vendor: "Street vendor", artisan: "Artisan / craftsperson", unemployed: "Looking for work", homemaker: "Homemaker", retired: "Retired",
  rural: "Rural", urban: "Urban", female: "Female", male: "Male", other: "Other",
  general: "General", obc: "OBC", sc: "SC (Scheduled Caste)", st: "ST (Scheduled Tribe)",
  school: "School", undergraduate_regular: "Undergraduate (regular)", postgraduate_regular: "Postgraduate (regular)", diploma: "Diploma", distance: "Distance / correspondence",
};
const LABEL_STYLE: Record<string, string> = {
  potential_match: "bg-leaf-50 text-leaf-dark ring-leaf/30", rules_need_verification: "bg-navy-100 text-navy-800 ring-navy-700/20",
  more_info: "bg-ivory-dark text-ink ring-line", period_may_have_closed: "bg-saffron-50 text-saffron-dark ring-saffron/30", appears_ineligible: "bg-red-50 text-red-800 ring-red-200",
};
// Income asked as a bracket; we send the bracket's upper limit so "income ≤ ₹X" rules work.
const INCOME_BRACKETS: { label: string; label_hi: string; value: number }[] = [
  { label: "Up to ₹1 lakh a year", label_hi: "₹1 लाख/वर्ष तक", value: 100000 },
  { label: "₹1 – 2.5 lakh", label_hi: "₹1 – 2.5 लाख", value: 250000 },
  { label: "₹2.5 – 4.5 lakh", label_hi: "₹2.5 – 4.5 लाख", value: 450000 },
  { label: "₹4.5 – 8 lakh", label_hi: "₹4.5 – 8 लाख", value: 800000 },
  { label: "₹8 – 18 lakh", label_hi: "₹8 – 18 लाख", value: 1800000 },
  { label: "More than ₹18 lakh", label_hi: "₹18 लाख से अधिक", value: 99999999 },
];
const STORE = "js_elig_v1"; // sessionStorage only — cleared when the tab closes

function Wizard() {
  const { lang } = useApp();
  const sp = useSearchParams();
  const { data: meta } = useFetch<Meta>("/meta");
  const [step, setStep] = useState<1 | 2 | 3>(sp.get("categories") ? 2 : 1);
  const [interests, setInterests] = useState<string[]>((sp.get("categories") || "").split(",").filter(Boolean));
  const [answers, setAnswers] = useState<Answers>({});
  const [questions, setQuestions] = useState<Q[] | null>(null);
  const [results, setResults] = useState<Result[] | null>(null);
  const [note, setNote] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [fieldErr, setFieldErr] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [showIneligible, setShowIneligible] = useState(false);

  useEffect(() => {
    try { const s = JSON.parse(sessionStorage.getItem(STORE) || "{}"); if (s.answers) setAnswers(s.answers); if (s.interests && !sp.get("categories")) setInterests(s.interests); } catch { /* storage unavailable */ }
  }, [sp]);
  useEffect(() => { try { sessionStorage.setItem(STORE, JSON.stringify({ answers, interests })); } catch { /* ignore */ } }, [answers, interests]);

  useEffect(() => {
    if (step !== 2) return;
    setQuestions(null);
    api<{ questions: Q[] }>(`/eligibility/questions?categories=${interests.join(",")}`).then((r) => setQuestions(r.questions)).catch((e) => setErr(e.message));
  }, [step, interests]);

  const setA = (f: string, v: string | number | boolean | undefined) => setAnswers((a) => { const n = { ...a }; if (v === undefined || v === "") delete n[f]; else n[f] = v; return n; });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const fe: Record<string, string> = {};
    for (const q of questions || []) {
      const v = answers[q.field];
      if (q.type === "number" && v !== undefined && (Number.isNaN(Number(v)) || Number(v) < (q.min ?? 0) || Number(v) > (q.max ?? 1e12))) fe[q.field] = `Enter a number between ${q.min} and ${q.max}.`;
    }
    setFieldErr(fe);
    if (Object.keys(fe).length) { document.getElementById(`q-${Object.keys(fe)[0]}`)?.focus(); return; }
    setBusy(true); setErr(null);
    try {
      const body = { interests, answers: Object.fromEntries(Object.entries(answers).filter(([k]) => (questions || []).some((q) => q.field === k))) };
      const r = await api<{ results: Result[]; note: string }>("/eligibility/match", { method: "POST", json: body });
      setResults(r.results); setNote(r.note); setStep(3);
      window.scrollTo({ top: 0 });
    } catch (e) {
      if (e instanceof ApiError && e.fieldErrors.length) setErr(e.fieldErrors.map((f) => f.message).join(" "));
      else setErr(e instanceof Error ? e.message : "Could not check eligibility.");
    } finally { setBusy(false); }
  }

  function exportResults() {
    const blob = new Blob([JSON.stringify({ generated: new Date().toISOString(), disclaimer: note, interests, answers, results }, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = "jansaathi-eligibility.json"; a.click();
    URL.revokeObjectURL(a.href);
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <h1 className="font-display text-4xl text-navy-900">Find schemes that may apply to you</h1>
      <p className="mt-2 text-muted">No account needed. Your answers stay in this browser tab and are not stored on our servers.</p>
      <ol className="mt-5 flex gap-2 text-sm" aria-label="Progress">
        {["What you need", "Your situation", "Results"].map((l, i) => (
          <li key={l} aria-current={step === i + 1 ? "step" : undefined} className={`flex-1 rounded-full px-3 py-1.5 text-center font-semibold ${step === i + 1 ? "bg-navy-900 text-white" : step > i + 1 ? "bg-leaf-50 text-leaf-dark" : "bg-ivory-dark text-muted"}`}>{i + 1}. {l}</li>
        ))}
      </ol>
      {err && <div className="mt-4"><ErrorBox message={err} /></div>}

      {step === 1 && (
        <section className="card mt-6 p-6" aria-labelledby="s1">
          <h2 id="s1" className="font-display text-2xl text-navy-900">What kind of help are you looking for?</h2>
          <p className="text-sm text-muted">Choose one or more, or skip to see everything.</p>
          {!meta ? <Loading /> : (
            <fieldset className="mt-4 grid gap-2 sm:grid-cols-2">
              <legend className="sr-only">Categories</legend>
              {meta.categories.filter((c) => c.count).map((c) => (
                <label key={c.id} className={`flex cursor-pointer items-center gap-3 rounded-xl border p-3 ${interests.includes(c.id) ? "border-navy-700 bg-navy-100" : "border-line bg-white"}`}>
                  <input type="checkbox" className="h-5 w-5 accent-[#0b1f3a]" checked={interests.includes(c.id)} onChange={(e) => setInterests((x) => e.target.checked ? [...x, c.id] : x.filter((y) => y !== c.id))} />
                  <span className="font-semibold">{lang === "hi" ? c.hi : c.en}</span><span className="ml-auto text-xs text-muted">{c.count}</span>
                </label>
              ))}
            </fieldset>
          )}
          <div className="mt-5 flex gap-2"><button className="btn btn-primary" onClick={() => setStep(2)}>Continue</button><button className="btn btn-ghost" onClick={() => { setInterests([]); setStep(2); }}>Skip — show all</button></div>
        </section>
      )}

      {step === 2 && (
        <form onSubmit={submit} className="card mt-6 grid gap-5 p-6" noValidate aria-labelledby="s2">
          <h2 id="s2" className="font-display text-2xl text-navy-900">Tell us about your situation</h2>
          <Notice>We only ask questions used by the schemes you selected. Every question is optional — unanswered ones show up as “more information required”. We never ask for Aadhaar, caste, religion, bank details or documents.</Notice>
          {!questions && <Loading />}
          {questions?.map((q) => {
            const v = answers[q.field];
            const id = `q-${q.field}`;
            return (
              <div key={q.field}>
                <label className="label" htmlFor={id}>{lang === "hi" ? q.q_hi : q.q} {q.sensitive && <span className="ml-1 inline-flex items-center gap-1 rounded bg-ivory-dark px-1.5 py-0.5 text-xs font-medium text-muted"><Lock size={11} aria-hidden />optional · private</span>}</label>
                <p id={`${id}-why`} className="mb-1.5 flex items-start gap-1 text-xs text-muted"><CircleHelp size={13} className="mt-0.5 shrink-0" aria-hidden />Why we ask: {q.why}</p>
                {q.type === "state" && (
                  <select id={id} aria-describedby={`${id}-why`} className="input" value={(v as string) || ""} onChange={(e) => setA(q.field, e.target.value)}>
                    <option value="">Select state / UT</option>{meta?.states.map((s) => <option key={s}>{s}</option>)}
                  </select>
                )}
                {q.field === "annual_income" && (
                  <select id={id} aria-describedby={`${id}-why`} className="input" value={v === undefined ? "" : String(v)} onChange={(e) => setA(q.field, e.target.value === "" ? undefined : Number(e.target.value))}>
                    <option value="">Prefer not to say</option>
                    {INCOME_BRACKETS.map((b) => <option key={b.value} value={b.value}>{lang === "hi" ? b.label_hi : b.label}</option>)}
                  </select>
                )}
                {q.type === "number" && q.field !== "annual_income" && (
                  <input id={id} type="number" inputMode="numeric" min={q.min} max={q.max} aria-describedby={`${id}-why${fieldErr[q.field] ? ` ${id}-err` : ""}`} aria-invalid={!!fieldErr[q.field]}
                    className="input" value={v === undefined ? "" : String(v)} onChange={(e) => setA(q.field, e.target.value === "" ? undefined : Number(e.target.value))} />
                )}
                {q.type === "choice" && (
                  <select id={id} aria-describedby={`${id}-why`} className="input" value={(v as string) || ""} onChange={(e) => setA(q.field, e.target.value)}>
                    <option value="">{q.sensitive ? "Prefer not to say" : "Select"}</option>{q.options?.map((o) => <option key={o} value={o}>{OPT[o] || o}</option>)}
                  </select>
                )}
                {q.type === "bool" && (
                  <div role="radiogroup" aria-labelledby={id} id={id} tabIndex={-1} className="flex flex-wrap gap-2">
                    {[["Yes", true], ["No", false], [q.sensitive ? "Prefer not to say" : "Not sure", undefined]].map(([l, val]) => (
                      <label key={String(l)} className={`cursor-pointer rounded-xl border px-4 py-2 font-semibold ${v === val ? "border-navy-700 bg-navy-100" : "border-line bg-white"}`}>
                        <input type="radio" className="sr-only" name={q.field} checked={v === val} onChange={() => setA(q.field, val as boolean | undefined)} />{String(l)}
                      </label>
                    ))}
                  </div>
                )}
                {fieldErr[q.field] && <p id={`${id}-err`} className="mt-1 text-sm text-red-700">{fieldErr[q.field]}</p>}
              </div>
            );
          })}
          <div className="flex flex-wrap gap-2">
            <button type="button" className="btn btn-ghost" onClick={() => setStep(1)}><ArrowLeft size={16} aria-hidden />Back</button>
            <button className="btn btn-saffron" disabled={busy || !questions}>{busy ? "Checking…" : "See what may apply"}</button>
            <button type="button" className="btn btn-ghost ml-auto" onClick={() => { setAnswers({}); try { sessionStorage.removeItem(STORE); } catch { /* ignore */ } }}>Clear my answers</button>
          </div>
        </form>
      )}

      {step === 3 && results && (
        <section className="mt-6" aria-labelledby="s3">
          <h2 id="s3" className="sr-only">Results</h2>
          <Notice tone="warn">{note}</Notice>
          <div className="no-print mt-4 flex flex-wrap gap-2">
            <button className="btn btn-ghost" onClick={() => setStep(2)}><ArrowLeft size={16} aria-hidden />Change my answers</button>
            <button className="btn btn-ghost" onClick={() => window.print()}><Printer size={16} aria-hidden />Print</button>
            <button className="btn btn-ghost" onClick={exportResults}><Download size={16} aria-hidden />Download results</button>
          </div>
          <ul className="mt-5 grid gap-4">
            {results.filter((r) => showIneligible || r.label !== "appears_ineligible").map((r) => (
              <li key={r.slug} className="card p-5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold ring-1 ${LABEL_STYLE[r.label]}`}>{r.label_text}</span>
                  <VerificationBadge status={r.verification_status} />
                </div>
                <h3 className="mt-2 font-display text-xl text-navy-900"><Link href={`/schemes/${r.slug}`} className="hover:underline">{lang === "hi" && r.name_hi ? r.name_hi : r.name}</Link></h3>
                <p className="text-sm text-muted">{r.summary}</p>
                <div className="mt-3 grid gap-3 text-sm md:grid-cols-3">
                  <div><p className="font-semibold text-leaf-dark">Conditions you appear to meet</p><ul className="mt-1 space-y-1">{r.satisfied.map((x, i) => <li key={i} className="flex gap-1.5"><Check size={15} className="mt-0.5 shrink-0 text-leaf" aria-hidden />{x.label}</li>)}{!r.satisfied.length && <li className="text-muted">—</li>}</ul></div>
                  <div><p className="font-semibold text-navy-800">Needs more information</p><ul className="mt-1 space-y-1">{r.missing.map((x, i) => <li key={i} className="flex gap-1.5"><CircleHelp size={15} className="mt-0.5 shrink-0 text-navy-700" aria-hidden />{x.label}</li>)}{!r.missing.length && <li className="text-muted">—</li>}</ul></div>
                  <div><p className="font-semibold text-red-800">Possible disqualifiers</p><ul className="mt-1 space-y-1">{r.failed.map((x, i) => <li key={i} className="flex gap-1.5"><X size={15} className="mt-0.5 shrink-0 text-red-700" aria-hidden />{x.label}</li>)}{!r.failed.length && <li className="text-muted">—</li>}</ul></div>
                </div>
                {r.verification_status === "needs_verification" && <p className="mt-3 flex items-center gap-1.5 text-sm text-saffron-dark"><AlertTriangle size={15} aria-hidden />Eligibility rules for this scheme have not been fully verified.</p>}
                <div className="mt-3 flex flex-wrap gap-3 text-sm font-semibold">
                  <Link href={`/schemes/${r.slug}`} className="text-navy-700 hover:underline">Details, documents & steps →</Link>
                  {(r.apply_url || r.info_url) && <a href={(r.apply_url || r.info_url)!} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-navy-700 hover:underline">Official site <ExternalLink size={13} aria-hidden /></a>}
                </div>
              </li>
            ))}
          </ul>
          {results.some((r) => r.label === "appears_ineligible") && (
            <button className="btn btn-ghost mt-4" onClick={() => setShowIneligible(!showIneligible)} aria-expanded={showIneligible}>
              {showIneligible ? "Hide" : "Show"} schemes that appear not to apply ({results.filter((r) => r.label === "appears_ineligible").length})
            </button>
          )}
        </section>
      )}
    </div>
  );
}

export default function EligibilityPage() {
  return <Suspense fallback={<Loading />}><Wizard /></Suspense>;
}
