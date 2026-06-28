import { ComingSoon } from "@/shared/ui/ComingSoon";

export default function NotesPage() {
  return (
    <ComingSoon
      title="Notes & Documents"
      description="Rich text notes and document management. Write, organize, and connect your ideas across the knowledge graph."
      version="Coming in V5"
      icon={
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
          <path d="M14 2v6h6M8 13h8M8 17h6" />
        </svg>
      }
    />
  );
}
