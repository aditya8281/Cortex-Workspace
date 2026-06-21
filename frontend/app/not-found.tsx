import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-bg-void">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-text-primary">404</h1>
        <p className="mt-4 text-lg text-text-secondary">Page not found</p>
        <Link href="/app" className="mt-6 inline-block text-accent hover:text-accent-bright">
          Return to Dashboard
        </Link>
      </div>
    </div>
  );
}
