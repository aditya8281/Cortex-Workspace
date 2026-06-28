import { ComingSoon } from "@/shared/ui/ComingSoon";

export default function TasksPage() {
  return (
    <ComingSoon
      title="Tasks & Calendar"
      description="Task management with calendar integration. Break down projects, track deadlines, and sync with your schedule."
      version="Coming in V5"
      icon={
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2" />
          <rect x="9" y="3" width="6" height="4" rx="1" />
          <path d="M9 14l2 2 4-4" />
        </svg>
      }
    />
  );
}
