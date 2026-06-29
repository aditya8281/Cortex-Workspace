"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { Card } from "@/shared/ui/Card";
import { apiFetch } from "@/shared/api/client";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await apiFetch("/auth/login", {
        method: "POST",
        body: { username, password },
      });
      // Full reload so AuthProvider re-mounts and fetches /me with new cookie.
      // router.push keeps the React tree — AuthProvider won't re-run its useEffect.
      window.location.href = "/";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="p-6">
      <div className="mb-6 text-center">
        <div className="mb-4 flex justify-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/12 text-accent">
            <svg width="24" height="24" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 0L16 8L8 16L0 8L8 0Z" />
            </svg>
          </div>
        </div>
        <h1 className="text-headline font-semibold text-text-primary">Welcome back</h1>
        <p className="mt-1.5 text-sm text-text-secondary">Sign in to CORTEX</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          autoComplete="username"
          placeholder="your-name"
        />
        <Input
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
          placeholder="Enter your password"
        />

        {error && (
          <div className="rounded-lg bg-danger/8 border border-danger/20 px-3 py-2">
            <p className="text-xs text-danger">{error}</p>
          </div>
        )}

        <Button
          type="submit"
          variant="primary"
          className="w-full"
          loading={loading}
        >
          Sign in
        </Button>
      </form>

      <div className="mt-5 pt-4 border-t border-border-subtle">
        <p className="text-center text-sm text-text-muted">
          No account?{" "}
          <Link href="/auth/register" className="text-accent hover:text-accent/80 font-medium transition-colors duration-150">
            Create one
          </Link>
        </p>
      </div>
    </Card>
  );
}
