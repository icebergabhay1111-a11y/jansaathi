import Link from "next/link";
import { notFound } from "next/navigation";
import { ExternalLink, FilePenLine, Phone, Siren } from "lucide-react";
import { ItemActions } from "@/components/ItemActions";
import { FreshnessNotice, List, Section, SourcesList } from "@/components/ui";
import { serverGet, serverLang } from "@/lib/server";
import type { Freshness, Source, VStatus } from "@/lib/types";

type Guide = {
  slug: string; kind: string; title: string; title_hi: string | null; summary: string;
  law_basis: { law: string; type: string }[]; qualifications: string[]; steps: string[];
  authorities: { name: string; url?: string; phone?: string }[]; documents: string[]; time_limits: string | null;
  escalation: string[]; emergency: boolean; sources: Source[]; last_verified: string | null; verification_status: VStatus;
  verification_note: string | null; freshness: Freshness;
};

const TYPE_LABEL: Record<string, string> = { constitutional: "Constitutional right", statutory: "Statutory (law passed by legislature)", administrative: "Administrative / policy", contractual: "Contractual", judicial: "Court decision" };

export async function generateMetadata({ params }: PageProps<"/guides/[slug]">) {
  const { slug } = await params;
  const { data } = await serverGet<Guide>(`/guides/${slug}`);
  return { title: data?.title || "Guide" };
}

export default async function GuidePage({ params }: PageProps<"/guides/[slug]">) {
  const { slug } = await params;
  const [{ data: g, status }, lang] = await Promise.all([serverGet<Guide>(`/guides/${slug}`), serverLang()]);
  if (status === 404) notFound();
  if (!g) return <p role="alert" className="mx-auto max-w-3xl p-10">We could not load this guide right now. Please try again shortly.</p>;
  const isComplaint = g.kind === "complaint";

  return (
    <article className="mx-auto max-w-5xl px-4 py-10">
      <nav aria-label="Breadcrumb" className="text-sm text-muted">
        <Link href={isComplaint ? "/complaints" : "/rights"} className="hover:underline">{isComplaint ? "Complaints & legal aid" : "Know your rights"}</Link> / <span>{g.title}</span>
      </nav>
      {g.emergency && (
        <p role="alert" className="mt-4 flex items-center gap-2 rounded-xl bg-red-50 p-4 font-semibold text-red-900"><Siren size={20} aria-hidden />In immediate danger? Call 112. For online money fraud, call 1930 right away.</p>
      )}
      <h1 className="mt-3 font-display text-3xl font-bold text-navy-900 sm:text-4xl">{lang === "hi" && g.title_hi ? g.title_hi : g.title}</h1>
      {lang === "hi" && g.title_hi && <p className="text-muted">{g.title}</p>}
      <p className="mt-4 text-lg">{g.summary}</p>
      <div className="mt-4"><ItemActions itemType="guide" slug={g.slug} /></div>

      <div className="mt-6 grid gap-5">
        <Section title="What the law says" id="law">
          <ul className="space-y-2">
            {g.law_basis.map((l) => <li key={l.law} className="flex flex-col gap-0.5 sm:flex-row sm:items-baseline sm:gap-3"><span className="shrink-0 rounded bg-navy-100 px-2 py-0.5 text-xs font-semibold text-navy-800">{TYPE_LABEL[l.type] || l.type}</span><span>{l.law}</span></li>)}
          </ul>
        </Section>
        <Section title="Facts that matter" id="qual"><List items={g.qualifications} /></Section>
        <Section title="Steps you can take" id="steps"><List items={g.steps} ordered /></Section>
        {g.documents.length > 0 && <Section title="Keep these ready" id="docs"><List items={g.documents} /></Section>}
        {g.time_limits && <Section title="Time limits" id="tl"><p>{g.time_limits}</p></Section>}
        <Section title="Where to go" id="auth">
          <ul className="space-y-3">
            {g.authorities.map((a) => (
              <li key={a.name} className="rounded-xl border border-line p-3">
                <p className="font-semibold text-navy-900">{a.name}</p>
                <div className="mt-1 flex flex-wrap gap-4 text-sm">
                  {a.url && <a href={a.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 font-semibold text-navy-700 underline">{new URL(a.url).hostname}<ExternalLink size={13} aria-hidden /></a>}
                  {a.phone && <a href={`tel:${a.phone}`} className="inline-flex items-center gap-1 font-semibold text-navy-700"><Phone size={13} aria-hidden />{a.phone}</a>}
                </div>
              </li>
            ))}
          </ul>
          {g.escalation.length > 0 && <><h3 className="mt-4 font-semibold">If unresolved, escalate to</h3><List items={g.escalation} /></>}
        </Section>
        <Link href={`/complaints?draft=${isComplaint ? "complaint" : g.slug === "guide-rti" ? "rti" : "complaint"}&topic=${encodeURIComponent(g.title)}`} className="btn btn-primary justify-self-start"><FilePenLine size={18} aria-hidden />Help me draft a letter</Link>
        <FreshnessNotice f={g.freshness} status={g.verification_status} note={g.verification_note} />
        <SourcesList sources={g.sources} lastVerified={g.last_verified} />
        <p className="text-sm text-muted">General legal information, not legal advice. JanSaathi does not submit complaints on your behalf.</p>
      </div>
    </article>
  );
}
