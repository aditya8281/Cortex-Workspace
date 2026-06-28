import { ComingSoon } from "@/shared/ui/ComingSoon";

export default function VaultPage() {
  return (
    <ComingSoon
      title="Encrypted Vault"
      description="Fernet-encrypted per-user file storage for sensitive documents, API keys, and private data. Zero-knowledge architecture."
      version="Coming in V2"
      icon={
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <rect x="3" y="11" width="18" height="11" rx="2" />
          <path d="M7 11V7a5 5 0 0110 0v4" />
          <circle cx="12" cy="16" r="1" />
        </svg>
      }
    />
  );
}
