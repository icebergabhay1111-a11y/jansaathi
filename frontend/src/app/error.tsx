"use client";
export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <div role="alert" className="mx-auto max-w-xl px-4 py-20 text-center">
      <h1 className="font-display text-3xl text-navy-900">Something went wrong</h1>
      <p className="mt-3 text-muted">Please try again. If the problem continues, the data service may be temporarily unavailable.</p>
      <button onClick={reset} className="btn btn-primary mt-6">Try again</button>
    </div>
  );
}
