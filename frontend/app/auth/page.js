"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Badge, Button, Card, Input, Loader } from "../../src/shared/ui";
import { setSession, getSessionToken } from "../../src/shared/auth/session";

const bootLines = [
  "Initializing Cortex auth terminal...",
  "Mounting secure session layer...",
  "Verifying credentials gate...",
];

function EyeIcon({ off = false }) {
  if (off) {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="h-4 w-4 fill-none stroke-current stroke-2">
        <path d="M3 3l18 18" />
        <path d="M10.58 10.58a2 2 0 102.83 2.83" />
        <path d="M9.88 5.08A10.9 10.9 0 0112 5c5.5 0 9.5 4.5 10 7-0.18 0.9-0.65 1.96-1.38 3.02" />
        <path d="M6.23 6.23C3.61 8.03 2.19 10.4 2 12c.5 2.5 4.5 7 10 7 1.04 0 2.03-.12 2.96-.35" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="h-4 w-4 fill-none stroke-current stroke-2">
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function BootTrace() {
  const [visibleCount, setVisibleCount] = useState(1);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setVisibleCount((current) => Math.min(bootLines.length, current + 1));
    }, 650);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="grid gap-cortex-8 rounded-cortex border border-cortex-border bg-cortex-bg-secondary/70 p-cortex-12 font-mono text-xs text-cortex-text-muted">
      {bootLines.slice(0, visibleCount).map((line, index) => (
        <div key={line} className="flex items-center gap-cortex-8">
          <span className="text-cortex-cyan">[{String(index + 1).padStart(2, "0")}]</span>
          <span>{line}</span>
          {index === visibleCount - 1 ? <Loader className="ml-auto h-3.5 w-3.5" /> : null}
        </div>
      ))}
    </div>
  );
}

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [bootReady, setBootReady] = useState(false);

  useEffect(() => {
    const token = getSessionToken();
    if (token) {
      router.replace("/");
      return;
    }
    setBootReady(true);
  }, [router]);

  const actionLabel = useMemo(() => (mode === "login" ? "Authenticate" : "Register"), [mode]);
  const passwordInputType = showPassword ? "text" : "password";

  function togglePasswordVisibility() {
    setShowPassword((current) => !current);
  }

  async function submitForm(event) {
    event.preventDefault();
    const trimmedUsername = username.trim();
    const trimmedPassword = password.trim();
    const trimmedConfirmPassword = confirmPassword.trim();

    if (!trimmedUsername || !trimmedPassword) {
      setError("SYSTEM ERROR: Username and password are required.");
      return;
    }

    if (mode === "register") {
      if (!trimmedConfirmPassword) {
        setError("SYSTEM ERROR: Confirm password is required.");
        return;
      }
      if (trimmedPassword !== trimmedConfirmPassword) {
        setError("SYSTEM ERROR: Passwords do not match.");
        return;
      }
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(mode === "login" ? "/api/auth/login" : "/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username: trimmedUsername, password: trimmedPassword }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.error || data?.detail || "Authentication failed");
      }

      setSession(data.access_token, data.user);
      router.replace("/");
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Authentication failed");
    } finally {
      setLoading(false);
      setPassword("");
      setConfirmPassword("");
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-cortex-bg px-cortex-16 py-cortex-24">
      <Card className="w-full max-w-[520px] border-cortex-border bg-cortex-surface backdrop-blur-xl">
        <div className="grid gap-cortex-16">
          <div className="flex items-start justify-between gap-cortex-12">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-cyan">Security Gate</p>
              <h1 className="mt-cortex-8 text-2xl font-medium text-cortex-text">Cortex Terminal Login</h1>
            </div>
            <Badge variant={mode === "login" ? "cyan" : "neutral"}>{mode}</Badge>
          </div>

          {bootReady ? <BootTrace /> : null}

          <div className="grid grid-cols-2 gap-cortex-8">
            <Button
              type="button"
              variant={mode === "login" ? "primary" : "secondary"}
              size="sm"
              onClick={() => setMode("login")}
            >
              Login
            </Button>
            <Button
              type="button"
              variant={mode === "register" ? "primary" : "secondary"}
              size="sm"
              onClick={() => setMode("register")}
            >
              Register
            </Button>
          </div>

          <form className="grid gap-cortex-12" onSubmit={submitForm}>
            <label className="grid gap-cortex-8">
              <span className="font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">
                Username
              </span>
              <Input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="operator-01"
                autoComplete="username"
              />
            </label>

            <label className="grid gap-cortex-8">
              <span className="font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">
                Password
              </span>
              <div className="relative">
                <Input
                  type={passwordInputType}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="••••••••"
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                  className="pr-12"
                />
                <button
                  type="button"
                  onClick={togglePasswordVisibility}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-3 top-1/2 -translate-y-1/2 rounded-cortex border border-cortex-border bg-cortex-bg-secondary px-3 py-1 text-xs text-cortex-text-muted transition duration-cortex hover:border-cortex-cyan/35 hover:text-cortex-text"
                >
                  <span className="inline-flex items-center gap-1">
                    <EyeIcon off={!showPassword} />
                    <span>{showPassword ? "Hide" : "Show"}</span>
                  </span>
                </button>
              </div>
            </label>

            {mode === "register" ? (
              <label className="grid gap-cortex-8">
                <span className="font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">
                  Confirm password
                </span>
                <Input
                  type={passwordInputType}
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  placeholder="••••••••"
                  autoComplete="new-password"
                />
              </label>
            ) : null}

            {error ? (
              <div className="rounded-cortex border border-cortex-error/45 bg-cortex-error/10 px-cortex-12 py-cortex-12 font-mono text-sm text-cortex-error">
                {error}
              </div>
            ) : null}

            <div className="flex items-center justify-between gap-cortex-12">
              <span className="font-mono text-xs uppercase tracking-[0.12em] text-cortex-text-muted">
                {mode === "login" ? "Enter credentials" : "Create account"}
              </span>
              <Button type="submit" variant="primary" disabled={loading}>
                {loading ? "Processing..." : actionLabel}
              </Button>
            </div>
          </form>
        </div>
      </Card>
    </div>
  );
}
