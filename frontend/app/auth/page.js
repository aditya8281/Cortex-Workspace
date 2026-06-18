/**
 * Auth page — Multi-step registration wizard + login.
 * Steps: Account → Profile → GitHub → Vault
 */
"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import {
  apiLogin,
  apiRegister,
  apiCheckUsername,
  apiConnectGitHub,
} from "../../src/shared/auth/cortexApi";
import Button from "../../src/shared/ui/Button";
import Input from "../../src/shared/ui/Input";
import Card from "../../src/shared/ui/Card";
import Steps from "../../src/shared/ui/Steps";
import PasswordStrength from "../../src/shared/ui/PasswordStrength";

const WIZARD_STEPS = ["Account", "Profile", "GitHub", "Vault"];

export default function AuthPage() {
  const router = useRouter();
  const { user, login, loading: authLoading } = useAuth();
  const [mode, setMode] = useState("login");
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authLoading && user) router.replace("/app");
  }, [user, authLoading, router]);

  // ── Fields ──
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [nickname, setNickname] = useState("");
  const [bio, setBio] = useState("");
  const [ghUsername, setGhUsername] = useState("");
  const [ghToken, setGhToken] = useState("");
  const [vaultPassword, setVaultPassword] = useState("");
  const [vaultConfirm, setVaultConfirm] = useState("");

  // ── Username validation ──
  const [usernameStatus, setUsernameStatus] = useState("");
  const [usernameMsg, setUsernameMsg] = useState("");
  const usernameTimer = useRef(null);

  const checkUsername = useCallback(async (val) => {
    const trimmed = val.trim();
    if (trimmed.length < 3) {
      setUsernameStatus("invalid");
      setUsernameMsg("At least 3 characters");
      return;
    }
    setUsernameStatus("checking");
    setUsernameMsg("");
    try {
      const res = await apiCheckUsername(trimmed);
      setUsernameStatus(res.available ? "available" : "taken");
      setUsernameMsg(res.message);
    } catch {
      setUsernameStatus("invalid");
      setUsernameMsg("Could not check username");
    }
  }, []);

  useEffect(() => {
    if (mode !== "register") return;
    clearTimeout(usernameTimer.current);
    if (!username.trim()) {
      setUsernameStatus("");
      setUsernameMsg("");
      return;
    }
    usernameTimer.current = setTimeout(() => checkUsername(username), 400);
    return () => clearTimeout(usernameTimer.current);
  }, [username, mode, checkUsername]);

  function switchMode(next) {
    setMode(next);
    setStep(0);
    setError("");
  }

  function validateStep(s) {
    setError("");
    if (s === 0) {
      if (!username.trim()) { setError("Username is required."); return false; }
      if (usernameStatus === "taken") { setError("Username is already taken."); return false; }
      if (usernameStatus === "invalid") { setError(usernameMsg || "Invalid username."); return false; }
      if (password.length < 8) { setError("Password must be at least 8 characters."); return false; }
      if (!/[a-zA-Z]/.test(password) || !/[0-9]/.test(password)) { setError("Password must contain at least one letter and one number."); return false; }
      if (password !== confirmPassword) { setError("Passwords do not match."); return false; }
      return true;
    }
    if (s === 1) {
      if (!fullName.trim()) { setError("Full name is required."); return false; }
      if (!nickname.trim()) { setError("Nickname is required."); return false; }
      return true;
    }
    if (s === 2) return true;
    if (s === 3) {
      if (vaultPassword.length < 8) { setError("Vault password must be at least 8 characters."); return false; }
      if (!/[a-zA-Z]/.test(vaultPassword) || !/[0-9]/.test(vaultPassword)) { setError("Vault password must contain at least one letter and one number."); return false; }
      if (vaultPassword !== vaultConfirm) { setError("Vault passwords do not match."); return false; }
      return true;
    }
    return true;
  }

  function handleNext() {
    if (!validateStep(step)) return;
    setStep((s) => Math.min(s + 1, WIZARD_STEPS.length - 1));
    setError("");
  }

  function handleBack() {
    setStep((s) => Math.max(s - 1, 0));
    setError("");
  }

  async function handleRegister() {
    if (!validateStep(step)) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiRegister({
        username: username.trim(),
        password,
        confirm_password: confirmPassword,
        full_name: fullName.trim(),
        nickname: nickname.trim(),
        bio: bio.trim() || undefined,
        vault_password: vaultPassword,
        personal_storage_path: "~/CortexVault",
      });
      login(data.access_token, data.user);
      if (ghUsername.trim() && ghToken.trim()) {
        try {
          await apiConnectGitHub(ghUsername.trim(), ghToken, data.access_token);
        } catch {}
      }
      router.replace("/app");
    } catch (err) {
      setError(err.message || "Registration failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleLogin(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await apiLogin({ username: username.trim(), password });
      login(data.access_token, data.user);
      router.replace("/app");
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  const isRegister = mode === "register";
  const isLastStep = step === WIZARD_STEPS.length - 1;

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-[400px] animate-fade-in overflow-hidden">
        {/* Brand */}
        <div className="text-center mb-6">
          <div className="flex justify-center mb-2">
            <div className="h-2 w-2 rounded-full bg-accent shadow-[0_0_12px_rgba(6,182,212,0.4)]" />
          </div>
          <h1 className="text-lg font-semibold text-text">Cortex</h1>
          <p className="text-xs text-text-muted mt-0.5">
            {isRegister
              ? `Step ${step + 1} of ${WIZARD_STEPS.length} — ${WIZARD_STEPS[step]}`
              : "Welcome back"}
          </p>
        </div>

        <Card className="p-5 overflow-hidden">
          {/* Tab toggle */}
          {step === 0 && (
            <div className="flex rounded-md bg-bg-surface p-0.5 mb-4">
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
          )}

          {/* Step progress */}
          {isRegister && (
            <div className="mb-4">
              <Steps steps={WIZARD_STEPS} current={step} />
            </div>
          )}

          {/* ── LOGIN ── */}
          {!isRegister && (
            <form onSubmit={handleLogin} className="grid gap-3">
              <Input
                label="Username"
                placeholder="operator-01"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
              />
              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
              {error && (
                <p className="text-xs text-error bg-error-muted rounded-md px-3 py-2">
                  {error}
                </p>
              )}
              <Button type="submit" loading={loading} className="w-full mt-1">
                Sign in
              </Button>
            </form>
          )}

          {/* ── REGISTER WIZARD ── */}
          {isRegister && (
            <>
              {/* Step 0: Account */}
              {step === 0 && (
                <div className="grid gap-3 animate-fade-in">
                  <div>
                    <Input
                      label="Username"
                      placeholder="operator-01"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      autoComplete="username"
                      error={
                        usernameStatus === "taken" || usernameStatus === "invalid"
                          ? usernameMsg
                          : undefined
                      }
                      className={
                        usernameStatus === "available"
                          ? "border-success/50"
                          : usernameStatus === "taken"
                          ? "border-error/50"
                          : usernameStatus === "checking"
                          ? "border-accent/30"
                          : ""
                      }
                      required
                    />
                    {usernameStatus === "available" && (
                      <p className="text-[11px] text-success mt-1 flex items-center gap-1">
                        <svg className="h-3 w-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                        {usernameMsg}
                      </p>
                    )}
                    {usernameStatus === "checking" && (
                      <p className="text-[11px] text-text-muted mt-1 flex items-center gap-1">
                        <svg className="animate-spin h-3 w-3 shrink-0" viewBox="0 0 24 24" fill="none">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Checking availability…
                      </p>
                    )}
                  </div>

                  <div>
                    <Input
                      label="Password"
                      type="password"
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      autoComplete="new-password"
                      required
                    />
                    <div className="mt-1">
                      <PasswordStrength password={password} />
                    </div>
                  </div>

                  <Input
                    label="Confirm password"
                    type="password"
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    autoComplete="new-password"
                    error={
                      confirmPassword && password !== confirmPassword
                        ? "Passwords do not match"
                        : undefined
                    }
                    required
                  />
                </div>
              )}

              {/* Step 1: Profile */}
              {step === 1 && (
                <div className="grid gap-3 animate-fade-in">
                  <Input
                    label="Full name"
                    placeholder="Ada Lovelace"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    autoComplete="name"
                    required
                  />
                  <Input
                    label="Nickname"
                    placeholder="ada"
                    value={nickname}
                    onChange={(e) => setNickname(e.target.value)}
                    autoComplete="nickname"
                    required
                  />
                  <div className="grid gap-1">
                    <label className="text-xs font-medium text-text-secondary">
                      Bio <span className="text-text-muted">(optional)</span>
                    </label>
                    <textarea
                      value={bio}
                      onChange={(e) => setBio(e.target.value)}
                      placeholder="Tell us about yourself…"
                      rows={2}
                      className="w-full rounded-md bg-bg-surface border border-border px-3 py-2 text-sm text-text placeholder:text-text-muted outline-none transition-colors resize-none focus:border-accent/40 focus:ring-1 focus:ring-accent/20"
                    />
                  </div>
                </div>
              )}

              {/* Step 2: GitHub */}
              {step === 2 && (
                <div className="grid gap-3 animate-fade-in">
                  <div className="rounded-md bg-bg-surface border border-border p-3">
                    <div className="flex items-center gap-2.5 mb-3">
                      <div className="h-8 w-8 rounded-md bg-bg-elevated border border-border flex items-center justify-center shrink-0">
                        <svg className="h-4 w-4 text-text-secondary" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-text">Connect GitHub</p>
                        <p className="text-[11px] text-text-muted">Link your account</p>
                      </div>
                    </div>
                    <Input
                      label="GitHub username"
                      placeholder="octocat"
                      value={ghUsername}
                      onChange={(e) => setGhUsername(e.target.value)}
                      autoComplete="off"
                    />
                    <div className="mt-2">
                      <Input
                        label="Personal access token"
                        type="password"
                        placeholder="ghp_xxxxxxxxxxxx"
                        value={ghToken}
                        onChange={(e) => setGhToken(e.target.value)}
                        autoComplete="off"
                      />
                      <p className="text-[10px] text-text-muted mt-1">
                        <a
                          href="https://github.com/settings/tokens"
                          target="_blank"
                          rel="noreferrer"
                          className="text-accent hover:underline"
                        >
                          Generate one →
                        </a>
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setStep(3)}
                    className="text-xs text-text-muted hover:text-text transition-colors text-center"
                  >
                    Skip for now →
                  </button>
                </div>
              )}

              {/* Step 3: Vault */}
              {step === 3 && (
                <div className="grid gap-3 animate-fade-in">
                  <div className="rounded-md bg-accent-faint border border-accent/10 p-3">
                    <p className="text-[11px] text-text-secondary leading-relaxed">
                      The <span className="text-accent font-medium">vault password</span> encrypts
                      your private files. It is never used for login and cannot be recovered.
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
                  <div>
                    <PasswordStrength password={vaultPassword} />
                  </div>
                  <Input
                    label="Confirm vault password"
                    type="password"
                    placeholder="••••••••"
                    value={vaultConfirm}
                    onChange={(e) => setVaultConfirm(e.target.value)}
                    autoComplete="new-password"
                    error={
                      vaultConfirm && vaultPassword !== vaultConfirm
                        ? "Vault passwords do not match"
                        : undefined
                    }
                    required
                  />
                </div>
              )}

              {/* Error */}
              {error && (
                <p className="text-xs text-error bg-error-muted rounded-md px-3 py-2 mt-2">
                  {error}
                </p>
              )}

              {/* Navigation */}
              <div className="flex gap-3 mt-3">
                {step > 0 && (
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={handleBack}
                    className="flex-1"
                  >
                    Back
                  </Button>
                )}
                {isLastStep ? (
                  <Button
                    type="button"
                    loading={loading}
                    onClick={handleRegister}
                    className="flex-1"
                  >
                    Create account
                  </Button>
                ) : (
                  <Button
                    type="button"
                    onClick={handleNext}
                    className="flex-1"
                  >
                    Continue
                  </Button>
                )}
              </div>
            </>
          )}
        </Card>

        <p className="mt-3 text-center text-[10px] text-text-muted font-mono tracking-wider uppercase">
          Local-first · Private by default
        </p>
      </div>
    </div>
  );
}
