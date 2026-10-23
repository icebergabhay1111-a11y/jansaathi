"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Eye, History, ShieldAlert } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useApp } from "@/lib/providers";
import { useFetch } from "@/lib/useFetch";
import { ErrorBox, Loading, Notice, VerificationBadge } from "@/components/ui";
import type { VStatus } from "@/lib/types";

type Row = { slug: string; title: string; status: string; verification_status: VStatus; last_verified: string | null; version: number; freshness: "fresh" | "stale" | "unverified"; updated_at: string; updated_by: string | null };
const KINDS = ["scheme", "right", "guide", "service"] as const;
const NEXT: Record<string, string[]> = { draft: ["source_review"], source_review: ["verified", "draft"], verified: ["approved", "draft"], approved: ["published", "draft"], published: ["unpublished"], unpublished: ["draft", "published"] };
const PUBLIC_PATH: Record<string, string> = { scheme: "/schemes", right: "/rights", guide: "/guides", service: "/services" };
const READONLY = new Set(["slug", "status", "version", "created_at", "updated_at", "updated_by", "freshness", "application_window", "verification_status", "last_verified", "verification_note"]);

function Editor({ kind, slug, onChanged, role }: { kind: string; slug: string; onChanged: () => void; role: string }) {
  const rec = useFetch<Record<string, unknown>>(`/admin/records/${kind}/${slug}`);
  const hist = useFetch<{ items: { version: number; changed_by: string; changed_at: string; note: string | null }[] }>(`/admin/records/${kind}/${slug}/history`);
  const [json, setJson] = useState("");
  const [note, setNote] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [v, setV] = useState({ verification_status: "verified", last_verified: new Date().toISOString().slice(0, 10), note: "" });

  useEffect(() => {
    if (!rec.data) return;
    const editable = Object.fromEntries(Object.entries(rec.data).filter(([k]) => !READONLY.has(k)));
    setJson(JSON.stringify(editable, null, 2));
  }, [rec.data]);

  const fail = (e: unknown) => setMsg({ ok: false, text: e instanceof ApiError ? e.message : "Action failed." });
  async function save() {
    let data: unknown;
    try { data = JSON.parse(json); } catch { setMsg({ ok: false, text: "The JSON is not valid." }); return; }
    try { await api(`/admin/records/${kind}/${slug}`, { method: "PUT", json: { data, note } }); setMsg({ ok: true, text: "Saved. A new version was recorded." }); rec.reload(); hist.reload(); onChanged(); } catch (e) { fail(e); }
  }
  async function move(to: string) {
    try { await api(`/admin/records/${kind}/${slug}/transition`, { method: "POST", json: { to, note } }); setMsg({ ok: true, text: `Moved to ${to}.` }); rec.reload(); onChanged(); } catch (e) { fail(e); }
  }
  async function verify(e: React.FormEvent) {
    e.preventDefault();
    try { await api(`/admin/records/${kind}/${slug}/verify`, { method: "POST", json: v }); setMsg({ ok: true, text: "Verification recorded." }); rec.reload(); onChanged(); } catch (e) { fail(e); }
  }

  if (rec.loading && !rec.data) return <Loading />;
  if (rec.error) return <ErrorBox message={rec.error} onRetry={rec.reload} />;
  const r = rec.data as Record<string, string> & { freshness: { message: string } };
  return (
    <div className="card grid gap-4 p-5">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="font-display text-xl text-navy-900">{(r.name || r.title) as string}</h3>
        <span className="rounded-full bg-ivory-dark px-2 py-0.5 text-xs font-bold">{r.status}</span>
        <VerificationBadge status={r.verification_status as VStatus} />
        {r.status === "published" && <Link href={`${PUBLIC_PATH[kind]}/${slug}`} target="_blank" className="ml-auto inline-flex items-center gap-1 text-sm font-semibold text-navy-700 underline"><Eye size={14} aria-hidden />View public page</Link>}
      </div>
      <p className="text-sm text-muted">{r.freshness.message}</p>
      {msg && <p role="status" className={`rounded-lg p-2 text-sm ${msg.ok ? "bg-leaf-50 text-leaf-dark" : "bg-red-50 text-red-800"}`}>{msg.text}</p>}
      <div>
        <p className="label">Workflow: Draft → Source review → Verified → Approved → Published</p>
        <div className="flex flex-wrap gap-2">
          {(NEXT[r.status] || []).map((to) => <button key={to} onClick={() => move(to)} className="btn btn-ghost !min-h-9 text-sm">Move to {to}</button>)}
        </div>
        <p className="mt-1 text-xs text-muted">Approve / publish / unpublish need the admin role (you: {role}). Editors editing a published record send it back to review.</p>
      </div>
      <form onSubmit={verify} className="grid gap-2 rounded-xl bg-ivory p-3 sm:grid-cols-[1fr_1fr_2fr_auto]">
        <label className="text-sm"><span className="label">Verification</span>
          <select className="input" value={v.verification_status} onChange={(e) => setV({ ...v, verification_status: e.target.value })}><option value="verified">verified</option><option value="reviewed">reviewed</option><option value="needs_verification">needs_verification</option></select></label>
        <label className="text-sm"><span className="label">Date checked</span><input type="date" className="input" value={v.last_verified} onChange={(e) => setV({ ...v, last_verified: e.target.value })} /></label>
        <label className="text-sm"><span className="label">What did you check?</span><input className="input" value={v.note} onChange={(e) => setV({ ...v, note: e.target.value })} placeholder="e.g. Confirmed amounts on official FAQ dated …" /></label>
        <button className="btn btn-primary self-end">Record</button>
      </form>
      <div>
        <label className="label" htmlFor="rj">Record content (JSON)</label>
        <textarea id="rj" spellCheck={false} className="input min-h-80 font-mono text-xs" value={json} onChange={(e) => setJson(e.target.value)} />
        <div className="mt-2 flex gap-2"><input className="input" placeholder="Change note (optional)" value={note} onChange={(e) => setNote(e.target.value)} /><button onClick={save} className="btn btn-primary">Save changes</button></div>
        <p className="mt-1 text-xs text-muted">Links must be official https government domains; benefit amounts are rejected on unverified records.</p>
      </div>
      <details><summary className="flex cursor-pointer items-center gap-1 text-sm font-semibold"><History size={14} aria-hidden />Change history</summary>
        <ul className="mt-2 space-y-1 text-sm">{hist.data?.items.map((h) => <li key={h.version}>v{h.version} · {h.changed_by} · {new Date(h.changed_at).toLocaleString()} {h.note ? `· ${h.note}` : ""}</li>)}</ul>
      </details>
    </div>
  );
}

function Records({ role }: { role: string }) {
  const [kind, setKind] = useState<(typeof KINDS)[number]>("scheme");
  const [status, setStatus] = useState("");
  const [sel, setSel] = useState<string | null>(null);
  const list = useFetch<{ items: Row[] }>(`/admin/records?kind=${kind}${status ? `&status=${status}` : ""}`);
  const [creating, setCreating] = useState(false);
  const [newJson, setNewJson] = useState(`{\n  "slug": "new-scheme-slug",\n  "name": "Scheme name",\n  "summary": "One-line summary",\n  "ministry": "Responsible ministry",\n  "categories": ["education"],\n  "sources": [{"url": "https://www.india.gov.in", "organisation": "Source organisation", "title": "Source title", "type": "official_portal"}]\n}`);
  const [cErr, setCErr] = useState<string | null>(null);

  async function create() {
    setCErr(null);
    try { const d = JSON.parse(newJson); await api(`/admin/records/${kind}`, { method: "POST", json: { data: d } }); setCreating(false); list.reload(); setSel(d.slug); }
    catch (e) { setCErr(e instanceof SyntaxError ? "Invalid JSON." : e instanceof Error ? e.message : "Failed."); }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_1.3fr]">
      <div>
        <div className="flex flex-wrap gap-2">
          <select aria-label="Record type" className="input !min-h-10 w-auto" value={kind} onChange={(e) => { setKind(e.target.value as typeof kind); setSel(null); }}>{KINDS.map((k) => <option key={k}>{k}</option>)}</select>
          <select aria-label="Status filter" className="input !min-h-10 w-auto" value={status} onChange={(e) => setStatus(e.target.value)}><option value="">all statuses</option>{Object.keys(NEXT).map((s) => <option key={s}>{s}</option>)}</select>
          <button onClick={() => setCreating(!creating)} className="btn btn-ghost !min-h-10">+ New {kind}</button>
        </div>
        {creating && (
          <div className="card mt-3 p-3">
            <textarea aria-label="New record JSON" spellCheck={false} className="input min-h-48 font-mono text-xs" value={newJson} onChange={(e) => setNewJson(e.target.value)} />
            {cErr && <p className="mt-1 text-sm text-red-700" role="alert">{cErr}</p>}
            <button onClick={create} className="btn btn-primary mt-2">Create as draft</button>
          </div>
        )}
        {list.loading && <Loading />}
        {list.error && <ErrorBox message={list.error} onRetry={list.reload} />}
        <ul className="mt-3 max-h-[70vh] divide-y divide-line overflow-auto rounded-xl border border-line bg-white">
          {list.data?.items.map((r) => (
            <li key={r.slug}>
              <button onClick={() => setSel(r.slug)} className={`w-full px-3 py-2.5 text-left hover:bg-ivory ${sel === r.slug ? "bg-navy-100" : ""}`}>
                <span className="block text-sm font-semibold text-navy-900">{r.title}</span>
                <span className="text-xs text-muted">{r.status} · {r.verification_status} · v{r.version}{r.freshness !== "fresh" ? ` · ${r.freshness}` : ""}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
      <div>{sel ? <Editor key={kind + sel} kind={kind} slug={sel} role={role} onChanged={list.reload} /> : <p className="text-muted">Select a record to edit, verify or move through the workflow.</p>}</div>
    </div>
  );
}

function Queue() {
  const q = useFetch<{ items: { kind: string; slug: string; title: string; state: string; review_due: string | null; note: string | null }[] }>("/admin/review-queue");
  if (q.loading) return <Loading />;
  if (q.error) return <ErrorBox message={q.error} onRetry={q.reload} />;
  return (
    <div>
      <Notice>Published records that were never verified or whose review date has passed. Old does not mean wrong — re-check and record the verification.</Notice>
      <ul className="mt-3 divide-y divide-line rounded-xl border border-line bg-white">
        {q.data?.items.map((i) => <li key={i.kind + i.slug} className="px-3 py-2.5 text-sm"><span className="font-semibold">{i.title}</span> <span className="text-muted">({i.kind}) · {i.state}{i.review_due ? ` · due ${i.review_due}` : ""}</span>{i.note && <p className="text-xs text-muted">{i.note}</p>}</li>)}
      </ul>
    </div>
  );
}

function Reports() {
  const [status, setStatus] = useState("open");
  const r = useFetch<{ items: { id: number; item_type: string; item_slug: string | null; kind: string; message: string; created_at: string }[] }>(`/admin/reports?status=${status}`);
  return (
    <div>
      <select aria-label="Report status" className="input !min-h-10 w-auto" value={status} onChange={(e) => setStatus(e.target.value)}><option>open</option><option>resolved</option><option>dismissed</option></select>
      {r.loading && <Loading />}
      {r.data?.items.length === 0 && <p className="mt-3 text-muted">No {status} reports.</p>}
      <ul className="mt-3 grid gap-3">
        {r.data?.items.map((x) => (
          <li key={x.id} className="card p-4 text-sm">
            <p className="font-semibold">{x.kind} · {x.item_type}{x.item_slug ? ` / ${x.item_slug}` : ""} <span className="font-normal text-muted">· {new Date(x.created_at).toLocaleString()}</span></p>
            <p className="mt-1 whitespace-pre-wrap">{x.message}</p>
            {status === "open" && <div className="mt-2 flex gap-2">
              <button className="btn btn-ghost !min-h-9" onClick={async () => { await api(`/admin/reports/${x.id}`, { method: "PATCH", json: { status: "resolved" } }); r.reload(); }}>Mark resolved</button>
              <button className="btn btn-ghost !min-h-9" onClick={async () => { await api(`/admin/reports/${x.id}`, { method: "PATCH", json: { status: "dismissed" } }); r.reload(); }}>Dismiss</button>
            </div>}
          </li>
        ))}
      </ul>
    </div>
  );
}

function Import() {
  const [kind, setKind] = useState("scheme");
  const [text, setText] = useState("[]");
  const [res, setRes] = useState<{ created: number; updated: number; errors: { index: number; slug?: string; errors: string[] }[] } | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const runs = useFetch<{ items: { id: number; actor: string; kind: string; created: number; updated: number; errors: unknown[]; at: string }[] }>("/admin/imports");
  async function run() {
    setErr(null); setRes(null);
    try { const records = JSON.parse(text); setRes(await api("/admin/import", { method: "POST", json: { kind, records } })); runs.reload(); }
    catch (e) { setErr(e instanceof SyntaxError ? "Invalid JSON — paste an array of records." : e instanceof Error ? e.message : "Import failed."); }
  }
  return (
    <div className="grid gap-3">
      <Notice>Paste a JSON array of records. Every record is validated (required fields, official https links, sources). Imported records always enter as <strong>drafts</strong>.</Notice>
      <select aria-label="Import type" className="input !min-h-10 w-auto" value={kind} onChange={(e) => setKind(e.target.value)}>{KINDS.map((k) => <option key={k}>{k}</option>)}</select>
      <textarea aria-label="Records JSON" spellCheck={false} className="input min-h-56 font-mono text-xs" value={text} onChange={(e) => setText(e.target.value)} />
      <button onClick={run} className="btn btn-primary justify-self-start">Validate & import</button>
      {err && <ErrorBox message={err} />}
      {res && <div className="card p-4 text-sm" role="status"><p className="font-semibold">Created {res.created}, updated {res.updated}, failed {res.errors.length}</p>
        <ul className="mt-2 space-y-1">{res.errors.map((e) => <li key={e.index} className="text-red-800">#{e.index} {e.slug || ""}: {e.errors.join("; ")}</li>)}</ul></div>}
      <h3 className="mt-4 font-semibold">Recent imports</h3>
      <ul className="text-sm">{runs.data?.items.map((r) => <li key={r.id}>{new Date(r.at).toLocaleString()} · {r.actor} · {r.kind} · +{r.created} / ~{r.updated} / ✗{r.errors.length}</li>)}</ul>
    </div>
  );
}

function Audit() {
  const a = useFetch<{ items: { actor: string; action: string; target: string; detail: unknown; at: string }[] }>("/admin/audit");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("editor");
  const [msg, setMsg] = useState<string | null>(null);
  return (
    <div className="grid gap-6">
      <form className="card grid gap-2 p-4 sm:grid-cols-[2fr_1fr_auto]" onSubmit={async (e) => { e.preventDefault(); try { await api("/admin/users/role", { method: "POST", json: { email, role } }); setMsg(`Updated ${email} → ${role}`); a.reload(); } catch (err) { setMsg(err instanceof Error ? err.message : "Failed"); } }}>
        <input aria-label="User email" className="input" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="user@example.com" />
        <select aria-label="Role" className="input" value={role} onChange={(e) => setRole(e.target.value)}><option>user</option><option>editor</option><option>admin</option></select>
        <button className="btn btn-primary">Set role</button>
        {msg && <p className="text-sm sm:col-span-3" role="status">{msg}</p>}
      </form>
      {a.error && <ErrorBox message={a.error} />}
      <ul className="divide-y divide-line rounded-xl border border-line bg-white text-sm">
        {a.data?.items.map((x, i) => <li key={i} className="px-3 py-2"><span className="font-semibold">{x.action}</span> {x.target} <span className="text-muted">· {x.actor} · {new Date(x.at).toLocaleString()}</span><code className="block truncate text-xs text-muted">{JSON.stringify(x.detail)}</code></li>)}
      </ul>
    </div>
  );
}

export default function AdminPage() {
  const { user, authLoading } = useApp();
  const [tab, setTab] = useState("records");
  const ov = useFetch<{ records: Record<string, { total: number; by_status: Record<string, number> }>; open_reports: number }>(user && user.role !== "user" ? "/admin/overview" : null);
  if (authLoading) return <Loading />;
  if (!user || user.role === "user") return (
    <div className="mx-auto max-w-xl px-4 py-16 text-center">
      <ShieldAlert size={36} className="mx-auto text-saffron-dark" aria-hidden />
      <h1 className="mt-3 font-display text-3xl text-navy-900">Restricted area</h1>
      <p className="mt-2 text-muted">The content dashboard is only for JanSaathi editors and administrators.</p>
      {!user && <Link href="/login?next=/admin" className="btn btn-primary mt-5">Sign in</Link>}
    </div>
  );
  const tabs = [["records", "Records"], ["queue", "Review queue"], ["reports", `Reports${ov.data ? ` (${ov.data.open_reports})` : ""}`], ["import", "Import"], ...(user.role === "admin" ? [["audit", "Audit & users"]] : [])];
  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="font-display text-4xl text-navy-900">Content administration</h1>
      <p className="text-muted">Signed in as {user.email} ({user.role})</p>
      {ov.data && <dl className="mt-5 grid gap-3 sm:grid-cols-4">{Object.entries(ov.data.records).map(([k, v]) => <div key={k} className="card p-4"><dt className="text-sm font-semibold capitalize text-muted">{k}s</dt><dd className="font-display text-2xl text-navy-900">{v.total}</dd><dd className="text-xs text-muted">{Object.entries(v.by_status).map(([s, n]) => `${s}: ${n}`).join(" · ")}</dd></div>)}</dl>}
      <div role="tablist" className="mt-6 flex flex-wrap gap-2">{tabs.map(([k, l]) => <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)} className={`btn !min-h-10 ${tab === k ? "btn-primary" : "btn-ghost"}`}>{l}</button>)}</div>
      <div className="mt-5" role="tabpanel">
        {tab === "records" && <Records role={user.role} />}
        {tab === "queue" && <Queue />}
        {tab === "reports" && <Reports />}
        {tab === "import" && <Import />}
        {tab === "audit" && user.role === "admin" && <Audit />}
      </div>
    </div>
  );
}
