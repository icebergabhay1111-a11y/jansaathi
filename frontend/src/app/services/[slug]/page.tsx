import Link from "next/link";
import { notFound } from "next/navigation";
import { ItemActions } from "@/components/ItemActions";
import { FreshnessNotice, List, OfficialButton, Section, SourcesList, VerificationBadge } from "@/components/ui";
import { serverGet, serverLang } from "@/lib/server";
import type { Freshness, Source, VStatus } from "@/lib/types";

type Service = {
  slug: string; name: string; name_hi: string | null; summary: string; who_can_use: string; authority: string; level: string; online: string;
  in_person: string | null; documents: string[]; steps: string[]; fee: string | null; processing_time: string | null; tracking: string | null;
  correction: string | null; appeal: string | null; portal_url: string | null; help_channel: string | null; sources: Source[];
  last_verified: string | null; verification_status: VStatus; verification_note: string | null; freshness: Freshness;
};
const ONLINE: Record<string, string> = { yes: "Available online", partial: "Apply online; an in-person visit may be needed", no: "In person only", varies: "Varies by state" };

export async function generateMetadata({ params }: PageProps<"/services/[slug]">) {
  const { slug } = await params;
  const { data } = await serverGet<Service>(`/services/${slug}`);
  return { title: data?.name || "Service" };
}

export default async function ServicePage({ params }: PageProps<"/services/[slug]">) {
  const { slug } = await params;
  const [{ data: s, status }, lang] = await Promise.all([serverGet<Service>(`/services/${slug}`), serverLang()]);
  if (status === 404) notFound();
  if (!s) return <p role="alert" className="mx-auto max-w-3xl p-10">We could not load this service right now. Please try again shortly.</p>;
  const notDoc = "Not documented in our records — check the official portal.";

  return (
    <article className="mx-auto max-w-5xl px-4 py-10">
      <nav aria-label="Breadcrumb" className="text-sm text-muted"><Link href="/services" className="hover:underline">Services</Link> / <span>{s.name}</span></nav>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
        <span className="rounded-full bg-navy-900 px-2.5 py-0.5 font-semibold uppercase tracking-wide text-white">{s.level === "state" ? "State government service" : "Central government service"}</span>
        <VerificationBadge status={s.verification_status} freshness={s.freshness.state} />
      </div>
      <h1 className="mt-3 font-display text-3xl font-bold text-navy-900 sm:text-4xl">{lang === "hi" && s.name_hi ? s.name_hi : s.name}</h1>
      <p className="mt-1 font-semibold text-muted">{s.authority}</p>
      <p className="mt-4 text-lg">{s.summary}</p>
      <div className="mt-5 flex flex-wrap gap-3">{s.portal_url && <OfficialButton href={s.portal_url}>Go to official portal</OfficialButton>}</div>
      <p className="mt-2 text-sm text-muted">JanSaathi does not issue certificates or process applications. You apply directly with the authority.</p>
      <div className="mt-4"><ItemActions itemType="service" slug={s.slug} /></div>

      <div className="mt-6 grid gap-5">
        <FreshnessNotice f={s.freshness} status={s.verification_status} note={s.verification_note} />
        <div className="grid gap-5 md:grid-cols-2">
          <Section title="Who can use it" id="who"><p>{s.who_can_use || notDoc}</p></Section>
          <Section title="Online or in person?" id="on"><p>{ONLINE[s.online]}</p>{s.in_person && <p className="mt-1 text-sm text-muted">{s.in_person}</p>}</Section>
        </div>
        <Section title="Steps" id="steps"><List items={s.steps} ordered /></Section>
        <Section title="Documents" id="docs"><List items={s.documents} /></Section>
        <div className="grid gap-5 md:grid-cols-2">
          <Section title="Official fee" id="fee"><p>{s.fee || notDoc}</p></Section>
          <Section title="Processing time" id="time"><p>{s.processing_time || notDoc}</p></Section>
          <Section title="Tracking" id="track"><p>{s.tracking || notDoc}</p></Section>
          <Section title="Corrections & renewal" id="corr"><p>{s.correction || notDoc}</p></Section>
        </div>
        <Section title="Rejection, appeal & help" id="appeal">
          <p>{s.appeal || notDoc}</p>
          {s.help_channel && <p className="mt-2"><strong>Help:</strong> {s.help_channel}</p>}
          <Link href="/complaints" className="mt-2 inline-block font-semibold text-navy-700 hover:underline">Service delayed or denied? →</Link>
        </Section>
        <SourcesList sources={s.sources} lastVerified={s.last_verified} />
      </div>
    </article>
  );
}
