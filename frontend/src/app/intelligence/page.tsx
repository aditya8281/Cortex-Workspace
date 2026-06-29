import { ComingSoon } from "@/shared/ui/ComingSoon";

export default function IntelligencePage() {
  return (
    <ComingSoon
      title="Intelligence Hub"
      description="View and manage your AI's knowledge graph, vector search, RAG pipelines, and embedding stats."
      version="Coming in V2"
      icon={
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
      }
    />
  );
}
