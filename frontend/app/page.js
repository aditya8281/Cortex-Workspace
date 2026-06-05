"use client";

// Minimal blank dashboard canvas (post-auth). Intentionally small — placeholder for future modules.
export default function Page() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-transparent">
      <div className="w-full max-w-3xl text-center p-8">
        <h2 className="text-lg font-medium text-cortex-text">Dashboard Canvas</h2>
        <p className="mt-2 text-sm text-cortex-text-muted">Blank workspace — add feature modules here.</p>
      </div>
    </main>
  );
}
