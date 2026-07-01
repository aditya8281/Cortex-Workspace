"use client";

export default function MemoryPage() {
  return (
    <div className="flex h-dvh items-center justify-center bg-bg-base">
      <div className="text-center">
        <svg
          width="24" height="24" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" strokeWidth="1.5"
          className="mx-auto mb-4 text-text-muted"
        >
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
        <p className="text-headline font-semibold text-text-primary">Memory</p>
        <p className="mt-1 text-sm text-text-muted">Coming soon</p>
      </div>
    </div>
  );
}
