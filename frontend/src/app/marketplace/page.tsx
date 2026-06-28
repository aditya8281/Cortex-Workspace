import { ComingSoon } from "@/shared/ui/ComingSoon";

export default function MarketplacePage() {
  return (
    <ComingSoon
      title="Agent Marketplace"
      description="Discover, install, and share community-built agents and plugins. Extend CORTEX with specialized capabilities."
      version="Coming in V6"
      icon={
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M6 2L3 7v13a2 2 0 002 2h14a2 2 0 002-2V7l-3-5z" />
          <path d="M3 7h18M16 11a4 4 0 01-8 0" />
        </svg>
      }
    />
  );
}
