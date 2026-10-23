"use client";
import Link from "next/link";
import { Phone } from "lucide-react";
import { useApp } from "@/lib/providers";
import { Logo } from "./Logo";

export function Footer() {
  const { t } = useApp();
  return (
    <footer className="mt-16 bg-navy-950 text-navy-100">
      <div className="tricolor-rule" aria-hidden />
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 md:grid-cols-[1.4fr_1fr_1fr]">
        <div>
          <div className="flex items-center gap-2.5"><Logo /><span className="font-display text-xl font-bold text-white">JanSaathi</span></div>
          <p className="mt-3 max-w-md text-sm leading-relaxed text-navy-100/80">{t("disclaimer")}</p>
        </div>
        <div>
          <h2 className="font-display text-lg text-white">Emergency</h2>
          <ul className="mt-2 space-y-1.5 text-sm">
            <li className="flex items-center gap-2"><Phone size={14} aria-hidden /> 112 — Police, fire, ambulance</li>
            <li className="flex items-center gap-2"><Phone size={14} aria-hidden /> 1930 — Cyber financial fraud</li>
            <li className="flex items-center gap-2"><Phone size={14} aria-hidden /> 1098 — Childline</li>
            <li className="flex items-center gap-2"><Phone size={14} aria-hidden /> 15100 — NALSA free legal aid</li>
          </ul>
        </div>
        <nav aria-label="Footer">
          <h2 className="font-display text-lg text-white">JanSaathi</h2>
          <ul className="mt-2 space-y-1.5 text-sm">
            <li><Link className="underline-offset-2 hover:underline" href="/about">{t("footer_about")}</Link></li>
            <li><Link className="underline-offset-2 hover:underline" href="/about#privacy">{t("footer_privacy")}</Link></li>
            <li><Link className="underline-offset-2 hover:underline" href="/about#accessibility">{t("footer_access")}</Link></li>
            <li><Link className="underline-offset-2 hover:underline" href="/about#contact">{t("footer_contact")}</Link></li>
          </ul>
        </nav>
      </div>
      <p className="border-t border-white/10 px-4 py-4 text-center text-xs text-navy-100/60">Not an official Government of India service. Links open official government portals.</p>
    </footer>
  );
}
