"use client";
import Link from "next/link";
import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Copy, FilePenLine, Printer, Siren } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useFetch } from "@/lib/useFetch";
import { ErrorBox, Notice, SkeletonCards, VerificationBadge } from "@/components/ui";
import type { Card } from "@/lib/types";

type Errs = Record<string, string>;

function Field({ id, label, err, hint, children }: { id: string; label: string; err?: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className="label">{label}</label>
      {hint && <p id={`${id}-hint`} className="-mt-1 mb-1 text-xs text-muted">{hint}</p>}
      {children}
      {err && <p id={`${id}-err`} className="mt-1 text-sm text-red-700">{err}</p>}
    </div>
  );
}

function DraftResult({ draft, nextSteps }: { draft: string; nextSteps: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="mt-5" aria-live="polite">
      <p className="rounded-xl bg-saffron-50 p-3 text-sm font-semibold text-saffron-dark">This is a draft only. It has not been sent anywhere. {nextSteps}</p>
      <pre className="mt-3 max-h-[28rem] overflow-auto whitespace-pre-wrap rounded-xl border border-line bg-white p-4 font-sans text-sm">{draft}</pre>
      <div className="no-print mt-3 flex gap-2">
        <button className="btn btn-ghost" onClick={async () => { await navigator.clipboard.writeText(draft); setCopied(true); setTimeout(() => setCopied(false), 1500); }}><Copy size={16} aria-hidden />{copied ? "Copied" : "Copy"}</button>
        <button className="btn btn-ghost" onClick={() => window.print()}><Printer size={16} aria-hidden />Print</button>
      </div>
    </div>
  );
}

function ComplaintForm({ topic }: { topic: string }) {
  const [f, setF] = useState({ authority: "", subject: topic, facts: "", relief: "", applicant_name: "", contact: "", reference_numbers: "" });
  const [errs, setErrs] = useState<Errs>({});
  const [res, setRes] = useState<{ draft: string; next_steps: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const up = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setF({ ...f, [k]: e.target.value });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const v: Errs = {};
    if (f.authority.trim().length < 3) v.authority = "Who is this addressed to? (at least 3 characters)";
    if (f.subject.trim().length < 3) v.subject = "Add a short subject.";
    if (f.facts.trim().length < 20) v.facts = "Describe what happened in at least 20 characters — dates, places, what was said or done.";
    if (f.relief.trim().length < 5) v.relief = "What do you want them to do?";
    if (!f.applicant_name.trim()) v.applicant_name = "Enter your name as it should appear.";
    if (f.contact.trim().length < 3) v.contact = "Enter a contact (email or phone).";
    setErrs(v);
    if (Object.keys(v).length) { document.getElementById(`c-${Object.keys(v)[0]}`)?.focus(); return; }
    setBusy(true); setErr(null);
    try { setRes(await api("/drafts/complaint", { method: "POST", json: f })); }
    catch (e) { setErr(e instanceof ApiError ? e.message : "Could not prepare the draft."); }
    finally { setBusy(false); }
  }
  const aria = (k: string) => ({ "aria-invalid": !!errs[k], "aria-describedby": errs[k] ? `c-${k}-err` : undefined });

  return (
    <form onSubmit={submit} noValidate className="grid gap-4">
      <Field id="c-authority" label="Addressed to (officer / department)" err={errs.authority}><input id="c-authority" className="input" value={f.authority} onChange={up("authority")} {...aria("authority")} placeholder="e.g. The District Collector, Vellore" /></Field>
      <Field id="c-subject" label="Subject" err={errs.subject}><input id="c-subject" className="input" value={f.subject} onChange={up("subject")} {...aria("subject")} /></Field>
      <Field id="c-facts" label="What happened (facts only)" err={errs.facts} hint="Stick to facts: dates, application numbers, who you spoke to. Avoid accusations you cannot support."><textarea id="c-facts" className="input min-h-32" value={f.facts} onChange={up("facts")} {...aria("facts")} /></Field>
      <Field id="c-relief" label="What you are asking for" err={errs.relief}><textarea id="c-relief" className="input min-h-20" value={f.relief} onChange={up("relief")} {...aria("relief")} placeholder="e.g. Process my application and inform me of its status" /></Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field id="c-applicant_name" label="Your name" err={errs.applicant_name}><input id="c-applicant_name" className="input" value={f.applicant_name} onChange={up("applicant_name")} {...aria("applicant_name")} /></Field>
        <Field id="c-contact" label="Contact for reply" err={errs.contact}><input id="c-contact" className="input" value={f.contact} onChange={up("contact")} {...aria("contact")} /></Field>
      </div>
      <Field id="c-ref" label="Application / reference number (optional)"><input id="c-ref" className="input" value={f.reference_numbers} onChange={up("reference_numbers")} /></Field>
      <p className="text-xs text-muted">We do not store what you type here. Never include Aadhaar, bank or OTP details.</p>
      {err && <ErrorBox message={err} />}
      <button className="btn btn-primary justify-self-start" disabled={busy}><FilePenLine size={16} aria-hidden />{busy ? "Preparing…" : "Prepare draft"}</button>
      {res && <DraftResult draft={res.draft} nextSteps={res.next_steps} />}
    </form>
  );
}

function RTIForm() {
  const [f, setF] = useState({ public_authority: "", info: "", applicant_name: "", address: "", bpl: false });
  const [errs, setErrs] = useState<Errs>({});
  const [res, setRes] = useState<{ draft: string; next_steps: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const v: Errs = {};
    if (f.public_authority.trim().length < 3) v.public_authority = "Name the public authority (department / office).";
    const items = f.info.split("\n").map((x) => x.trim()).filter(Boolean);
    if (!items.length) v.info = "Write at least one specific question, one per line.";
    if (items.length > 10) v.info = "Please limit to 10 questions.";
    if (!f.applicant_name.trim()) v.applicant_name = "Enter your name.";
    if (f.address.trim().length < 5) v.address = "Enter an address for correspondence.";
    setErrs(v);
    if (Object.keys(v).length) { document.getElementById(`r-${Object.keys(v)[0]}`)?.focus(); return; }
    setBusy(true); setErr(null);
    try { setRes(await api("/drafts/rti", { method: "POST", json: { public_authority: f.public_authority, information_sought: items, applicant_name: f.applicant_name, address: f.address, bpl: f.bpl } })); }
    catch (e) { setErr(e instanceof ApiError ? e.message : "Could not prepare the draft."); }
    finally { setBusy(false); }
  }
  const aria = (k: string) => ({ "aria-invalid": !!errs[k], "aria-describedby": errs[k] ? `r-${k}-err` : undefined });

  return (
    <form onSubmit={submit} noValidate className="grid gap-4">
      <Field id="r-public_authority" label="Public authority" err={errs.public_authority}><input id="r-public_authority" className="input" value={f.public_authority} onChange={(e) => setF({ ...f, public_authority: e.target.value })} {...aria("public_authority")} placeholder="e.g. Office of the Tahsildar, Katpadi" /></Field>
      <Field id="r-info" label="Information you want (one question per line)" err={errs.info} hint="Ask for records, e.g. 'Certified copy of file notings on my application no. …'."><textarea id="r-info" className="input min-h-28" value={f.info} onChange={(e) => setF({ ...f, info: e.target.value })} {...aria("info")} /></Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field id="r-applicant_name" label="Your name" err={errs.applicant_name}><input id="r-applicant_name" className="input" value={f.applicant_name} onChange={(e) => setF({ ...f, applicant_name: e.target.value })} {...aria("applicant_name")} /></Field>
        <Field id="r-address" label="Address for reply" err={errs.address}><input id="r-address" className="input" value={f.address} onChange={(e) => setF({ ...f, address: e.target.value })} {...aria("address")} /></Field>
      </div>
      <label className="flex items-center gap-2"><input type="checkbox" className="h-5 w-5" checked={f.bpl} onChange={(e) => setF({ ...f, bpl: e.target.checked })} />I am a BPL card holder (fee exemption)</label>
      {err && <ErrorBox message={err} />}
      <button className="btn btn-primary justify-self-start" disabled={busy}><FilePenLine size={16} aria-hidden />{busy ? "Preparing…" : "Prepare RTI draft"}</button>
      {res && <DraftResult draft={res.draft} nextSteps={res.next_steps} />}
    </form>
  );
}

function ComplaintsInner() {
  const sp = useSearchParams();
  const [tab, setTab] = useState<"complaint" | "rti">(sp.get("draft") === "rti" ? "rti" : "complaint");
  const { data, loading, error, reload } = useFetch<{ items: Card[] }>("/guides?kind=complaint");

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="font-display text-4xl text-navy-900">Complaints, grievances & legal aid</h1>
      <p className="mt-2 max-w-3xl text-muted">Find the right official channel, prepare a clear factual letter, and know how to escalate.</p>
      <p role="note" className="mt-4 flex items-center gap-2 rounded-xl bg-red-50 p-4 font-semibold text-red-900"><Siren size={20} aria-hidden />Emergency: call 112. Online money fraud: call 1930 immediately. Free legal aid: 15100.</p>

      <section aria-labelledby="cat" className="mt-8">
        <h2 id="cat" className="font-display text-2xl text-navy-900">What is the problem about?</h2>
        {loading && <SkeletonCards n={6} />}
        {error && <ErrorBox message={error} onRetry={reload} />}
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data?.items.map((g) => (
            <Link key={g.slug} href={`/guides/${g.slug}`} className="card card-hover p-4">
              <p className="font-semibold text-navy-900">{g.title}</p>
              <p className="mt-1 line-clamp-2 text-sm text-muted">{g.summary}</p>
              <div className="mt-2"><VerificationBadge status={g.verification_status} freshness={g.freshness} /></div>
            </Link>
          ))}
          <Link href="/guides/guide-legal-aid" className="card card-hover border-leaf/40 bg-leaf-50 p-4"><p className="font-semibold text-leaf-dark">Need a free lawyer?</p><p className="mt-1 text-sm">Who qualifies for free legal aid and how to apply.</p></Link>
          <Link href="/guides/guide-rti" className="card card-hover p-4"><p className="font-semibold text-navy-900">Get information with RTI</p><p className="mt-1 text-sm text-muted">Ask a public authority for records and reasons.</p></Link>
        </div>
      </section>

      <section aria-labelledby="draft" className="card mt-10 p-6">
        <h2 id="draft" className="font-display text-2xl text-navy-900">Draft a letter</h2>
        <Notice>JanSaathi prepares a draft for you to review. We do not send or file anything — you submit it yourself on the official channel.</Notice>
        <div role="tablist" aria-label="Draft type" className="mt-4 flex gap-2">
          <button role="tab" aria-selected={tab === "complaint"} onClick={() => setTab("complaint")} className={`btn ${tab === "complaint" ? "btn-primary" : "btn-ghost"}`}>Complaint / grievance letter</button>
          <button role="tab" aria-selected={tab === "rti"} onClick={() => setTab("rti")} className={`btn ${tab === "rti" ? "btn-primary" : "btn-ghost"}`}>RTI application</button>
        </div>
        <div className="mt-5" role="tabpanel">{tab === "complaint" ? <ComplaintForm topic={sp.get("topic") || ""} /> : <RTIForm />}</div>
      </section>
    </div>
  );
}

export default function ComplaintsPage() {
  return <Suspense fallback={<SkeletonCards />}><ComplaintsInner /></Suspense>;
}
