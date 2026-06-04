import { Card, Spinner } from "@/components/ui/base";

export function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="space-y-4">
        <Spinner />
        <p className="text-center text-gray-400">Loading...</p>
      </div>
    </div>
  );
}

export function SectionLoader() {
  return (
    <div className="flex items-center justify-center py-8">
      <Spinner />
    </div>
  );
}

export function SkeletonCard() {
  return (
    <Card className="animate-pulse">
      <div className="space-y-4">
        <div className="h-4 bg-surface rounded w-3/4"></div>
        <div className="h-4 bg-surface rounded w-1/2"></div>
        <div className="h-4 bg-surface rounded w-2/3"></div>
      </div>
    </Card>
  );
}

export function SkeletonTable() {
  return (
    <div className="space-y-2">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="h-12 bg-surface rounded animate-pulse"></div>
      ))}
    </div>
  );
}
