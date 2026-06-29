import { ComingSoon } from "@/shared/ui/ComingSoon";

export default function ComparePage() {
  return (
    <ComingSoon
      title="Model Comparison"
      description="Side-by-side comparison of models, benchmarks, capabilities, and performance metrics."
      version="Coming in V2"
      icon={
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <rect x="3" y="3" width="7" height="18" rx="1" />
          <rect x="14" y="9" width="7" height="12" rx="1" />
        </svg>
      }
    />
  );
}
