export default function DashboardLoading() {
  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-8rem)]">
      <div className="flex flex-col items-center gap-3">
        <div className="h-6 w-6 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
        <p className="text-xs text-text-muted font-mono">Loading workspace...</p>
      </div>
    </div>
  );
}
