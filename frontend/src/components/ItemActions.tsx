"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Bookmark, BookmarkCheck, Flag, Printer } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useApp } from "@/lib/providers";

export function ItemActions({ itemType, slug }: { itemType: "scheme" | "service" | "right" | "guide"; slug: string }) {
  const { t, user } = useApp();
  const path = usePathname();
  const [saved, setSaved] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [reporting, setReporting] = useState(false);

  async function save() {
    setMsg(null);
    try {
      await api("/me/saved", { method: "POST", json: { item_type: itemType, item_slug: slug } });
      setSaved(true);
      setMsg("Saved to your dashboard.");
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) { setSaved(true); setMsg("Already in your dashboard."); }
      else setMsg(e instanceof Error ? e.message : "Could not save.");
    }
  }

  return (
    <div className="no-print">
      <div className="flex flex-wrap gap-2">
        {user ? (
          <button onClick={save} disabled={saved} className="btn btn-ghost">{saved ? <BookmarkCheck size={16} aria-hidden /> : <Bookmark size={16} aria-hidden />}{saved ? t("saved") : t("save")}</button>
        ) : (
          <Link href={`/login?next=${encodeURIComponent(path)}`} className="btn btn-ghost"><Bookmark size={16} aria-hidden />Sign in to save</Link>
        )}
        <button onClick={() => window.print()} className="btn btn-ghost"><Printer size={16} aria-hidden />Print</button>
        <button onClick={() => setReporting(!reporting)} aria-expanded={reporting} className="btn btn-ghost"><Flag size={16} aria-hidden />{t("report")}</button>
      </div>
      {msg && <p role="status" className="mt-2 text-sm text-leaf-dark">{msg}</p>}
      {reporting && <ReportForm itemType={itemType} slug={slug} onDone={() => setReporting(false)} />}
    </div>
  );
}

export function ReportForm({ itemType, slug, onDone, defaultKind = "outdated" }: { itemType: string; slug?: string; onDone?: () => void; defaultKind?: string }) {
  const [kind, setKind] = useState(defaultKind);
  const [message, setMessage] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "done" | "error">("idle");
  const [err, setErr] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (message.trim().length < 5) { setErr("Please describe the problem (at least 5 characters)."); return; }
    setState("sending"); setErr("");
    try {
      await api("/reports", { method: "POST", json: { item_type: itemType, item_slug: slug, kind, message } });
      setState("done");
      setTimeout(() => onDone?.(), 1500);
    } catch (e) {
      setState("error"); setErr(e instanceof Error ? e.message : "Could not send.");
    }
  }

  if (state === "done") return <p role="status" className="mt-3 rounded-xl bg-leaf-50 p-3 text-sm text-leaf-dark">Thank you — an editor will review your report.</p>;
  return (
    <form onSubmit={submit} className="mt-3 grid gap-3 rounded-xl border border-line bg-white p-4" noValidate>
      <div>
        <label className="label" htmlFor="rk">What is wrong?</label>
        <select id="rk" className="input" value={kind} onChange={(e) => setKind(e.target.value)}>
          <option value="outdated">Information is outdated</option>
          <option value="incorrect">Information is incorrect</option>
          {itemType === "assistant" && <option value="ai_answer">The AI answer was wrong</option>}
          <option value="other">Something else</option>
        </select>
      </div>
      <div>
        <label className="label" htmlFor="rm">Details (do not include personal information)</label>
        <textarea id="rm" className="input min-h-24" value={message} onChange={(e) => setMessage(e.target.value)} aria-invalid={!!err} aria-describedby={err ? "rm-err" : undefined} maxLength={2000} />
        {err && <p id="rm-err" className="mt-1 text-sm text-red-700">{err}</p>}
      </div>
      <button className="btn btn-primary justify-self-start" disabled={state === "sending"}>{state === "sending" ? "Sending…" : "Send report"}</button>
    </form>
  );
}
