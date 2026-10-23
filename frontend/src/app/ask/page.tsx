"use client";
import Link from "next/link";
import { Fragment, Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Bot, Copy, Download, ExternalLink, Flag, Plus, Send, ShieldCheck, Trash2, User } from "lucide-react";
import { api } from "@/lib/api";
import { useApp } from "@/lib/providers";
import { Notice, VerificationBadge } from "@/components/ui";
import { VoiceButton, type VoiceLang } from "@/components/VoiceButton";
import { ReportForm } from "@/components/ItemActions";
import type { VStatus } from "@/lib/types";

type Src = { n: number; kind: string; slug: string; title: string; url: string | null; path: string; verification_status: VStatus; last_verified: string | null; cited: boolean };
type Msg = { role: "user" | "assistant"; content: string; sources?: Src[]; mode?: "ai" | "fallback"; mode_reason?: string | null; disclaimer?: string; followups?: string[]; error?: boolean };
type Convo = { id: string; title: string; messages: Msg[]; at: number };

const KEY = "js_chats_v1";
const uid = () => Math.random().toString(36).slice(2) + Date.now().toString(36);
const SUGGESTED: Record<VoiceLang, string[]> = {
  en: ["I am a student from Uttar Pradesh. What scholarships should I investigate?", "My pension has been pending for months. What should I do?", "How can I apply for an income certificate?", "The police refused to register my FIR. What can I do?", "How do I file an RTI?"],
  hi: ["अनुच्छेद 21 को आसान हिन्दी में समझाइए", "वृद्धावस्था पेंशन कैसे मिलेगी?", "राशन कार्ड न मिलने पर शिकायत कहाँ करें?", "मुझे मुफ़्त कानूनी सहायता कैसे मिलेगी?"],
  ta: ["முதியோர் ஓய்வூதியம் பெறுவது எப்படி?", "கல்லூரி மாணவர்களுக்கான உதவித்தொகை என்ன?", "காவல் நிலையத்தில் புகார் ஏற்க மறுத்தால் என்ன செய்வது?", "இலவச சட்ட உதவி எப்படிப் பெறுவது?"],
};

// Minimal, safe renderer: React escapes text; we only interpret **bold**, bullet lines and [n] citations.
function Rich({ text, sources }: { text: string; sources?: Src[] }) {
  const lines = text.split("\n");
  const inline = (s: string, k: number) =>
    s.split(/(\*\*[^*]+\*\*|\[\d+\])/g).map((part, i) => {
      if (/^\*\*[^*]+\*\*$/.test(part)) return <strong key={`${k}-${i}`}>{part.slice(2, -2)}</strong>;
      const m = part.match(/^\[(\d+)\]$/);
      if (m) {
        const src = sources?.find((x) => x.n === Number(m[1]));
        return src ? <Link key={`${k}-${i}`} href={src.path} className="mx-0.5 rounded bg-navy-100 px-1 text-xs font-bold text-navy-800 no-underline" title={src.title}>{m[1]}</Link> : <Fragment key={`${k}-${i}`}>{part}</Fragment>;
      }
      return <Fragment key={`${k}-${i}`}>{part}</Fragment>;
    });
  const out: React.ReactNode[] = [];
  let list: React.ReactNode[] = [];
  const flush = () => { if (list.length) { out.push(<ul key={`l${out.length}`}>{list}</ul>); list = []; } };
  lines.forEach((ln, i) => {
    const b = ln.match(/^\s*(?:[-*•]|\d+\.)\s+(.*)$/);
    if (b) { list.push(<li key={i}>{inline(b[1], i)}</li>); return; }
    flush();
    if (ln.trim()) out.push(<p key={i}>{inline(ln.replace(/^#+\s*/, ""), i)}</p>);
  });
  flush();
  return <div className="prose-js">{out}</div>;
}

function AskInner() {
  const { t, lang, setLang } = useApp();
  // Answer + voice language. Tamil is available for AI answers and voice even though the interface is English/Hindi.
  const [alang, setAlang] = useState<VoiceLang>(lang);
  const [interim, setInterim] = useState("");
  const sp = useSearchParams();
  const router = useRouter();
  const [convos, setConvos] = useState<Convo[]>([]);
  const [current, setCurrent] = useState<Convo>({ id: uid(), title: "New conversation", messages: [], at: Date.now() });
  const [keep, setKeep] = useState(false);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [reportFor, setReportFor] = useState<number | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const asked = useRef(false);

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(KEY) || "null");
      if (saved) { setKeep(true); setConvos(saved); }
    } catch { /* storage unavailable */ }
  }, []);
  useEffect(() => {
    try {
      if (!keep) { localStorage.removeItem(KEY); return; }
      const all = [current, ...convos.filter((c) => c.id !== current.id)].filter((c) => c.messages.length).slice(0, 20);
      localStorage.setItem(KEY, JSON.stringify(all));
    } catch { /* ignore */ }
  }, [keep, convos, current]);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [current.messages.length, busy]);

  async function send(text: string, langOverride?: VoiceLang) {
    const q = text.trim();
    if (!q || busy) return;
    const history = current.messages.filter((m) => !m.error).map((m) => ({ role: m.role, content: m.content }));
    const next: Convo = { ...current, title: current.messages.length ? current.title : q.slice(0, 60), messages: [...current.messages, { role: "user", content: q }], at: Date.now() };
    setCurrent(next); setInput(""); setBusy(true);
    try {
      const r = await api<{ answer: string; sources: Src[]; mode: "ai" | "fallback"; mode_reason: string | null; disclaimer: string; followups: string[] }>(
        "/assistant/ask", { method: "POST", json: { question: q, history, lang: langOverride || alang } });
      setCurrent((c) => ({ ...c, messages: [...c.messages, { role: "assistant", content: r.answer, sources: r.sources, mode: r.mode, mode_reason: r.mode_reason, disclaimer: r.disclaimer, followups: r.followups }] }));
    } catch (e) {
      setCurrent((c) => ({ ...c, messages: [...c.messages, { role: "assistant", content: e instanceof Error ? e.message : "Something went wrong.", error: true }] }));
    } finally { setBusy(false); }
  }

  useEffect(() => {
    const q = sp.get("q");
    const ql = sp.get("lang");
    const qlang = ql === "ta" || ql === "hi" || ql === "en" ? (ql as VoiceLang) : undefined;
    if (qlang) setAlang(qlang);
    if (q && !asked.current) { asked.current = true; send(q, qlang); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sp]);

  const newChat = () => {
    if (current.messages.length) setConvos((cs) => [current, ...cs.filter((c) => c.id !== current.id)]);
    setCurrent({ id: uid(), title: "New conversation", messages: [], at: Date.now() });
  };
  const exportChat = () => {
    const txt = current.messages.map((m) => `${m.role === "user" ? "You" : "JanSaathi"}:\n${m.content}${m.sources?.length ? `\nSources: ${m.sources.map((s) => `${s.title} (${s.url || s.path})`).join("; ")}` : ""}`).join("\n\n---\n\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([`JanSaathi conversation — ${new Date().toLocaleString()}\nGeneral information, not legal advice.\n\n${txt}`], { type: "text/plain" }));
    a.download = "jansaathi-conversation.txt"; a.click(); URL.revokeObjectURL(a.href);
  };
  const lastRetry = () => { const lastUser = [...current.messages].reverse().find((m) => m.role === "user"); if (lastUser) { setCurrent((c) => ({ ...c, messages: c.messages.filter((m) => !m.error).slice(0, -1) })); send(lastUser.content); } };

  return (
    <div className="mx-auto grid max-w-7xl gap-6 px-4 py-8 lg:grid-cols-[260px_1fr]">
      <aside className="order-2 lg:order-1" aria-label="Conversations">
        <button onClick={newChat} className="btn btn-primary w-full"><Plus size={16} aria-hidden />{t("new_chat")}</button>
        <label className="mt-4 flex items-start gap-2 text-sm">
          <input type="checkbox" className="mt-1 h-4 w-4" checked={keep} onChange={(e) => setKeep(e.target.checked)} />
          <span>Keep conversation history on this device<span className="block text-xs text-muted">Stored only in your browser. Off by default.</span></span>
        </label>
        {keep && convos.length > 0 && (
          <ul className="mt-4 space-y-1">
            {convos.filter((c) => c.id !== current.id).map((c) => (
              <li key={c.id} className="flex items-center gap-1">
                <button onClick={() => { newChat(); setCurrent(c); }} className="flex-1 truncate rounded-lg px-2 py-2 text-left text-sm hover:bg-ivory-dark">{c.title}</button>
                <button aria-label={`Delete ${c.title}`} onClick={() => setConvos((cs) => cs.filter((x) => x.id !== c.id))} className="rounded p-2 text-muted hover:bg-ivory-dark"><Trash2 size={14} aria-hidden /></button>
              </li>
            ))}
          </ul>
        )}
        {keep && <button onClick={() => { setConvos([]); setKeep(false); }} className="mt-3 text-sm font-semibold text-red-700 hover:underline">Delete all saved conversations</button>}
      </aside>

      <section className="order-1 flex min-h-[70vh] flex-col lg:order-2" aria-labelledby="ask-h">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 id="ask-h" className="font-display text-3xl text-navy-900">{t("nav_ask")}</h1>
          <div className="flex items-center gap-2 text-sm">
            <label htmlFor="alang" className="font-semibold">Speak &amp; answer in</label>
            <select id="alang" className="input !min-h-10 w-auto" value={alang} onChange={(e) => { const v = e.target.value as VoiceLang; setAlang(v); if (v !== "ta" && v !== lang) setLang(v); }}>
              <option value="en">English</option><option value="hi">हिन्दी</option><option value="ta">தமிழ் (Tamil — AI)</option>
            </select>
            {current.messages.length > 0 && <>
              <button onClick={exportChat} className="btn btn-ghost !min-h-10 !px-3" aria-label="Download conversation"><Download size={16} aria-hidden /></button>
              <button onClick={() => setCurrent({ ...current, messages: [] })} className="btn btn-ghost !min-h-10 !px-3" aria-label="Clear conversation"><Trash2 size={16} aria-hidden /></button>
            </>}
          </div>
        </div>
        {alang === "ta" && <div className="mt-3"><Notice tone="warn">தமிழ் பதில்கள் AI மூலம் உருவாக்கப்படுகின்றன; அவை மனிதரால் சரிபார்க்கப்படவில்லை. Tamil answers are AI-generated from English records and not reviewed by a person — check the official links. If the AI service is off, records are shown in English.</Notice></div>}
        <div className="mt-3"><Notice>Answers come only from JanSaathi&apos;s published records, with sources. Not legal advice, not an official decision. Don&apos;t share Aadhaar, bank details or OTPs.</Notice></div>

        <div className="mt-4 flex-1 space-y-4" aria-live="polite">
          {current.messages.length === 0 && (
            <div className="card p-6">
              <p className="font-display text-xl text-navy-900">Try asking</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {SUGGESTED[alang].map((s) => <button key={s} onClick={() => send(s)} className="rounded-full border border-line bg-ivory px-3 py-1.5 text-left text-sm hover:border-navy-700">{s}</button>)}
              </div>
            </div>
          )}
          {current.messages.map((m, i) => (
            <div key={i} className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}>
              {m.role === "assistant" && <span className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-full bg-navy-900 text-white" aria-hidden><Bot size={16} /></span>}
              <div className={`max-w-[85%] rounded-2xl p-4 ${m.role === "user" ? "bg-navy-900 text-white" : m.error ? "border border-red-200 bg-red-50 text-red-900" : "card"}`}>
                <span className="sr-only">{m.role === "user" ? "You said:" : "JanSaathi replied:"}</span>
                {m.role === "user" ? <p className="whitespace-pre-wrap">{m.content}</p> : <Rich text={m.content} sources={m.sources} />}
                {m.error && <button onClick={lastRetry} className="btn btn-ghost mt-2 bg-white">{t("retry")}</button>}
                {m.role === "assistant" && !m.error && (
                  <>
                    <p className={`mt-3 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${m.mode === "ai" ? "bg-saffron-50 text-saffron-dark" : "bg-leaf-50 text-leaf-dark"}`}>
                      {m.mode === "ai" ? <>AI-generated explanation of the records below — check the sources</> : <><ShieldCheck size={12} aria-hidden />Direct from JanSaathi records{m.mode_reason ? ` (AI unavailable: ${m.mode_reason})` : ""}</>}
                    </p>
                    {m.sources && m.sources.length > 0 && (
                      <details className="mt-3 rounded-xl bg-ivory p-3" open={m.mode === "fallback"}>
                        <summary className="cursor-pointer text-sm font-semibold text-navy-900">Sources ({m.sources.length})</summary>
                        <ol className="mt-2 space-y-2 text-sm">
                          {m.sources.map((s) => (
                            <li key={s.n} className="flex flex-wrap items-center gap-2">
                              <span className="font-bold text-navy-800">[{s.n}]</span>
                              <Link href={s.path} className="font-semibold text-navy-700 underline">{s.title}</Link>
                              <VerificationBadge status={s.verification_status} />
                              {s.url && <a href={s.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-0.5 text-xs text-muted underline">official<ExternalLink size={11} aria-hidden /></a>}
                            </li>
                          ))}
                        </ol>
                      </details>
                    )}
                    {m.disclaimer && <p className="mt-2 text-xs text-muted">{m.disclaimer}</p>}
                    <div className="mt-2 flex flex-wrap gap-2">
                      <button onClick={() => navigator.clipboard.writeText(m.content)} className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-semibold text-muted hover:bg-ivory-dark"><Copy size={13} aria-hidden />Copy</button>
                      <button onClick={() => setReportFor(reportFor === i ? null : i)} className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-semibold text-muted hover:bg-ivory-dark"><Flag size={13} aria-hidden />Report incorrect</button>
                    </div>
                    {reportFor === i && <ReportForm itemType="assistant" defaultKind="ai_answer" onDone={() => setReportFor(null)} />}
                    {i === current.messages.length - 1 && m.followups && (
                      <div className="mt-3 flex flex-wrap gap-2">{m.followups.map((f) => <button key={f} onClick={() => f.toLowerCase().includes("eligibility") || f.includes("पात्रता") ? router.push("/eligibility") : send(f)} className="rounded-full border border-line px-3 py-1 text-xs font-semibold hover:border-navy-700">{f}</button>)}</div>
                    )}
                  </>
                )}
              </div>
              {m.role === "user" && <span className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-full bg-saffron text-navy-950" aria-hidden><User size={16} /></span>}
            </div>
          ))}
          {busy && <p role="status" className="flex items-center gap-2 text-muted"><Bot size={16} className="animate-pulse" aria-hidden />Searching verified records…</p>}
          <div ref={endRef} />
        </div>

        <form onSubmit={(e) => { e.preventDefault(); send(input); }} className="sticky bottom-0 mt-4 flex gap-2 bg-ivory py-3">
          <VoiceButton lang={alang} onInterim={(x) => setInterim(x)} onText={(x) => { setInterim(""); setInput((cur) => (cur ? `${cur} ${x}` : x)); }} className="self-center" />
          <label htmlFor="ask-in" className="sr-only">{t("ask_placeholder")}</label>
          <textarea id="ask-in" rows={2} className="input resize-none" maxLength={1500} value={interim || input} onChange={(e) => setInput(e.target.value)} placeholder={alang === "ta" ? "தட்டச்சு செய்யவும் அல்லது 🎤 அழுத்திப் பேசவும்…" : alang === "hi" ? "लिखें या 🎤 दबाकर बोलें…" : "Type, or tap 🎤 and speak…"}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); } }} />
          <button className="btn btn-saffron" disabled={busy || !input.trim()}><Send size={16} aria-hidden /><span className="sr-only sm:not-sr-only">{t("send")}</span></button>
        </form>
      </section>
    </div>
  );
}

export default function AskPage() {
  return <Suspense fallback={null}><AskInner /></Suspense>;
}
