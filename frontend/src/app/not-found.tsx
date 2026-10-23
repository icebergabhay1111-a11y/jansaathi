import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-xl px-4 py-20 text-center">
      <h1 className="font-display text-4xl text-navy-900">Page not found</h1>
      <p className="mt-3 text-muted">This page does not exist or the record is not published.</p>
      <div className="mt-6 flex justify-center gap-3"><Link href="/" className="btn btn-primary">Go home</Link><Link href="/search?q=scheme" className="btn btn-ghost">Search</Link></div>
    </div>
  );
}
