"use client";
import Link from "next/link";
import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useApp } from "@/lib/providers";
import { ErrorBox, Notice } from "@/components/ui";

function LoginInner() {
  const { refreshUser } = useApp();
  const router = useRouter();
  const sp = useSearchParams();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const next = sp.get("next") || "/dashboard";
  const safeNext = next.startsWith("/") && !next.startsWith("//") ? next : "/dashboard";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const v: Record<string, string> = {};
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim())) v.email = "Enter a valid email address.";
    if (password.length < 8) v.password = "Password must be at least 8 characters.";
    setErrs(v);
    if (Object.keys(v).length) return;
    setBusy(true); setErr(null);
    try {
      await api(`/auth/${mode}`, { method: "POST", json: { email, password, display_name: name || undefined } });
      await refreshUser();
      router.push(safeNext);
    } catch (e) {
      setErr(e instanceof ApiError ? (e.fieldErrors[0]?.message || e.message) : "Could not sign in.");
    } finally { setBusy(false); }
  }

  return (
    <div className="mx-auto max-w-md px-4 py-12">
      <h1 className="font-display text-3xl text-navy-900">{mode === "login" ? "Sign in" : "Create an account"}</h1>
      <p className="mt-2 text-muted">An account is optional. It lets you save schemes, track your own application status and set reminders.</p>
      <div className="mt-4"><Notice>We only store your email, a securely hashed password and what you choose to save. You can export or delete everything at any time.</Notice></div>
      <form onSubmit={submit} noValidate className="card mt-6 grid gap-4 p-6">
        {mode === "register" && <div><label className="label" htmlFor="nm">Name (optional)</label><input id="nm" className="input" value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" /></div>}
        <div>
          <label className="label" htmlFor="em">Email</label>
          <input id="em" type="email" className="input" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" aria-invalid={!!errs.email} aria-describedby={errs.email ? "em-err" : undefined} />
          {errs.email && <p id="em-err" className="mt-1 text-sm text-red-700">{errs.email}</p>}
        </div>
        <div>
          <label className="label" htmlFor="pw">Password</label>
          <input id="pw" type="password" className="input" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete={mode === "login" ? "current-password" : "new-password"} aria-invalid={!!errs.password} aria-describedby={errs.password ? "pw-err" : undefined} />
          {errs.password && <p id="pw-err" className="mt-1 text-sm text-red-700">{errs.password}</p>}
        </div>
        {err && <ErrorBox message={err} />}
        <button className="btn btn-primary" disabled={busy}>{busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}</button>
        <button type="button" className="text-sm font-semibold text-navy-700 hover:underline" onClick={() => { setMode(mode === "login" ? "register" : "login"); setErr(null); }}>
          {mode === "login" ? "New here? Create an account" : "Already have an account? Sign in"}
        </button>
      </form>
      <p className="mt-4 text-center text-sm text-muted">Or <Link href="/schemes" className="underline">continue as a guest</Link> — every information page works without an account.</p>
    </div>
  );
}

export default function LoginPage() {
  return <Suspense fallback={null}><LoginInner /></Suspense>;
}
