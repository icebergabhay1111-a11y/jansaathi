"use client";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "./api";
import { DICT, type Key, type Lang } from "./i18n-dict";

type User = { id: number; email: string; display_name: string | null; role: "user" | "editor" | "admin" };

type Ctx = {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (k: Key) => string;
  user: User | null;
  authLoading: boolean;
  refreshUser: () => Promise<void>;
  logout: () => Promise<void>;
};

const AppCtx = createContext<Ctx | null>(null);

export function Providers({ initialLang, children }: { initialLang: Lang; children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>(initialLang);
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const router = useRouter();

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    document.cookie = `js_lang=${l}; path=/; max-age=31536000; samesite=lax`;
    document.documentElement.lang = l;
    router.refresh(); // re-render server pages in the new language
  }, [router]);

  const refreshUser = useCallback(async () => {
    try {
      const r = await api<{ user: User | null }>("/auth/me");
      setUser(r.user);
    } catch {
      setUser(null);
    } finally {
      setAuthLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try { await api("/auth/logout", { method: "POST" }); } finally { setUser(null); router.push("/"); }
  }, [router]);

  useEffect(() => { refreshUser(); }, [refreshUser]);

  const tr = useCallback((k: Key) => DICT[lang][k] ?? DICT.en[k], [lang]);
  return <AppCtx.Provider value={{ lang, setLang, t: tr, user, authLoading, refreshUser, logout }}>{children}</AppCtx.Provider>;
}

export function useApp() {
  const c = useContext(AppCtx);
  if (!c) throw new Error("useApp outside Providers");
  return c;
}
