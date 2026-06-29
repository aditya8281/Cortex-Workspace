import { ComingSoon } from "@/shared/ui/ComingSoon";

export default function DocsPage() {
  return (
    <ComingSoon
      title="Documentation"
      description="Browse CORTEX documentation, API references, integration guides, and architecture overviews."
      version="Coming in V2"
      icon={
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M4 19.5A2.5 2.5 0 016.5 17H20" />
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z" />
        </svg>
      }
    />
  );
}
