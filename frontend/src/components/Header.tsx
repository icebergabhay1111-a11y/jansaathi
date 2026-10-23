"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Languages, LogIn, Menu, WifiOff, X } from "lucide-react";
import { useApp } from "@/lib/providers";
import type { Key } from "@/lib/i18n-dict";
import { Logo } from "./Logo";

const NAV: [string, Key][] = [
  ["/", "nav_home"], ["/schemes", "nav_schemes"], ["/rights", "nav_rights"], ["/services", "nav_services"],
  ["/complaints", "nav_complaints"], ["/ask", "nav_ask"], ["/offices", "nav_offices"], ["/dashboard", "nav_dashboard"],
];

export function Header() {
  const { t, lang, setLang, user, logout } = useApp();
  const path = usePathname();
  const [open, setOpen] = useState(false);
  const [offline, setOffline] = useState(false);

  useEffect(() => setOpen(false), [path]);
  useEffect(() => {
    const up = () => setOffline(!navigator.onLine);
    up();
    window.addEventListener("online", up);
    window.addEventListener("offline", up);
    return () => { window.removeEventListener("online", up); window.removeEventListener("offline", up); };
  }, []);

  const active = (href: string) => (href === "/" ? path === "/" : path.startsWith(href));
  const nav = user && user.role !== "user" ? [...NAV, ["/admin", "nav_admin"] as [string, Key]] : NAV;

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-ivory/95 backdrop-blur">
      <a href="#main" className="skip-link">{t("skip")}</a>
      <div className="tricolor-rule" aria-hidden />
      {offline && <p role="status" className="flex items-center justify-center gap-2 bg-saffron-50 px-4 py-1.5 text-sm text-saffron-dark"><WifiOff size={15} aria-hidden />{t("offline")}</p>}
      <div className="mx-auto flex max-w-7xl items-center gap-2 px-3 py-3 sm:gap-3 sm:px-4">
        <Link href="/" className="flex min-w-0 items-center gap-2" aria-label="JanSaathi home">
          <Logo className="h-8 w-8 shrink-0 sm:h-9 sm:w-9" />
          <span className="leading-tight">
            <span className="block font-display text-lg font-bold text-navy-900 sm:text-xl">JanSaathi</span>
            <span className="hidden text-[11px] font-medium uppercase tracking-wider text-muted sm:block">{t("brandTag")}</span>
          </span>
        </Link>
        <nav aria-label="Main" className="ml-6 hidden flex-1 items-center gap-1 2xl:flex">
          {nav.map(([href, k]) => (
            <Link key={href} href={href} aria-current={active(href) ? "page" : undefined}
              className={`rounded-lg px-2.5 py-2 text-sm font-semibold transition-colors ${active(href) ? "bg-navy-900 text-white" : "text-navy-900 hover:bg-ivory-dark"}`}>{t(k)}</Link>
          ))}
        </nav>
        <div className="ml-auto flex shrink-0 items-center gap-1.5 sm:gap-2">
          <label className="sr-only" htmlFor="lang">Language</label>
          <div className="flex items-center gap-1 rounded-xl border border-line bg-white px-1.5 sm:px-2">
            <Languages size={16} className="hidden text-muted sm:block" aria-hidden />
            <select id="lang" value={lang} onChange={(e) => setLang(e.target.value as "en" | "hi")} className="h-10 bg-transparent text-sm font-semibold text-navy-900 outline-none">
              <option value="en">English</option>
              <option value="hi">हिन्दी</option>
            </select>
          </div>
          {user ? (
            <button onClick={logout} className="btn btn-ghost hidden text-sm sm:inline-flex">{t("signout")}</button>
          ) : (
            <Link href="/login" className="btn btn-ghost hidden text-sm sm:inline-flex"><LogIn size={16} aria-hidden />{t("signin")}</Link>
          )}
          <button className="btn btn-ghost !px-3 2xl:hidden" aria-expanded={open} aria-controls="mobile-nav" onClick={() => setOpen(!open)}>
            {open ? <X size={18} aria-hidden /> : <Menu size={18} aria-hidden />}<span className="sr-only sm:not-sr-only">{open ? t("close") : t("menu")}</span>
          </button>
        </div>
      </div>
      {open && (
        <nav id="mobile-nav" aria-label="Main mobile" className="border-t border-line bg-ivory px-4 pb-4 2xl:hidden">
          <ul className="grid gap-1 pt-2">
            {nav.map(([href, k]) => (
              <li key={href}><Link href={href} aria-current={active(href) ? "page" : undefined} className={`block rounded-lg px-3 py-3 font-semibold ${active(href) ? "bg-navy-900 text-white" : "text-navy-900 hover:bg-ivory-dark"}`}>{t(k)}</Link></li>
            ))}
            <li>{user ? <button onClick={logout} className="w-full rounded-lg px-3 py-3 text-left font-semibold text-navy-900 hover:bg-ivory-dark">{t("signout")}</button>
              : <Link href="/login" className="block rounded-lg px-3 py-3 font-semibold text-navy-900 hover:bg-ivory-dark">{t("signin")}</Link>}</li>
          </ul>
        </nav>
      )}
    </header>
  );
}
