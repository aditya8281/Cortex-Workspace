"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Shield, Lock, User, CodeSquare, ArrowRight, ArrowLeft, Check } from "lucide-react";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { apiLogin, apiRegister, apiCheckUsername, apiConnectGitHub } from "../../src/shared/auth/cortexApi";
import Button from "../../src/shared/ui/Button";
import Input from "../../src/shared/ui/Input";
import Card from "../../src/shared/ui/Card";
import PasswordStrength from "../../src/shared/ui/PasswordStrength";
import { cn } from "../../src/lib/utils";

const WIZARD_STEPS = ["Account", "Profile", "GitHub", "Vault"] as const;

type Mode = "login" | "register";
type UsernameStatus = "" | "invalid" | "checking" | "available" | "taken";

function FloatingDots() {
  const dots = useMemo(() => [
    { id: 0, x: 12, y: 18, size: 3, delay: 0.2, duration: 5.5 },
    { id: 1, x: 78, y: 32, size: 5, delay: 1.1, duration: 6.2 },
    { id: 2, x: 45, y: 85, size: 2, delay: 2.3, duration: 4.8 },
    { id: 3, x: 91, y: 12, size: 4, delay: 0.8, duration: 7.1 },
    { id: 4, x: 23, y: 67, size: 3, delay: 1.9, duration: 5.0 },
    { id: 5, x: 67, y: 45, size: 6, delay: 0.5, duration: 6.8 },
    { id: 6, x: 8, y: 90, size: 2, delay: 2.7, duration: 4.3 },
    { id: 7, x: 55, y: 20, size: 4, delay: 1.4, duration: 5.9 },
    { id: 8, x: 35, y: 55, size: 3, delay: 0.3, duration: 6.5 },
    { id: 9, x: 82, y: 78, size: 5, delay: 2.0, duration: 5.2 },
    { id: 10, x: 15, y: 40, size: 2, delay: 1.6, duration: 7.0 },
    { id: 11, x: 60, y: 8, size: 4, delay: 0.9, duration: 4.6 },
  ], []);

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {dots.map((dot) => (
        <motion.div
          key={dot.id}
          className="absolute rounded-full bg-accent/20"
          style={{
            left: `${dot.x}%`,
            top: `${dot.y}%`,
            width: dot.size,
            height: dot.size,
          }}
          animate={{
            y: [0, -30, 0],
            opacity: [0.2, 0.6, 0.2],
            scale: [1, 1.3, 1],
          }}
          transition={{
            duration: dot.duration,
            repeat: Infinity,
            ease: "easeInOut",
            delay: dot.delay,
          }}
        />
      ))}
    </div>
  );
}

function ErrorShake({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      animate={{ x: [0, -6, 6, -4, 4, 0] }}
      transition={{ duration: 0.4 }}
    >
      {children}
    </motion.div>
  );
}

export default function AuthPage() {
  const router = useRouter();
  const { user, login, loading: authLoading } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [shakeKey, setShakeKey] = useState(0);

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
    setUsernameStatus("checking");
    setUsernameMsg("");
    usernameTimer.current = setTimeout(() => checkUsername(username), 400);
    return () => { if (usernameTimer.current) clearTimeout(usernameTimer.current); };
  }, [username, mode, checkUsername]);

  function switchMode(next: Mode) {
    setMode(next);
    setStep(0);
    setError("");
    setUsername("");
    setPassword("");
    setConfirmPassword("");
    setFullName("");
    setNickname("");
    setBio("");
    setGhUsername("");
    setGhToken("");
    setVaultPassword("");
    setVaultConfirm("");
    setStorageRoot("~/CortexData");
    setStorageCustom(false);
    setUsernameStatus("");
    setUsernameMsg("");
  }

  function validateStep(s: number): boolean {
    setError("");
    if (s === 0) {
      if (!username.trim()) { setError("Username is required."); return false; }
      if (usernameStatus === "checking") { setError("Still checking username availability..."); return false; }
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

  function handleNext() {
    if (!validateStep(step)) { setShakeKey((k) => k + 1); return; }
    setStep((s) => Math.min(s + 1, WIZARD_STEPS.length - 1));
    setError("");
  }
  function handleBack() { setStep((s) => Math.max(s - 1, 0)); setError(""); }

  async function handleRegister() {
    if (!validateStep(step)) { setShakeKey((k) => k + 1); return; }
    setLoading(true); setError("");
    try {
      const data = await apiRegister({ username: username.trim(), password, confirm_password: confirmPassword, full_name: fullName.trim(), nickname: nickname.trim(), bio: bio.trim() || undefined, vault_password: vaultPassword, storage_root: effectiveStorageRoot.trim() });
      if (!data.user) { setError("Registration succeeded but user data is missing. Please try logging in."); setLoading(false); return; }
      login(data.user);
      if (ghUsername.trim() && ghToken.trim()) { try { await apiConnectGitHub(ghUsername.trim(), ghToken.trim()); } catch { setError("GitHub connection failed. You can connect later from settings."); } }
      router.replace("/app");
    } catch (err) { setError(err instanceof Error ? err.message : "Registration failed."); } finally { setLoading(false); }
  }

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault(); setLoading(true); setError("");
    try {
      const data = await apiLogin({ username: username.trim(), password });
      if (!data.user) { setError("Login succeeded but user data is missing. Please try again."); setLoading(false); return; }
      login(data.user);
      router.replace("/app");
    } catch (err) { setError(err instanceof Error ? err.message : "Something went wrong."); } finally { setLoading(false); }
  }

  const isRegister = mode === "register";
  const isLastStep = step === WIZARD_STEPS.length - 1;

  const stepIcons = [Lock, User, CodeSquare, Shield];

  return (
    <div className="min-h-screen flex flex-col lg:flex-row">
      {/* Left side — visualization */}
      <div className="hidden lg:flex relative w-1/2 items-center justify-center overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-accent/5 via-transparent to-accent/[0.02]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(6,182,212,0.06)_0%,transparent_70%)]" />
        <FloatingDots />
        <div className="relative z-10 flex flex-col items-center gap-6 px-12">
          <motion.div
            className="w-16 h-16 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center"
            animate={{ boxShadow: ["0 0 20px rgba(6,182,212,0.1)", "0 0 40px rgba(6,182,212,0.2)", "0 0 20px rgba(6,182,212,0.1)"] }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          >
            <div className="h-3 w-3 rounded-full bg-accent shadow-[0_0_16px_rgba(6,182,212,0.5)]" />
          </motion.div>
          <div className="text-center">
            <h1 className="text-2xl font-semibold text-text font-display tracking-tight">Cortex</h1>
            <p className="text-sm text-text-muted mt-2 max-w-xs leading-relaxed">
              Your machine&apos;s intelligence layer. Local-first, private by default.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-text-muted font-mono tracking-wider uppercase">
            <span className="h-1.5 w-1.5 rounded-full bg-success shadow-[0_0_6px_rgba(34,197,94,0.4)]" />
            End-to-end encrypted
          </div>
        </div>
      </div>

      {/* Right side — form */}
      <div className="flex-1 flex items-center justify-center px-4 py-8 lg:px-12">
        <div className="w-full max-w-[440px]">
          {/* Mobile header */}
          <div className="lg:hidden text-center mb-6">
            <div className="flex justify-center mb-2">
              <div className="h-2 w-2 rounded-full bg-accent shadow-[0_0_12px_rgba(6,182,212,0.4)]" />
            </div>
            <h1 className="text-lg font-semibold text-text">Cortex</h1>
            <p className="text-xs text-text-muted mt-0.5">Local-first · Private by default</p>
          </div>

          <Card className="p-6">
            {/* Login/Register toggle */}
            <div className="flex rounded-xl bg-bg-surface p-1 mb-5 border border-border/50 relative">
              <motion.div
                className="absolute top-1 bottom-1 rounded-lg bg-bg-elevated border border-border shadow-sm"
                layout
                transition={{ type: "spring", damping: 25, stiffness: 300 }}
                style={{ left: mode === "login" ? "4px" : "50%", width: "calc(50% - 4px)" }}
              />
              {(["login", "register"] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => switchMode(m)}
                  className={cn(
                    "flex-1 py-2 text-sm font-medium rounded-lg transition-colors relative z-10",
                    mode === m ? "text-text" : "text-text-muted hover:text-text-secondary"
                  )}
                >
                  {m === "login" ? "Sign in" : "Register"}
                </button>
              ))}
            </div>

            {/* Wizard progress */}
            {isRegister && (
              <div className="mb-5">
                <div className="flex items-center justify-between mb-3" role="tablist">
                  {WIZARD_STEPS.map((s, i) => {
                    const Icon = stepIcons[i];
                    const isDone = i < step;
                    const isActive = i === step;
                    return (
                      <div key={s} className="flex items-center">
                        <motion.div
                          role="tab"
                          aria-selected={isActive}
                          className={cn(
                            "w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300",
                            isDone
                              ? "bg-accent text-white shadow-[0_0_10px_rgba(6,182,212,0.3)]"
                              : isActive
                              ? "bg-accent/15 text-accent border border-accent/30"
                              : "bg-bg-surface text-text-muted border border-border"
                          )}
                          animate={isActive ? { scale: [1, 1.05, 1] } : {}}
                          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                        >
                          {isDone ? <Check className="w-3.5 h-3.5" /> : <Icon className="w-3.5 h-3.5" />}
                        </motion.div>
                        {i < WIZARD_STEPS.length - 1 && (
                          <div className="w-8 sm:w-12 h-px mx-1 relative">
                            <motion.div
                              className="h-full bg-accent/30"
                              initial={{ scaleX: 0 }}
                              animate={{ scaleX: isDone ? 1 : 0 }}
                              transition={{ duration: 0.3 }}
                              style={{ transformOrigin: "left" }}
                            />
                            <div className="h-full bg-border absolute w-full" />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
                <div className="h-[3px] w-full rounded-full bg-bg-surface overflow-hidden">
                  <motion.div
                    className="h-full rounded-full bg-gradient-to-r from-accent/60 to-accent"
                    initial={{ width: 0 }}
                    animate={{ width: `${(step / (WIZARD_STEPS.length - 1)) * 100}%` }}
                    transition={{ type: "spring", damping: 25, stiffness: 200 }}
                  />
                </div>
                <div className="flex justify-between mt-2">
                  <span className="text-[10px] font-mono text-text-muted uppercase tracking-wider">
                    Step {step + 1} of {WIZARD_STEPS.length}
                  </span>
                  <span className="text-[10px] font-mono text-accent uppercase tracking-wider">
                    {WIZARD_STEPS[step]}
                  </span>
                </div>
              </div>
            )}

            {/* Login form */}
            {!isRegister && (
              <form onSubmit={handleLogin} className="grid gap-4">
                <Input label="Username" placeholder="operator-01" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required />
                <Input label="Password" type="password" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required />
                <ErrorShake key={shakeKey}>
                  {error && <p role="alert" className="text-sm text-error bg-error/10 rounded-xl px-3 py-2 border border-error/10">{error}</p>}
                </ErrorShake>
                <Button type="submit" loading={loading} className="w-full mt-1">Sign in</Button>
              </form>
            )}

            {/* Register wizard */}
            {isRegister && (
              <AnimatePresence mode="wait">
                <motion.div
                  key={step}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ type: "spring", damping: 25, stiffness: 200 }}
                >
                  {/* Step 0: Account */}
                  {step === 0 && (
                    <div className="grid gap-4">
                      <div>
                        <Input label="Username" placeholder="operator-01" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" error={usernameStatus === "taken" || usernameStatus === "invalid" ? usernameMsg : undefined} className={usernameStatus === "available" ? "border-success/50" : usernameStatus === "taken" ? "border-error/50" : usernameStatus === "checking" ? "border-accent/30" : ""} required />
                        {usernameStatus === "available" && <p className="text-xs text-success mt-1">{usernameMsg}</p>}
                        {usernameStatus === "checking" && <p className="text-xs text-text-muted mt-1">Checking availability...</p>}
                      </div>
                      <div>
                        <Input label="Password" type="password" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" required />
                        <div className="mt-1"><PasswordStrength password={password} /></div>
                      </div>
                      <Input label="Confirm password" type="password" placeholder="••••••••" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} autoComplete="new-password" error={confirmPassword && password !== confirmPassword ? "Passwords do not match" : undefined} required />
                    </div>
                  )}

                  {/* Step 1: Profile */}
                  {step === 1 && (
                    <div className="grid gap-4">
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
                                className={cn(
                                  "flex items-center gap-3 p-3 rounded-xl border text-left transition-all duration-200",
                                  storageRoot === preset.path
                                    ? "border-accent/40 bg-accent-faint text-accent"
                                    : "border-border bg-bg-surface text-text-secondary hover:border-border hover:bg-bg-hover"
                                )}
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
                              className="flex items-center gap-2 p-3 rounded-xl border border-dashed border-border text-text-muted hover:border-accent/30 hover:text-text-secondary transition-colors text-xs"
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
                              Back to presets
                            </button>
                          </div>
                        )}
                      </div>

                      <div className="grid gap-1.5">
                        <label htmlFor="bio" className="text-xs font-medium text-text-secondary">Bio <span className="text-text-muted">(optional)</span></label>
                        <textarea id="bio" value={bio} onChange={(e) => setBio(e.target.value)} placeholder="Tell us about yourself..." rows={2} className="w-full rounded-xl bg-bg-surface border border-border-subtle px-3.5 py-2.5 text-sm text-text placeholder:text-text-muted outline-none transition-all duration-200 resize-none focus:border-accent/40 focus:ring-2 focus:ring-accent/10 focus:shadow-glow" />
                      </div>
                    </div>
                  )}

                  {/* Step 2: GitHub */}
                  {step === 2 && (
                    <div className="grid gap-4">
                      <div className="rounded-xl bg-bg-surface border border-border-subtle p-4">
                        <div className="flex items-center gap-2 mb-3">
                          <CodeSquare className="w-4 h-4 text-text-secondary" />
                          <p className="text-sm font-medium text-text">Connect GitHub</p>
                        </div>
                        <div className="grid gap-3">
                          <Input label="GitHub username" placeholder="octocat" value={ghUsername} onChange={(e) => setGhUsername(e.target.value)} autoComplete="off" />
                          <Input label="Personal access token" type="password" placeholder="ghp_xxxxxxxxxxxx" value={ghToken} onChange={(e) => setGhToken(e.target.value)} autoComplete="off" />
                          <p className="text-xs text-text-muted"><a href="https://github.com/settings/tokens" target="_blank" rel="noreferrer" className="text-accent hover:underline">Generate one</a></p>
                        </div>
                      </div>
                      <button type="button" onClick={() => setStep(3)} className="text-xs text-text-muted hover:text-text transition-colors text-center">
                        Skip for now
                      </button>
                    </div>
                  )}

                  {/* Step 3: Vault */}
                  {step === 3 && (
                    <div className="grid gap-4">
                      <motion.div
                        className="rounded-xl bg-accent-faint border border-accent/10 p-4"
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ type: "spring", damping: 25, stiffness: 200 }}
                      >
                        <div className="flex items-start gap-3">
                          <motion.div
                            className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center shrink-0"
                            animate={{ boxShadow: ["0 0 10px rgba(6,182,212,0.1)", "0 0 20px rgba(6,182,212,0.2)", "0 0 10px rgba(6,182,212,0.1)"] }}
                            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                          >
                            <Shield className="w-4 h-4 text-accent" />
                          </motion.div>
                          <div>
                            <p className="text-sm font-medium text-text">Vault encryption</p>
                            <p className="text-xs text-text-secondary leading-relaxed mt-0.5">
                              The <span className="text-accent font-medium">vault password</span> encrypts your private files. It is never used for login and cannot be recovered.
                            </p>
                          </div>
                        </div>
                      </motion.div>
                      <Input label="Vault password" type="password" placeholder="••••••••" value={vaultPassword} onChange={(e) => setVaultPassword(e.target.value)} autoComplete="new-password" required />
                      <PasswordStrength password={vaultPassword} />
                      <Input label="Confirm vault password" type="password" placeholder="••••••••" value={vaultConfirm} onChange={(e) => setVaultConfirm(e.target.value)} autoComplete="new-password" error={vaultConfirm && vaultPassword !== vaultConfirm ? "Vault passwords do not match" : undefined} required />
                    </div>
                  )}
                </motion.div>
              </AnimatePresence>
            )}

            {/* Error display for register */}
            {isRegister && error && (
              <ErrorShake key={shakeKey}>
                <p role="alert" className="text-sm text-error bg-error/10 rounded-xl px-3 py-2 border border-error/10 mt-4">{error}</p>
              </ErrorShake>
            )}

            {/* Navigation buttons */}
            {isRegister && (
              <div className="flex gap-3 mt-5">
                {step > 0 && (
                  <Button type="button" variant="secondary" onClick={handleBack} className="flex-1">
                    <ArrowLeft className="w-3.5 h-3.5" />
                    Back
                  </Button>
                )}
                {isLastStep ? (
                  <Button type="button" loading={loading} onClick={handleRegister} className="flex-1">
                    Create account
                    <Check className="w-3.5 h-3.5" />
                  </Button>
                ) : (
                  <Button type="button" onClick={handleNext} className="flex-1">
                    Continue
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                )}
              </div>
            )}
          </Card>

          {/* Footer tagline */}
          <p className="mt-4 text-center text-xs text-text-muted font-mono tracking-wider uppercase">
            Local-first · Private by default
          </p>
        </div>
      </div>
    </div>
  );
}
