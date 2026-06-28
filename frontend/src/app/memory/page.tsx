import { ComingSoon } from "@/shared/ui/ComingSoon";

export default function MemoryPage() {
  return (
    <ComingSoon
      title="Memory & Knowledge Graph"
      description="Persistent memory system with vector search, knowledge graph, and RAG-powered retrieval across your documents and conversations."
      version="Coming in V2"
      icon={
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="12" cy="12" r="3" />
          <circle cx="4" cy="8" r="2" />
          <circle cx="20" cy="8" r="2" />
          <circle cx="4" cy="16" r="2" />
          <circle cx="20" cy="16" r="2" />
          <path d="M9 10.5L6 9M15 10.5l3-1.5M9 13.5l-3 1.5M15 13.5l3 1.5" />
        </svg>
      }
    />
  );
}
