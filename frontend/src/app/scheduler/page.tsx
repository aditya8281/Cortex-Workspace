import { ComingSoon } from "@/shared/ui/ComingSoon";

export default function SchedulerPage() {
  return (
    <ComingSoon
      title="Scheduler & Automation"
      description="Schedule recurring tasks, set up automated workflows, and build research pipelines that run while you sleep."
      version="Coming in V4"
      icon={
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v5l3 3" />
        </svg>
      }
    />
  );
}
