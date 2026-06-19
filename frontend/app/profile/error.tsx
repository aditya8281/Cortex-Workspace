"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8">
      <h2 className="text-xl font-semibold text-text-primary">Something went wrong</h2>
      <p className="text-text-secondary">{error.message}</p>
      <button
        onClick={reset}
        className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-bg-void hover:bg-accent/90"
      >
        Try again
      </button>
    </div>
  );
}
