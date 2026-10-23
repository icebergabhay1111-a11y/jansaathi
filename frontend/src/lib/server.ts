// Server-side fetch for SSR pages (talks directly to the backend).
import "server-only";
import { cookies } from "next/headers";
import type { Lang } from "./i18n-dict";

const BACKEND = process.env.BACKEND_URL || "http://127.0.0.1:8000";

export async function serverGet<T>(path: string): Promise<{ data: T | null; status: number }> {
  try {
    const res = await fetch(`${BACKEND}/api${path}`, { next: { revalidate: 60 } });
    if (!res.ok) return { data: null, status: res.status };
    return { data: (await res.json()) as T, status: 200 };
  } catch {
    return { data: null, status: 0 };
  }
}

export async function serverLang(): Promise<Lang> {
  const c = await cookies();
  return c.get("js_lang")?.value === "hi" ? "hi" : "en";
}
