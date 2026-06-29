import { ComingSoon } from "@/shared/ui/ComingSoon";

export default function DeveloperPage() {
  return (
    <ComingSoon
      title="Developer Tools"
      description="API playground, webhook testing, MCP server management, and developer settings."
      version="Coming in V2"
      icon={
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <polyline points="16 18 22 12 16 6" />
          <polyline points="8 6 2 12 8 18" />
        </svg>
      }
    />
  );
}
