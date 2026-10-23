import Link from "next/link";
import { notFound } from "next/navigation";
import { MessageCircleQuestion } from "lucide-react";
import { ItemActions } from "@/components/ItemActions";
import { FreshnessNotice, List, ResultCard, Section, SourcesList } from "@/components/ui";
import { serverGet, serverLang } from "@/lib/server";
import type { Card, Freshness, Source, VStatus } from "@/lib/types";

type Right = {
  slug: string; article: string; part: string; group: string; title: string; title_hi: string | null; plain_en: string; plain_hi: string | null;
  protects: string; applies_to: string; against_whom: string | null; limitations: string[]; examples: string[]; situations: string[];
  remedies: string[]; authorities: string[]; sources: Source[]; last_verified: string | null; verification_status: VStatus;
  verification_note: string | null; freshness: Freshness; related_items: Card[];
};

export async function generateMetadata({ params }: PageProps<"/rights/[slug]">) {
  const { slug } = await params;
  const { data } = await serverGet<Right>(`/rights/${slug}`);
  return { title: data ? `${data.article === "Preamble" ? "Preamble" : `Article ${data.article}`}: ${data.title}` : "Rights" };
}

export default async function RightPage({ params }: PageProps<"/rights/[slug]">) {
  const { slug } = await params;
  const [{ data: a, status }, lang] = await Promise.all([serverGet<Right>(`/rights/${slug}`), serverLang()]);
  if (status === 404) notFound();
  if (!a) return <p role="alert" className="mx-auto max-w-3xl p-10">We could not load this provision right now. Please try again shortly.</p>;
  const label = a.article === "Preamble" ? "Preamble" : `Article ${a.article}`;

  return (
    <article className="mx-auto max-w-5xl px-4 py-10">
      <nav aria-label="Breadcrumb" className="text-sm text-muted"><Link href="/rights" className="hover:underline">Know your rights</Link> / <span>{label}</span></nav>
      <header className="mt-3">
        <p className="text-sm font-bold uppercase tracking-wider text-saffron-dark">{a.part} · {a.group}</p>
        <h1 className="mt-1 font-display text-3xl font-bold text-navy-900 sm:text-4xl">{label}: {a.title}</h1>
        {a.title_hi && <p className="mt-1 text-lg text-muted">{a.title_hi}</p>}
        <div className="mt-4"><ItemActions itemType="right" slug={a.slug} /></div>
      </header>

      <div className="mt-6 grid gap-5">
        <Section title="In plain language" id="plain">
          <p className="text-lg">{a.plain_en}</p>
          {a.plain_hi && (
            <div className={`mt-4 rounded-xl bg-ivory-dark p-4 ${lang === "hi" ? "order-first" : ""}`} lang="hi">
              <p className="text-lg">{a.plain_hi}</p>
              <p className="mt-2 text-xs text-muted">व्याख्यात्मक अनुवाद — संविधान का आधिकारिक हिन्दी पाठ नहीं।</p>
            </div>
          )}
        </Section>
        <div className="grid gap-5 md:grid-cols-3">
          <Section title="What it protects" id="prot"><p>{a.protects}</p></Section>
          <Section title="Who can use it" id="who"><p>{a.applies_to}</p></Section>
          <Section title="Against whom" id="against"><p>{a.against_whom || "—"}</p></Section>
        </div>
        <Section title="Important limits & exceptions" id="lim"><List items={a.limitations} /></Section>
        {a.examples.length > 0 && <Section title="Practical examples" id="ex"><List items={a.examples} /></Section>}
        {a.situations.length > 0 && <Section title="When this may be relevant" id="sit"><List items={a.situations} /></Section>}
        <Section title="What you can do" id="rem">
          <List items={a.remedies} />
          <p className="mt-3 text-sm text-muted">Whether a right has actually been violated depends on the facts. For a real situation, speak to a lawyer or a Legal Services Authority (NALSA helpline 15100).</p>
        </Section>
        {a.authorities.length > 0 && <Section title="Relevant authorities" id="auth"><List items={a.authorities} /></Section>}
        <FreshnessNotice f={a.freshness} status={a.verification_status} note={a.verification_note} />
        <SourcesList sources={a.sources} lastVerified={a.last_verified} />
        {a.related_items.length > 0 && (
          <section aria-labelledby="rel"><h2 id="rel" className="font-display text-2xl text-navy-900">Related</h2>
            <div className="mt-3 grid gap-4 sm:grid-cols-2">{a.related_items.map((r) => <ResultCard key={r.kind + r.slug} c={r} />)}</div></section>
        )}
        <Link href={`/ask?q=${encodeURIComponent(`Explain ${label} in simple words`)}`} className="btn btn-primary justify-self-start"><MessageCircleQuestion size={18} aria-hidden />Ask a follow-up question</Link>
      </div>
    </article>
  );
}
