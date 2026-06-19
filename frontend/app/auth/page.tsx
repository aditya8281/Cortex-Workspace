"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { apiLogin, apiRegister, apiCheckUsername, apiConnectGitHub } from "../../src/shared/auth/cortexApi";
import Button from "../../src/shared/ui/Button";
import Input from "../../src/shared/ui/Input";
import Card from "../../src/shared/ui/Card";
import Steps from "../../src/shared/ui/Steps";
import PasswordStrength from "../../src/shared/ui/PasswordStrength";

const WIZARD_STEPS = ["Account", "Profile", "GitHub", "Vault"] as const;

type Mode = "login" | "register";
type UsernameStatus = "" | "invalid" | "checking" | "available" | "taken";

export default function AuthPage() {
  const router = useRouter();
  const { user, login, loading: authLoading } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authLoading && user) router.replace("/app");
  }, [user, authLoading, router]);

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
  const [storageRoot, setStorageRoot] = useState("~/CortexData");
  const [storageCustom, setStorageCustom] = useState(false);

  const effectiveStorageRoot = (() => {
    if (storageCustom) return storageRoot;
    if (username.trim() && (storageRoot === "~/CortexData" || storageRoot.startsWith("~/CortexData/"))) {
      return `~/CortexData/${username.trim()}`;
    }
    return storageRoot;
  })();

  const [usernameStatus, setUsernameStatus] = useState<UsernameStatus>("");
  const [usernameMsg, setUsernameMsg] = useState("");
  const usernameTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const checkUsername = useCallback(async (val: string) => {
    const trimmed = val.trim();
    if (trimmed.length < 3) { setUsernameStatus("invalid"); setUsernameMsg("At least 3 characters"); return; }
    setUsernameStatus("checking"); setUsernameMsg("");
    try {
      const res = await apiCheckUsername(trimmed);
      setUsernameStatus(res.available ? "available" : "taken");
      setUsernameMsg(res.message);
    } catch {
      setUsernameStatus("invalid"); setUsernameMsg("Could not check username");
    }
  }, []);

  useEffect(() => {
    if (mode !== "register") return;
    if (usernameTimer.current) clearTimeout(usernameTimer.current);
    if (!username.trim()) { setUsernameStatus(""); setUsernameMsg(""); return; }
    usernameTimer.current = setTimeout(() => checkUsername(username), 400);
    return () => { if (usernameTimer.current) clearTimeout(usernameTimer.current); };
  }, [username, mode, checkUsername]);

  function switchMode(next: Mode) { setMode(next); setStep(0); setError(""); }

  function validateStep(s: number): boolean {
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
      if (!effectiveStorageRoot.trim()) { setError("Storage root path is required."); return false; }
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

  function handleNext() { if (!validateStep(step)) return; setStep((s) => Math.min(s + 1, WIZARD_STEPS.length - 1)); setError(""); }
  function handleBack() { setStep((s) => Math.max(s - 1, 0)); setError(""); }

  async function handleRegister() {
    if (!validateStep(step)) return;
    setLoading(true); setError("");
    try {
      const data = await apiRegister({ username: username.trim(), password, confirm_password: confirmPassword, full_name: fullName.trim(), nickname: nickname.trim(), bio: bio.trim() || undefined, vault_password: vaultPassword, storage_root: effectiveStorageRoot.trim() });
      login(data.user!);
      if (ghUsername.trim() && ghToken.trim()) { try { await apiConnectGitHub(ghUsername.trim(), ghToken); } catch {} }
      router.replace("/app");
    } catch (err) { setError(err instanceof Error ? err.message : "Registration failed."); } finally { setLoading(false); }
  }

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault(); setLoading(true); setError("");
    try {
      const data = await apiLogin({ username: username.trim(), password });
      login(data.user!);
      router.replace("/app");
    } catch (err) { setError(err instanceof Error ? err.message : "Something went wrong."); } finally { setLoading(false); }
  }

  const isRegister = mode === "register";
  const isLastStep = step === WIZARD_STEPS.length - 1;

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-[440px] animate-fade-in">
        <div className="page-header text-center mb-6">
          <div className="flex justify-center mb-2"><div className="h-2 w-2 rounded-full bg-accent shadow-[0_0_12px_rgba(6,182,212,0.4)]" /></div>
          <h1 className="text-lg font-semibold text-text">Cortex</h1>
          <p className="text-xs text-text-muted mt-0.5">{isRegister ? `Step ${step + 1} of ${WIZARD_STEPS.length} \u2014 ${WIZARD_STEPS[step]}` : "Welcome back"}</p>
        </div>

        <Card className="p-5">
          {step === 0 && (
            <div className="flex rounded-lg bg-bg-surface p-0.5 mb-4 border border-border/50">
              {(["login", "register"] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => switchMode(m)}
                  className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all duration-200 ${
                    mode === m
                      ? "bg-bg-elevated text-text shadow-sm border border-border"
                      : "text-text-muted hover:text-text-secondary"
                  }`}
                >
                  {m === "login" ? "Sign in" : "Register"}
                </button>
              ))}
            </div>
          )}

          {isRegister && <div className="mb-4"><Steps steps={[...WIZARD_STEPS]} current={step} /></div>}

          {!isRegister && (
            <form onSubmit={handleLogin} className="grid gap-3">
              <Input label="Username" placeholder="operator-01" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required />
              <Input label="Password" type="password" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required />
              {error && <p className="text-sm text-error bg-error/10 rounded-md px-3 py-2 border border-error/10">{error}</p>}
              <Button type="submit" loading={loading} className="w-full mt-1">Sign in</Button>
            </form>
          )}

          {isRegister && (
            <>
              {step === 0 && (
                <div key="step-0" className="grid gap-3 animate-fade-in-up">
                  <div>
                    <Input label="Username" placeholder="operator-01" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" error={usernameStatus === "taken" || usernameStatus === "invalid" ? usernameMsg : undefined} className={usernameStatus === "available" ? "border-success/50" : usernameStatus === "taken" ? "border-error/50" : usernameStatus === "checking" ? "border-accent/30" : ""} required />
                    {usernameStatus === "available" && <p className="text-xs text-success mt-1">{'\u2713'} {usernameMsg}</p>}
                    {usernameStatus === "checking" && <p className="text-xs text-text-muted mt-1">Checking availability...</p>}
                  </div>
                  <div>
                    <Input label="Password" type="password" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" required />
                    <div className="mt-1"><PasswordStrength password={password} /></div>
                  </div>
                  <Input label="Confirm password" type="password" placeholder="••••••••" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} autoComplete="new-password" error={confirmPassword && password !== confirmPassword ? "Passwords do not match" : undefined} required />
                </div>
              )}

              {step === 1 && (
                <div key="step-1" className="grid gap-3 animate-fade-in-up">
                  <Input label="Full name" placeholder="Ada Lovelace" value={fullName} onChange={(e) => setFullName(e.target.value)} autoComplete="name" required />
                  <Input label="Nickname" placeholder="ada" value={nickname} onChange={(e) => setNickname(e.target.value)} autoComplete="nickname" required />

                  <div className="grid gap-1.5">
                    <label className="text-xs font-medium text-text-secondary">Data Storage Location</label>
                    <p className="text-xs text-text-muted">Where your personal data, vault files, and profile will be stored.</p>

                    {!storageCustom ? (
                      <div className="grid gap-2 mt-1">
                        {[
                          { label: "Home folder", path: "~/CortexData", icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" },
                          { label: "Documents folder", path: "~/Documents/Cortex", icon: "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" },
                          { label: "Desktop", path: "~/CortexWorkspace", icon: "M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" },
                        ].map((preset) => (
                          <button
                            key={preset.path}
                            type="button"
                            onClick={() => setStorageRoot(preset.path)}
                            className={`interactive-card flex items-center gap-3 p-3 rounded-lg border text-left transition-all ${
                              storageRoot === preset.path
                                ? "border-accent/40 bg-accent-faint text-accent"
                                : "border-border bg-bg-surface text-text-secondary hover:border-border hover:bg-bg-hover"
                            }`}
                          >
                            <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                              <path strokeLinecap="round" strokeLinejoin="round" d={preset.icon} />
                            </svg>
                            <div className="min-w-0">
                              <span className="text-sm font-medium block">{preset.label}</span>
                              <span className="text-xs text-text-muted font-mono block truncate">{preset.path}</span>
                            </div>
                            {storageRoot === preset.path && (
                              <svg className="w-4 h-4 text-accent shrink-0 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                              </svg>
                            )}
                          </button>
                        ))}
                        <button
                          type="button"
                          onClick={() => setStorageCustom(true)}
                          className="flex items-center gap-2 p-3 rounded-lg border border-dashed border-border text-text-muted hover:border-accent/30 hover:text-text-secondary transition-colors text-xs"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                          </svg>
                          Custom path...
                        </button>
                      </div>
                    ) : (
                      <div className="grid gap-2 mt-1">
                        <Input
                          placeholder="~/MyCortexData"
                          value={storageRoot}
                          onChange={(e) => setStorageRoot(e.target.value)}
                          required
                        />
                        <button
                          type="button"
                          onClick={() => setStorageCustom(false)}
                          className="text-xs text-text-muted hover:text-text-secondary transition-colors text-left"
                        >
                          {"\u2190"} Back to presets
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="grid gap-1.5">
                    <label className="text-xs font-medium text-text-secondary">Bio <span className="text-text-muted">(optional)</span></label>
                    <textarea value={bio} onChange={(e) => setBio(e.target.value)} placeholder="Tell us about yourself..." rows={2} className="w-full rounded-md bg-bg-surface border border-border px-3 py-2 text-sm text-text placeholder:text-text-muted outline-none transition-colors resize-none focus:border-accent/40 focus:ring-1 focus:ring-accent/20" />
                  </div>
                </div>
              )}

              {step === 2 && (
                <div key="step-2" className="grid gap-3 animate-fade-in-up">
                  <div className="rounded-md bg-bg-surface border border-border p-4">
                    <p className="text-sm font-medium text-text mb-3">Connect GitHub</p>
                    <div className="grid gap-3">
                      <Input label="GitHub username" placeholder="octocat" value={ghUsername} onChange={(e) => setGhUsername(e.target.value)} autoComplete="off" />
                      <Input label="Personal access token" type="password" placeholder="ghp_xxxxxxxxxxxx" value={ghToken} onChange={(e) => setGhToken(e.target.value)} autoComplete="off" />
                      <p className="text-xs text-text-muted"><a href="https://github.com/settings/tokens" target="_blank" rel="noreferrer" className="text-accent hover:underline">Generate one</a></p>
                    </div>
                  </div>
                  <button type="button" onClick={() => setStep(3)} className="text-xs text-text-muted hover:text-text transition-colors text-center">Skip for now</button>
                </div>
              )}

              {step === 3 && (
                <div key="step-3" className="grid gap-3 animate-fade-in-up">
                  <div className="rounded-md bg-accent-faint border border-accent/10 p-3"><p className="text-sm text-text-secondary leading-relaxed">The <span className="text-accent font-medium">vault password</span> encrypts your private files. It is never used for login and cannot be recovered.</p></div>
                  <Input label="Vault password" type="password" placeholder="••••••••" value={vaultPassword} onChange={(e) => setVaultPassword(e.target.value)} autoComplete="new-password" required />
                  <PasswordStrength password={vaultPassword} />
                  <Input label="Confirm vault password" type="password" placeholder="••••••••" value={vaultConfirm} onChange={(e) => setVaultConfirm(e.target.value)} autoComplete="new-password" error={vaultConfirm && vaultPassword !== vaultConfirm ? "Vault passwords do not match" : undefined} required />
                </div>
              )}

              {error && <p className="text-sm text-error bg-error/10 rounded-md px-3 py-2 border border-error/10 mt-2">{error}</p>}

              <div className="flex gap-3 mt-3">
                {step > 0 && <Button type="button" variant="secondary" onClick={handleBack} className="flex-1">Back</Button>}
                {isLastStep ? (
                  <Button type="button" loading={loading} onClick={handleRegister} className="flex-1">Create account</Button>
                ) : (
                  <Button type="button" onClick={handleNext} className="flex-1">Continue</Button>
                )}
              </div>
            </>
          )}
        </Card>
        <p className="mt-3 text-center text-xs text-text-muted font-mono tracking-wider uppercase">Local-first \u00b7 Private by default</p>
      </div>
    </div>
  );
}
