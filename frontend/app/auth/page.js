/**
 * Auth page — Combined login and register with tab toggle.
 * Clean, centered card design.
 */
"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { apiLogin, apiRegister } from "../../src/shared/auth/cortexApi";
import Button from "../../src/shared/ui/Button";
import Input from "../../src/shared/ui/Input";
import Card from "../../src/shared/ui/Card";

export default function AuthPage() {
  const router = useRouter();
  const { user, login, loading: authLoading } = useAuth();
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (!authLoading && user) router.replace("/app");
  }, [user, authLoading, router]);

  // Login fields
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  // Register-only fields
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [nickname, setNickname] = useState("");
  const [vaultPassword, setVaultPassword] = useState("");
  const [vaultConfirm, setVaultConfirm] = useState("");

  function switchMode(next) {
    setMode(next);
    setError("");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      if (mode === "login") {
        const data = await apiLogin({ username: username.trim(), password });
        login(data.access_token, data.user);
        router.replace("/app");
      } else {
        // Validate
        if (password !== confirmPassword) {
          setError("Passwords do not match.");
          setLoading(false);
          return;
        }
        if (password.length < 8) {
          setError("Password must be at least 8 characters.");
          setLoading(false);
          return;
        }
        if (vaultPassword.length < 8) {
          setError("Vault password must be at least 8 characters.");
          setLoading(false);
          return;
        }
        if (vaultPassword !== vaultConfirm) {
          setError("Vault passwords do not match.");
          setLoading(false);
          return;
        }

        const data = await apiRegister({
          username: username.trim(),
          password,
          confirm_password: confirmPassword,
          full_name: fullName.trim() || username.trim(),
          nickname: nickname.trim() || username.trim(),
          vault_password: vaultPassword,
          personal_storage_path: "~/CortexVault",
        });
        login(data.access_token, data.user);
        router.replace("/app");
      }
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  const isRegister = mode === "register";

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm animate-fade-in">
        {/* Brand */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-3">
            <div className="h-2 w-2 rounded-full bg-accent shadow-[0_0_12px_rgba(6,182,212,0.4)]" />
          </div>
          <h1 className="text-lg font-semibold text-text">Cortex</h1>
          <p className="text-xs text-text-muted mt-1">
            {isRegister ? "Create your account" : "Welcome back"}
          </p>
        </div>

        <Card className="p-6">
          {/* Tab toggle */}
          <div className="flex rounded-md bg-bg-surface p-0.5 mb-5">
            {["login", "register"].map((m) => (
              <button
                key={m}
                onClick={() => switchMode(m)}
                className={[
                  "flex-1 py-1.5 text-xs font-medium rounded-[5px] transition-all",
                  mode === m
                    ? "bg-bg-elevated text-text shadow-sm"
                    : "text-text-muted hover:text-text-secondary",
                ].join(" ")}
              >
                {m === "login" ? "Sign in" : "Register"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="grid gap-4">
            {/* Username — always shown */}
            <Input
              label="Username"
              placeholder="operator-01"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />

            {/* Password — always shown */}
            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={isRegister ? "new-password" : "current-password"}
              required
            />

            {/* Register-only fields */}
            {isRegister && (
              <>
                <Input
                  label="Confirm password"
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  autoComplete="new-password"
                  required
                />
                <hr className="border-border" />
                <Input
                  label="Full name"
                  placeholder="Ada Lovelace"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  autoComplete="name"
                />
                <Input
                  label="Nickname"
                  placeholder="ada"
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                  autoComplete="nickname"
                />
                <hr className="border-border" />
                <div className="rounded-md bg-accent-faint border border-accent/10 p-3">
                  <p className="text-[11px] text-text-secondary leading-relaxed">
                    The <span className="text-accent font-medium">vault password</span> is used
                    exclusively for encrypting your private files. It is never used for login.
                  </p>
                </div>
                <Input
                  label="Vault password"
                  type="password"
                  placeholder="••••••••"
                  value={vaultPassword}
                  onChange={(e) => setVaultPassword(e.target.value)}
                  autoComplete="new-password"
                  required
                />
                <Input
                  label="Confirm vault password"
                  type="password"
                  placeholder="••••••••"
                  value={vaultConfirm}
                  onChange={(e) => setVaultConfirm(e.target.value)}
                  autoComplete="new-password"
                  required
                />
              </>
            )}

            {/* Error */}
            {error && (
              <p className="text-xs text-error bg-error-muted rounded-md px-3 py-2">
                {error}
              </p>
            )}

            <Button type="submit" loading={loading} className="w-full mt-1">
              {isRegister ? "Create account" : "Sign in"}
            </Button>
          </form>
        </Card>

        <p className="mt-4 text-center text-[10px] text-text-muted font-mono tracking-wider uppercase">
          Local-first · Private by default
        </p>
      </div>
    </div>
  );
}
