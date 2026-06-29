import { ComingSoon } from "@/shared/ui/ComingSoon";

export default function ExecutionPage() {
  return (
    <ComingSoon
      title="Execution Dashboard"
      description="Monitor tool executions, workflow runs, agent actions, and execution history in real-time."
      version="Coming in V2"
      icon={
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M5 12h14" />
          <path d="M12 5l7 7-7 7" />
        </svg>
      }
    />
  );
}
