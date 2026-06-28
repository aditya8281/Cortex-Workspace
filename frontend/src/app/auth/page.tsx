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
        body: JSON.stringify({ username, password }),
      });
      router.push("/");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="p-6">
      <div className="mb-6 text-center">
        <div className="mb-3 flex justify-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/12 text-accent">
            <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 0L16 8L8 16L0 8L8 0Z" />
            </svg>
          </div>
        </div>
        <h1 className="text-title font-semibold text-text-primary">Welcome back</h1>
        <p className="mt-1 text-sm text-text-secondary">Sign in to CORTEX</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          autoComplete="username"
        />
        <Input
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
        />

        {error && (
          <p className="text-sm text-danger">{error}</p>
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

      <p className="mt-4 text-center text-sm text-text-muted">
        No account?{" "}
        <Link href="/auth/register" className="text-accent hover:text-accent/80 transition-colors duration-150">
          Create one
        </Link>
      </p>
    </Card>
  );
}
