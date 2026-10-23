// Original mark: two figures under a sheltering arc (companion/"saathi"). Deliberately not a government emblem.
export function Logo({ className = "h-9 w-9" }: { className?: string }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden>
      <rect width="40" height="40" rx="11" fill="#0b1f3a" />
      <path d="M8 22a12 12 0 0 1 24 0" fill="none" stroke="#e8862a" strokeWidth="3.2" strokeLinecap="round" />
      <circle cx="16" cy="21" r="3" fill="#fbf8f1" />
      <circle cx="24.5" cy="21" r="3" fill="#fbf8f1" />
      <path d="M11.5 32c.6-4 2.3-6 4.5-6s3.9 2 4.5 6M20 32c.6-4 2.3-6 4.5-6s3.9 2 4.5 6" fill="none" stroke="#1f7a4d" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}
