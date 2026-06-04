"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button, Input, Card } from "@/components/ui/base";
import { useAuth } from "@/hooks/useAuth";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      await login({ email, password });
      router.push("/dashboard");
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : typeof err === 'object' && err !== null && 'response' in err ? (err as any).response?.data?.message : 'Login failed';
      setError(errorMsg || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <Card className="w-full max-w-md">
        <h1 className="text-2xl font-bold mb-6">Cortex Login</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <p className="text-danger text-sm">{error}</p>}
          <Button type="submit" loading={loading} className="w-full">
            Login
          </Button>
        </form>
        <p className="text-center mt-4 text-gray-400">
          Don't have an account?{" "}
          <button
            onClick={() => router.push("/register")}
            className="text-primary hover:underline"
          >
            Register
          </button>
        </p>
      </Card>
    </div>
  );
}
