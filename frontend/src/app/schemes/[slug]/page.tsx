import Link from "next/link";
import { notFound } from "next/navigation";
import { ClipboardCheck } from "lucide-react";
import { ItemActions } from "@/components/ItemActions";
import { DocumentChecklist, type ChecklistItem } from "@/components/DocumentChecklist";
import { FreshnessNotice, List, OfficialButton, ResultCard, Section, SourcesList, VerificationBadge } from "@/components/ui";
import { serverGet, serverLang } from "@/lib/server";
import type { Card, Freshness, Source, VStatus } from "@/lib/types";

type Scheme = {
  slug: string; name: string; name_hi: string | null; summary: string; summary_hi: string | null; description: string; ministry: string;
  level: string; states: string[]; categories: string[]; beneficiaries: string[]; eligibility_text: string[]; exclusions: string[];
  documents: string[]; benefit_type: string; benefit_amount: string | null; application_steps: string[]; apply_url: string | null;
  info_url: string | null; opens_on: string | null; closes_on: string | null; renewal: string | null; selection_process: string | null;
  rejection_reasons: string[]; grievance: string | null; faqs: { q: string; a: string }[]; sources: Source[]; last_verified: string | null;
  verification_status: VStatus; verification_note: string | null; freshness: Freshness; application_window: string; related: Card[]; version: number;
  document_checklist: ChecklistItem[];
};

export async function generateMetadata({ params }: PageProps<"/schemes/[slug]">) {
  const { slug } = await params;
  const { data } = await serverGet<Scheme>(`/schemes/${slug}`);
  return { title: data?.name || "Scheme", description: data?.summary };
}

export default async function SchemePage({ params }: PageProps<"/schemes/[slug]">) {
  const { slug } = await params;
  const [{ data: s, status }, lang] = await Promise.all([serverGet<Scheme>(`/schemes/${slug}`), serverLang()]);
  if (status === 404) notFound();
  if (!s) return <p role="alert" className="mx-auto max-w-3xl p-10">We could not load this scheme right now. Please try again shortly.</p>;
  const hi = lang === "hi";

  return (
    <article className="mx-auto max-w-5xl px-4 py-10">
      <nav aria-label="Breadcrumb" className="text-sm text-muted"><Link href="/schemes" className="hover:underline">Schemes</Link> / <span>{s.name}</span></nav>
      <header className="mt-3">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="rounded-full bg-navy-900 px-2.5 py-0.5 font-semibold uppercase tracking-wide text-white">{s.level === "central" ? "Central scheme" : `State scheme · ${s.states.join(", ")}`}</span>
          <VerificationBadge status={s.verification_status} freshness={s.freshness.state} />
        </div>
        <h1 className="mt-3 font-display text-3xl font-bold text-navy-900 sm:text-4xl">{hi && s.name_hi ? s.name_hi : s.name}</h1>
        {hi && s.name_hi && <p className="text-muted">{s.name}</p>}
        <p className="mt-1 font-semibold text-muted">{s.ministry}</p>
        <p className="mt-4 text-lg">{hi && s.summary_hi ? s.summary_hi : s.summary}</p>
        {hi && s.summary_hi && <p className="mt-1 text-xs text-muted">हिन्दी सारांश व्याख्यात्मक अनुवाद है, आधिकारिक पाठ नहीं।</p>}
        {s.description && <p className="mt-2 text-muted">{s.description}</p>}
        <div className="mt-5 flex flex-wrap gap-3">
          {s.apply_url && <OfficialButton href={s.apply_url}>Apply on official portal</OfficialButton>}
          {s.info_url && s.info_url !== s.apply_url && <OfficialButton href={s.info_url} primary={!s.apply_url}>Official information</OfficialButton>}
          <Link href={`/eligibility?categories=${s.categories.join(",")}`} className="btn btn-ghost"><ClipboardCheck size={16} aria-hidden />Check my eligibility</Link>
        </div>
        <div className="mt-4"><ItemActions itemType="scheme" slug={s.slug} /></div>
      </header>

      <div className="mt-6"><FreshnessNotice f={s.freshness} status={s.verification_status} note={s.verification_note} /></div>
      {s.application_window === "closed_maybe" && <p role="alert" className="mt-3 rounded-xl bg-saffron-50 p-3 text-saffron-dark">The last recorded application period has ended ({s.closes_on}). It may have been extended — check the official portal.</p>}

      <div className="mt-6 grid gap-5">
        <Section title="Who may benefit" id="ben"><List items={s.beneficiaries} /></Section>
        <Section title="Eligibility criteria" id="eli">
          <List items={s.eligibility_text} />
          {s.exclusions.length > 0 && <><h3 className="mt-4 font-semibold text-navy-900">Not eligible / excluded</h3><List items={s.exclusions} /></>}
          <p className="mt-3 text-sm text-muted">Only the responsible authority can decide whether you are eligible.</p>
        </Section>
        <Section title="Benefits" id="bnf">
          <p className="font-semibold">{s.benefit_type}</p>
          {s.benefit_amount ? <p className="mt-1">{s.benefit_amount}</p> : <p className="mt-1 rounded-lg bg-saffron-50 p-3 text-sm text-saffron-dark">The benefit amount has not been verified by JanSaathi yet, so we do not show it. Please check the official website.</p>}
        </Section>
        <Section title="Document checklist — and where to get each one" id="docs">
          <DocumentChecklist slug={s.slug} items={s.document_checklist || s.documents.map((t) => ({ text: t, doc: null }))} />
        </Section>
        <Section title="How to apply" id="how">
          <List items={s.application_steps} ordered />
          {(s.opens_on || s.closes_on) && <p className="mt-3 text-sm">Application window: {s.opens_on || "—"} to {s.closes_on || "—"}</p>}
        </Section>
        {(s.renewal || s.selection_process) && (
          <Section title="Selection & renewal" id="sel">
            {s.selection_process && <p><strong>Selection:</strong> {s.selection_process}</p>}
            {s.renewal && <p className="mt-2"><strong>Renewal:</strong> {s.renewal}</p>}
          </Section>
        )}
        {s.rejection_reasons.length > 0 && <Section title="Common reasons for rejection (documented)" id="rej"><List items={s.rejection_reasons} /></Section>}
        {s.grievance && <Section title="Grievances & appeals" id="grv"><p>{s.grievance}</p><Link className="mt-2 inline-block font-semibold text-navy-700 hover:underline" href="/complaints">Prepare a complaint →</Link></Section>}
        {s.faqs.length > 0 && (
          <Section title="Frequently asked questions" id="faq">
            {s.faqs.map((f) => <details key={f.q} className="border-b border-line py-2"><summary className="cursor-pointer font-semibold">{f.q}</summary><p className="mt-1">{f.a}</p></details>)}
          </Section>
        )}
        <SourcesList sources={s.sources} lastVerified={s.last_verified} />
        {s.related.length > 0 && (
          <section aria-labelledby="rel">
            <h2 id="rel" className="font-display text-2xl text-navy-900">Related schemes</h2>
            <div className="mt-3 grid gap-4 sm:grid-cols-2">{s.related.map((r) => <ResultCard key={r.slug} c={r} />)}</div>
          </section>
        )}
        <p className="text-xs text-muted">Record version {s.version}. JanSaathi is not a government website.</p>
      </div>
    </article>
  );
}
