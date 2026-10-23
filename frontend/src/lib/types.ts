export type VStatus = "verified" | "reviewed" | "needs_verification";
export type Freshness = { state: "fresh" | "stale" | "unverified"; review_due: string | null; message: string };
export type Source = { url: string; organisation: string; title: string; type: string; retrieved?: string };

export type Card = {
  kind: "scheme" | "right" | "guide" | "service";
  slug: string;
  title: string;
  title_hi?: string | null;
  summary: string;
  summary_hi?: string | null;
  verification_status: VStatus;
  freshness: Freshness["state"];
  last_verified: string | null;
  categories?: string[];
  level?: string;
  states?: string[];
  ministry?: string;
  benefit_type?: string;
  article?: string;
  group?: string;
  applies_to?: string;
  authority?: string;
  online?: string;
  portal_url?: string;
  popular?: boolean;
  guide_kind?: string;
  emergency?: boolean;
  why?: string[];
  application_window?: string;
};

export type Paged<T> = { items: T[]; total: number; page: number; pages: number; size: number };

export type Meta = {
  states: string[];
  categories: { id: string; en: string; hi: string; count: number }[];
  languages: { code: string; name: string; status: string }[];
  ai_configured: boolean;
  labels: Record<string, string>;
  verification_counts: Record<string, number>;
  coverage_note: string;
};

export const hrefFor = (c: Pick<Card, "kind" | "slug">) =>
  c.kind === "scheme" ? `/schemes/${c.slug}` : c.kind === "right" ? `/rights/${c.slug}` : c.kind === "service" ? `/services/${c.slug}` : `/guides/${c.slug}`;
