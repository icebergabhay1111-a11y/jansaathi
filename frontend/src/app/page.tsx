import Link from "next/link";
import { ArrowRight, BookOpenCheck, ClipboardCheck, FileSearch, Landmark, MapPin, MessageCircleQuestion, Mic, Scale, ShieldCheck } from "lucide-react";
import { HomeSearch } from "@/components/HomeSearch";
import { QuickCards } from "@/components/QuickCards";
import { serverGet, serverLang } from "@/lib/server";
import { t } from "@/lib/i18n-dict";
import type { Card, Meta, Paged } from "@/lib/types";
import { hrefFor } from "@/lib/types";

export default async function Home() {
  const lang = await serverLang();
  const [{ data: meta }, { data: services }, { data: updates }, { data: state }] = await Promise.all([
    serverGet<Meta>("/meta"),
    serverGet<Paged<Card>>("/services?size=8"),
    serverGet<{ items: (Card & { note?: string })[] }>("/updates"),
    serverGet<Paged<Card>>("/schemes?level=state&size=6"),
  ]);
  const backendDown = !meta;
  const cats = (meta?.categories || []).filter((c) => c.count > 0);
  const popular = (services?.items || []).filter((s) => s.popular).slice(0, 8);
  const tr = (k: Parameters<typeof t>[1]) => t(lang, k);

  return (
    <>
      <section className="hero-bg text-white">
        <div className="mx-auto grid max-w-7xl gap-10 px-4 pb-16 pt-12 lg:grid-cols-[1.25fr_1fr] lg:pt-20">
          <div>
            <p className="mb-4 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-sm text-white/90 ring-1 ring-white/15">
              <ShieldCheck size={15} aria-hidden /> Every answer linked to its official source
            </p>
            <h1 className="font-display text-4xl font-bold leading-tight sm:text-5xl lg:text-6xl">{tr("hero_title")}</h1>
            <p className="mt-4 max-w-2xl text-lg text-white/85">{tr("hero_sub")}</p>
            <div className="mt-8 max-w-2xl"><HomeSearch /></div>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/eligibility" className="btn btn-saffron"><ClipboardCheck size={18} aria-hidden />{tr("cta_schemes")}</Link>
              <Link href="/rights" className="btn border border-white/30 text-white hover:bg-white/10"><Scale size={18} aria-hidden />{tr("cta_rights")}</Link>
            </div>
          </div>
          <Link href="/ask" className="group self-end rounded-3xl bg-white/[.06] p-6 ring-1 ring-white/15 backdrop-blur transition hover:bg-white/[.1]">
            <div className="flex items-center gap-3">
              <span className="grid h-11 w-11 place-items-center rounded-xl bg-saffron text-navy-950"><MessageCircleQuestion size={22} aria-hidden /></span>
              <div><p className="font-display text-2xl">{tr("cta_ask")}</p><p className="text-sm text-white/70">Answers drawn only from JanSaathi&apos;s reviewed records</p></div>
            </div>
            <ul className="mt-5 space-y-2 text-[15px] text-white/85">
              <li>“I am a student from Uttar Pradesh. What scholarships should I look at?”</li>
              <li>“मेरी पेंशन कई महीनों से रुकी है। क्या करूँ?”</li>
              <li>“What protections apply if I am arrested?”</li>
            </ul>
            <span className="mt-5 inline-flex items-center gap-1 font-semibold text-saffron">Start a conversation <ArrowRight size={16} className="transition group-hover:translate-x-1" aria-hidden /></span>
          </Link>
        </div>
      </section>

      <div className="mx-auto max-w-7xl space-y-16 px-4 py-14">
        {backendDown && <p role="alert" className="rounded-xl bg-red-50 p-4 text-red-900">We could not reach the JanSaathi data service. Some sections are unavailable — please try again shortly.</p>}

        <section aria-labelledby="pop">
          <div className="flex items-end justify-between gap-4">
            <h2 id="pop" className="font-display text-3xl text-navy-900">{tr("popular_services")}</h2>
            <Link href="/services" className="font-semibold text-navy-700 hover:underline">{tr("view_all")} →</Link>
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {popular.map((s) => (
              <Link key={s.slug} href={hrefFor(s)} className="card card-hover flex items-start gap-3 p-4">
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-navy-100 text-navy-800"><FileSearch size={19} aria-hidden /></span>
                <span><span className="block font-semibold leading-snug text-navy-900">{lang === "hi" && s.title_hi ? s.title_hi : s.title}</span><span className="text-xs text-muted">{s.authority}</span></span>
              </Link>
            ))}
          </div>
        </section>

        <section aria-labelledby="qh">
          <div className="flex items-end justify-between gap-4">
            <h2 id="qh" className="font-display text-3xl text-navy-900">{lang === "hi" ? "तुरंत मदद — अपने अधिकार जानें" : "Know your rights — quick help"}</h2>
            <Link href="/rights" className="font-semibold text-navy-700 hover:underline">{tr("view_all")} →</Link>
          </div>
          <div className="mt-5"><QuickCards compact /></div>
        </section>

        <section aria-labelledby="near" className="grid gap-4 md:grid-cols-2">
          <Link href="/offices" className="card card-hover flex items-start gap-4 p-6">
            <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-leaf-50 text-leaf-dark"><MapPin size={22} aria-hidden /></span>
            <span><span id="near" className="block font-display text-2xl text-navy-900">{lang === "hi" ? "नज़दीकी कार्यालय खोजें" : "Find a nearby office"}</span>
              <span className="text-muted">{lang === "hi" ? "CSC, ई-सेवा केंद्र, तहसील, पंचायत और डाकघर — दूरी और रास्ते के साथ।" : "CSC, e-Sevai centres, taluk/tehsil, panchayat and post offices — with distance and directions."}</span></span>
          </Link>
          <Link href="/ask" className="card card-hover flex items-start gap-4 p-6">
            <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-saffron-50 text-saffron-dark"><Mic size={22} aria-hidden /></span>
            <span><span className="block font-display text-2xl text-navy-900">{lang === "hi" ? "बोलकर पूछें" : "Ask by voice"}</span>
              <span className="text-muted">{lang === "hi" ? "हिन्दी, तमिल या अंग्रेज़ी में बोलें — टाइप करने की ज़रूरत नहीं।" : "Speak in Hindi, Tamil or English — no typing needed."}</span></span>
          </Link>
        </section>

        <section aria-labelledby="cat">
          <h2 id="cat" className="font-display text-3xl text-navy-900">{tr("browse_category")}</h2>
          <div className="mt-5 flex flex-wrap gap-2">
            {cats.map((c) => (
              <Link key={c.id} href={`/schemes?category=${c.id}`} className="rounded-full border border-line bg-white px-4 py-2 font-semibold text-navy-900 hover:border-navy-700">
                {lang === "hi" ? c.hi : c.en} <span className="text-muted">· {c.count}</span>
              </Link>
            ))}
          </div>
          <p className="mt-3 text-sm text-muted">{tr("coverage_warning")}</p>
        </section>

        <div className="grid gap-8 lg:grid-cols-2">
          <section aria-labelledby="st" className="card p-6">
            <h2 id="st" className="font-display text-2xl text-navy-900">{tr("state_specific")}</h2>
            <p className="mt-1 text-sm text-muted">Certificates, ration cards and land records are issued by state governments. We currently list these state-run schemes:</p>
            <ul className="mt-4 space-y-2">
              {(state?.items || []).map((s) => <li key={s.slug}><Link className="font-semibold text-navy-700 hover:underline" href={hrefFor(s)}>{s.title}</Link> <span className="text-sm text-muted">({s.states?.join(", ")})</span></li>)}
            </ul>
            <Link href="/services?level=state" className="mt-4 inline-block font-semibold text-navy-700 hover:underline">State-run services →</Link>
          </section>
          <section aria-labelledby="up" className="card p-6">
            <h2 id="up" className="font-display text-2xl text-navy-900">{tr("updates")}</h2>
            <ul className="mt-4 divide-y divide-line">
              {(updates?.items || []).map((u) => (
                <li key={u.slug} className="py-2.5">
                  <Link className="font-semibold text-navy-900 hover:underline" href={hrefFor(u)}>{u.title}</Link>
                  <p className="text-xs text-muted">{u.verification_status === "verified" ? "Verified" : "Reviewed"} {u.last_verified}{u.note ? ` — ${u.note}` : ""}</p>
                </li>
              ))}
            </ul>
          </section>
        </div>

        <section aria-labelledby="how">
          <h2 id="how" className="font-display text-3xl text-navy-900">{tr("how_it_works")}</h2>
          <ol className="mt-6 grid gap-4 md:grid-cols-3">
            {[
              [ClipboardCheck, "Tell us your situation", "Answer a few questions — only the ones that matter. Sensitive questions are optional and explained."],
              [BookOpenCheck, "See what may apply", "We compare your answers with documented eligibility rules and explain every match and gap."],
              [Landmark, "Take the official step", "Apply, complain or request information on the real government portal. We never submit on your behalf."],
            ].map(([Icon, title, body], i) => {
              const I = Icon as typeof ClipboardCheck;
              return (
                <li key={i} className="card p-6">
                  <span className="grid h-11 w-11 place-items-center rounded-xl bg-saffron-50 text-saffron-dark"><I size={20} aria-hidden /></span>
                  <p className="mt-3 font-display text-xl text-navy-900">{i + 1}. {title as string}</p>
                  <p className="mt-1 text-muted">{body as string}</p>
                </li>
              );
            })}
          </ol>
        </section>

        <section aria-labelledby="tr" className="card grid gap-6 p-6 md:grid-cols-[1fr_1.3fr]">
          <div>
            <h2 id="tr" className="font-display text-3xl text-navy-900">{tr("transparency")}</h2>
            <p className="mt-2 text-muted">Every record shows its source and one of three labels. We never hide which is which.</p>
            <Link href="/about" className="mt-4 inline-block font-semibold text-navy-700 hover:underline">Read our sources & limitations →</Link>
          </div>
          <dl className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-leaf-50 p-4"><dt className="font-semibold text-leaf-dark">Verified · {meta?.verification_counts?.verified ?? 0}</dt><dd className="mt-1 text-sm text-ink/80">Confirmed against an official document on the date shown.</dd></div>
            <div className="rounded-xl bg-navy-100 p-4"><dt className="font-semibold text-navy-800">Reviewed · {meta?.verification_counts?.reviewed ?? 0}</dt><dd className="mt-1 text-sm text-ink/80">Prepared from authoritative sources and cross-checked; re-confirm before acting.</dd></div>
            <div className="rounded-xl bg-saffron-50 p-4"><dt className="font-semibold text-saffron-dark">Needs verification · {meta?.verification_counts?.needs_verification ?? 0}</dt><dd className="mt-1 text-sm text-ink/80">Official source identified, details not yet confirmed. Amounts are withheld.</dd></div>
          </dl>
        </section>
      </div>
    </>
  );
}
