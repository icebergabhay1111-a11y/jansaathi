"use client";
import Link from "next/link";
import { useState } from "react";
import { AlarmClock, Bell, BellOff, CalendarPlus, ClipboardCheck, Download, ExternalLink, Trash2 } from "lucide-react";
import { downloadIcs } from "@/lib/ics";
import { api } from "@/lib/api";
import { useApp } from "@/lib/providers";
import { useFetch } from "@/lib/useFetch";
import { Empty, ErrorBox, Loading, Notice, ResultCard } from "@/components/ui";
import type { Card } from "@/lib/types";

type Saved = { id: number; item_type: string; item_slug: string; title: string; my_status: string; status_source: string; notes: string | null; documents: string[]; links: Record<string, string>; closes_on: string | null; available: boolean;
  applied_on: string | null; reference_no: string | null; reminders: { id: number; title: string; due_date: string; enabled: boolean }[] };
type Rem = { id: number; title: string; due_date: string; enabled: boolean; overdue: boolean; days_left: number; related_slug: string | null };

const STATUS_LABEL: Record<string, string> = { interested: "Interested", preparing_documents: "Preparing documents", applied: "Applied", approved: "Approved", rejected: "Rejected", not_applying: "Not applying" };
const PATH: Record<string, string> = { scheme: "/schemes", service: "/services", right: "/rights", guide: "/guides" };

function Upcoming({ items }: { items: Rem[] }) {
  const soon = items.filter((r) => r.enabled && r.days_left <= 7).sort((a, b) => a.days_left - b.days_left);
  if (!soon.length) return null;
  return (
    <section aria-labelledby="up-h" className="mt-6 rounded-2xl bg-saffron-50 p-4 ring-1 ring-saffron/40">
      <h2 id="up-h" className="flex items-center gap-2 font-semibold text-saffron-dark"><AlarmClock size={18} aria-hidden />Coming up</h2>
      <ul className="mt-2 space-y-1 text-sm">
        {soon.map((r) => (
          <li key={r.id}><strong>{r.title}</strong> — {r.overdue ? <span className="text-red-700">was due {r.due_date}</span> : r.days_left === 0 ? "today" : `in ${r.days_left} day${r.days_left === 1 ? "" : "s"} (${r.due_date})`}</li>
        ))}
      </ul>
    </section>
  );
}

function TrackerFields({ s, statuses, onChange }: { s: Saved; statuses: string[]; onChange: () => void }) {
  const [applied, setApplied] = useState(s.applied_on || "");
  const [ref, setRef] = useState(s.reference_no || "");
  const [remDate, setRemDate] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);
  const today = new Date().toISOString().slice(0, 10);

  async function save(json: Record<string, unknown>, okMsg: string) {
    setErr(null); setOk(null);
    try { await api(`/me/saved/${s.id}`, { method: "PATCH", json }); setOk(okMsg); onChange(); }
    catch (e) { setErr(e instanceof Error ? e.message : "Could not save."); }
  }
  async function addReminder() {
    setErr(null); setOk(null);
    if (!remDate) { setErr("Pick a date for the reminder."); return; }
    try {
      await api("/me/reminders", { method: "POST", json: { title: `Follow up: ${s.title}`.slice(0, 200), due_date: remDate, related_slug: s.item_slug } });
      setRemDate(""); setOk("Reminder added."); onChange();
    } catch (e) { setErr(e instanceof Error ? e.message : "Could not add the reminder."); }
  }

  return (
    <div className="mt-3 grid gap-3 text-sm">
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="grid gap-1"><span className="font-semibold">My status</span>
          <select className="input !min-h-10" value={s.my_status} onChange={(e) => save({ my_status: e.target.value }, "Status updated.")}>
            {statuses.map((x) => <option key={x} value={x}>{STATUS_LABEL[x]}</option>)}
          </select>
        </label>
        <label className="grid gap-1"><span className="font-semibold">Applied on</span>
          <input type="date" max={today} className="input !min-h-10" value={applied} onChange={(e) => setApplied(e.target.value)}
            onBlur={() => applied !== (s.applied_on || "") && save(applied ? { applied_on: applied } : { clear_applied_on: true }, "Application date saved.")} />
        </label>
      </div>
      <label className="grid gap-1"><span className="font-semibold">Application / acknowledgement number <span className="font-normal text-muted">(optional)</span></span>
        <input className="input !min-h-10" maxLength={80} value={ref} onChange={(e) => setRef(e.target.value)} placeholder="e.g. the number on your receipt"
          onBlur={() => ref !== (s.reference_no || "") && save({ reference_no: ref }, "Reference saved.")} />
      </label>
      <div className="rounded-xl bg-ivory p-3">
        <p className="font-semibold">Reminders for this {s.item_type}</p>
        {s.reminders.length > 0 ? (
          <ul className="mt-1 space-y-1">
            {s.reminders.map((r) => (
              <li key={r.id} className="flex items-center gap-2">
                <span className={r.enabled ? "" : "opacity-50"}>{r.due_date}</span>
                <button type="button" onClick={() => downloadIcs(r)} className="inline-flex items-center gap-1 text-xs font-semibold text-navy-700 underline"><CalendarPlus size={12} aria-hidden />Add to calendar</button>
              </li>
            ))}
          </ul>
        ) : <p className="text-muted">None yet — e.g. a date to check your status or the renewal date.</p>}
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <label className="sr-only" htmlFor={`rd-${s.id}`}>Reminder date</label>
          <input id={`rd-${s.id}`} type="date" min={today} className="input !min-h-10 w-auto" value={remDate} onChange={(e) => setRemDate(e.target.value)} />
          <button type="button" onClick={addReminder} className="btn btn-ghost !min-h-10 bg-white">Add reminder</button>
        </div>
      </div>
      {err && <p role="alert" className="text-red-700">{err}</p>}
      {ok && <p role="status" className="text-leaf-dark">{ok}</p>}
      <p className="text-xs text-muted">Status, dates and numbers here are what <strong>you</strong> enter — not synced with any government system.</p>
    </div>
  );
}

function Authed() {
  const saved = useFetch<{ items: Saved[]; statuses: string[] }>("/me/saved");
  const rems = useFetch<{ items: Rem[] }>("/me/reminders");
  const updates = useFetch<{ items: Card[] }>("/updates");
  const { user, logout } = useApp();
  const [title, setTitle] = useState("");
  const [due, setDue] = useState("");
  const [remErr, setRemErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);

  async function remove(id: number) { await api(`/me/saved/${id}`, { method: "DELETE" }); saved.reload(); setMsg("Removed."); }
  async function addRem(e: React.FormEvent) {
    e.preventDefault(); setRemErr(null);
    if (title.trim().length < 2 || !due) { setRemErr("Enter a title and a date."); return; }
    try { await api("/me/reminders", { method: "POST", json: { title, due_date: due } }); setTitle(""); setDue(""); rems.reload(); }
    catch (e) { setRemErr(e instanceof Error ? e.message : "Could not add."); }
  }
  async function exportData() {
    const d = await api("/me/export");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([JSON.stringify(d, null, 2)], { type: "application/json" }));
    a.download = "jansaathi-my-data.json"; a.click(); URL.revokeObjectURL(a.href);
  }
  async function deleteAccount() {
    await api("/auth/account", { method: "DELETE" });
    await logout();
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div><h1 className="font-display text-4xl text-navy-900">My dashboard</h1><p className="text-muted">Signed in as {user?.email}</p></div>
        <Link href="/eligibility" className="btn btn-saffron"><ClipboardCheck size={18} aria-hidden />Find schemes for me</Link>
      </div>
      {msg && <p role="status" className="mt-3 text-sm text-leaf-dark">{msg}</p>}
      <Upcoming items={rems.data?.items || []} />

      <section aria-labelledby="sv" className="mt-8">
        <h2 id="sv" className="font-display text-2xl text-navy-900">Saved schemes & services</h2>
        <Notice>“My status” is what <strong>you</strong> record. It is not connected to any government system — check the official portal for your real application status.</Notice>
        {saved.loading && <Loading />}
        {saved.error && <ErrorBox message={saved.error} onRetry={saved.reload} />}
        {saved.data && saved.data.items.length === 0 && <div className="mt-4"><Empty title="Nothing saved yet"><p>Use “Save” on any scheme or service page.</p></Empty></div>}
        <ul className="mt-4 grid gap-4 md:grid-cols-2">
          {saved.data?.items.map((s) => (
            <li key={s.id} className="card p-5">
              <div className="flex items-start justify-between gap-3">
                <Link href={`${PATH[s.item_type]}/${s.item_slug}`} className="font-display text-lg text-navy-900 hover:underline">{s.title}</Link>
                <button onClick={() => remove(s.id)} aria-label={`Remove ${s.title}`} className="rounded p-2 text-muted hover:bg-ivory-dark"><Trash2 size={16} aria-hidden /></button>
              </div>
              {!s.available && <p className="mt-1 text-sm text-saffron-dark">This record is currently unpublished for review.</p>}
              <TrackerFields s={s} statuses={saved.data!.statuses} onChange={() => { saved.reload(); rems.reload(); }} />
              <div className="mt-3 flex flex-wrap gap-3 text-sm">
                {Object.entries(s.links).map(([k, u]) => <a key={k} href={u} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 font-semibold text-navy-700 underline">{k === "apply_url" ? "Apply (official)" : k === "portal_url" ? "Official portal" : "Official info"}<ExternalLink size={12} aria-hidden /></a>)}
                {s.item_type === "scheme" && <Link href={`/schemes/${s.item_slug}#docs`} className="font-semibold text-navy-700 underline">Document checklist</Link>}
              </div>
              {s.closes_on && <p className="mt-2 text-xs text-muted">Official closing date on record: {s.closes_on}</p>}
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="rm" className="mt-10 grid gap-6 lg:grid-cols-2">
        <div className="card p-5">
          <h2 id="rm" className="font-display text-2xl text-navy-900">My reminders</h2>
          <p className="text-sm text-muted">Reminders you create — not official deadlines. JanSaathi does not send SMS or email; use <strong>Add to calendar</strong> (<CalendarPlus size={13} className="inline" aria-hidden />) to get an alert on your phone a day before.</p>
          <form onSubmit={addRem} className="mt-4 grid gap-2 sm:grid-cols-[1fr_auto_auto]" noValidate>
            <label className="sr-only" htmlFor="rt">Reminder title</label>
            <input id="rt" className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Renew scholarship on NSP" />
            <label className="sr-only" htmlFor="rd">Date</label>
            <input id="rd" type="date" className="input" value={due} onChange={(e) => setDue(e.target.value)} />
            <button className="btn btn-primary">Add</button>
          </form>
          {remErr && <p className="mt-2 text-sm text-red-700" role="alert">{remErr}</p>}
          <ul className="mt-4 divide-y divide-line">
            {rems.data?.items.map((r) => (
              <li key={r.id} className={`flex items-center gap-3 py-2.5 ${!r.enabled ? "opacity-50" : ""}`}>
                <div className="flex-1"><p className="font-semibold">{r.title}</p><p className={`text-xs ${r.overdue ? "text-red-700" : "text-muted"}`}>{r.due_date} · {r.overdue ? "past" : `${r.days_left} days left`} · user-created</p></div>
                <button aria-label={`Add "${r.title}" to my phone calendar`} title="Add to calendar" onClick={() => downloadIcs(r)} className="rounded p-2 hover:bg-ivory-dark"><CalendarPlus size={16} aria-hidden /></button>
                <button aria-label={r.enabled ? "Turn off reminder" : "Turn on reminder"} onClick={async () => { await api(`/me/reminders/${r.id}`, { method: "PATCH", json: { enabled: !r.enabled } }); rems.reload(); }} className="rounded p-2 hover:bg-ivory-dark">{r.enabled ? <Bell size={16} aria-hidden /> : <BellOff size={16} aria-hidden />}</button>
                <button aria-label="Delete reminder" onClick={async () => { await api(`/me/reminders/${r.id}`, { method: "DELETE" }); rems.reload(); }} className="rounded p-2 hover:bg-ivory-dark"><Trash2 size={16} aria-hidden /></button>
              </li>
            ))}
            {rems.data?.items.length === 0 && <li className="py-3 text-sm text-muted">No reminders.</li>}
          </ul>
        </div>
        <div>
          <h2 className="font-display text-2xl text-navy-900">Recently verified</h2>
          <div className="mt-3 grid gap-3">{updates.data?.items.slice(0, 4).map((u) => <ResultCard key={u.kind + u.slug} c={u} />)}</div>
        </div>
      </section>

      <section aria-labelledby="pd" className="card mt-10 p-5">
        <h2 id="pd" className="font-display text-2xl text-navy-900">Your data</h2>
        <div className="mt-3 flex flex-wrap gap-2">
          <button onClick={exportData} className="btn btn-ghost"><Download size={16} aria-hidden />Download my data</button>
          {!confirmDelete ? <button onClick={() => setConfirmDelete(true)} className="btn btn-ghost text-red-700"><Trash2 size={16} aria-hidden />Delete my account</button> : (
            <span className="flex flex-wrap items-center gap-2" role="alert">This permanently deletes your account, saved items and reminders.
              <button onClick={deleteAccount} className="btn bg-red-700 text-white">Yes, delete everything</button>
              <button onClick={() => setConfirmDelete(false)} className="btn btn-ghost">Cancel</button></span>
          )}
        </div>
      </section>
    </div>
  );
}

export default function DashboardPage() {
  const { user, authLoading } = useApp();
  if (authLoading) return <Loading />;
  if (!user) return (
    <div className="mx-auto max-w-2xl px-4 py-14 text-center">
      <h1 className="font-display text-4xl text-navy-900">My dashboard</h1>
      <p className="mt-3 text-muted">Sign in to save schemes, keep document checklists, track your own application status and set reminders. Browsing and the eligibility check work without an account.</p>
      <div className="mt-6 flex justify-center gap-3"><Link href="/login?next=/dashboard" className="btn btn-primary">Sign in or create account</Link><Link href="/eligibility" className="btn btn-ghost">Check eligibility as a guest</Link></div>
    </div>
  );
  return <Authed />;
}
