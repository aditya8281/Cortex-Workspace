import { ComingSoon } from "@/shared/ui/ComingSoon";

export default function SearchPage() {
  return (
    <ComingSoon
      title="Universal Search"
      description="Full-text and semantic search across your entire knowledge base, conversations, and codebase. Hybrid retrieval with RRF ranking."
      version="Coming in V2"
      icon={
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="11" cy="11" r="7" />
          <path d="M21 21l-4.35-4.35" />
        </svg>
      }
    />
  );
}
