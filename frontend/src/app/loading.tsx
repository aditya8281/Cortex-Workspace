export default function Loading() {
  return (
    <div className="flex h-dvh items-center justify-center bg-void">
      <div className="flex flex-col items-center gap-3">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" />
        <p className="text-xs text-text-muted font-mono">Loading CORTEX…</p>
      </div>
    </div>
  );
}
