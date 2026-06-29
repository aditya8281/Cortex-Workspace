import { ComingSoon } from "@/shared/ui/ComingSoon";

export default function AppsPage() {
  return (
    <ComingSoon
      title="Apps & Integrations"
      description="Explore and install community apps, MCP servers, and third-party integrations."
      version="Coming in V6"
      icon={
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <rect x="3" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="3" width="7" height="7" rx="1" />
          <rect x="3" y="14" width="7" height="7" rx="1" />
          <rect x="14" y="14" width="7" height="7" rx="1" />
        </svg>
      }
    />
  );
}
