import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Providers } from "@/lib/providers";
import { serverLang } from "@/lib/server";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";

export const metadata: Metadata = {
  title: { default: "JanSaathi — Know your rights, discover your benefits", template: "%s · JanSaathi" },
  description: "Independent, source-linked guide to Indian government schemes, constitutional rights, public services and grievance procedures. Not a government website.",
  manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = { themeColor: "#0b1f3a", width: "device-width", initialScale: 1 };

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const lang = await serverLang();
  return (
    <html lang={lang}>
      <body className="min-h-screen antialiased">
        <Providers initialLang={lang}>
          <Header />
          <main id="main" tabIndex={-1} className="outline-none">{children}</main>
          <Footer />
        </Providers>
      </body>
    </html>
  );
}
