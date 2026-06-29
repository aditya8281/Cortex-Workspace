import { ComingSoon } from "@/shared/ui/ComingSoon";

export default function KnowledgePage() {
  return (
    <ComingSoon
      title="Knowledge Graph"
      description="Explore your knowledge graph, entity relationships, semantic connections, and memory clusters."
      version="Coming in V2"
      icon={
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="12" cy="5" r="2.5" />
          <circle cx="5" cy="19" r="2.5" />
          <circle cx="19" cy="19" r="2.5" />
          <line x1="12" y1="7.5" x2="5" y2="16.5" />
          <line x1="12" y1="7.5" x2="19" y2="16.5" />
          <line x1="7.5" y1="19" x2="16.5" y2="19" />
        </svg>
      }
    />
  );
}
