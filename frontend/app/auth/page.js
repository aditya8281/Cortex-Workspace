"use client";

import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { setSession, getSessionToken } from "../../src/shared/auth/session";
import { apiLogin, apiRegister } from "../../src/shared/auth/cortexApi";
import {
  cn,
  useField,
  Field,
  TextInput,
  PasswordInput,
  Btn,
  ErrorBanner,
  StepIndicator,
  Panel,
} from "../../src/shared/ui/form";

// ─── LOGIN ──────────────────────────────────────────────────────────────────────

function LoginForm({ onSwitch }) {
  const router = useRouter();
  const [username, onUsername] = useField();
  const [password, onPassword] = useField();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const usernameRef = useRef(null);

  useEffect(() => { usernameRef.current?.focus(); }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError("Username and password are required.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await apiLogin({ username: username.trim(), password });
      setSession(data.access_token, data.user);
      router.replace("/");
    } catch (err) {
      setError(err.message || "Authentication failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="animate-cortex-fade-in grid gap-6 p-7">
      {/* header */}
      <div className="grid gap-1">
        <div className="flex items-center gap-2 mb-1">
          <div className="h-[6px] w-[6px] rounded-full bg-cortex-cyan shadow-[0_0_8px_rgba(0,245,255,0.6)]" />
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-cortex-cyan">Cortex · Auth</span>
        </div>
        <h1 className="text-xl font-semibold text-cortex-text">Welcome back</h1>
        <p className="text-[13px] text-cortex-text-muted">Authenticate to resume your workspace.</p>
      </div>

      <form className="grid gap-4" onSubmit={handleSubmit} noValidate>
        <Field label="Username" id="login-username">
          <TextInput
            id="login-username"
            inputRef={usernameRef}
            value={username}
            onChange={onUsername}
            placeholder="operator-01"
            autoComplete="username"
            disabled={loading}
          />
        </Field>
        <Field label="Password" id="login-password">
          <PasswordInput
            id="login-password"
            value={password}
            onChange={onPassword}
            placeholder="••••••••"
            autoComplete="current-password"
            disabled={loading}
          />
        </Field>

        <ErrorBanner message={error} />

        <Btn type="submit" loading={loading} className="w-full mt-1">
          Authenticate
        </Btn>
      </form>

      <div className="grid gap-2 border-t border-cortex-border/50 pt-4">
        <Btn variant="ghost" className="w-full text-xs" onClick={onSwitch}>
          Create a new account →
        </Btn>
        <Btn variant="ghost" className="w-full text-xs" disabled>
          Import .crtx file (coming soon)
        </Btn>
      </div>
    </div>
  );
}

// ─── REGISTRATION STEPS ─────────────────────────────────────────────────────────

// step 1: account credentials
function Step1Account({ data, setData, onNext, error }) {
  const usernameRef = useRef(null);
  useEffect(() => { usernameRef.current?.focus(); }, []);

  function handleNext(e) {
    e.preventDefault();
    onNext();
  }

  return (
    <form className="grid gap-5" onSubmit={handleNext} noValidate>
      <div className="grid gap-1">
        <h2 className="text-base font-semibold text-cortex-text">Create your account</h2>
        <p className="text-[13px] text-cortex-text-muted">Choose a username and a strong password.</p>
      </div>

      <Field label="Username" id="reg-username">
        <TextInput
          id="reg-username"
          inputRef={usernameRef}
          value={data.username}
          onChange={(e) => setData("username", e.target.value)}
          placeholder="operator-01"
          autoComplete="username"
        />
      </Field>
      <Field label="Password" id="reg-password" hint="Min 8 characters, must contain a letter and a number.">
        <PasswordInput
          id="reg-password"
          value={data.password}
          onChange={(e) => setData("password", e.target.value)}
          placeholder="••••••••"
          autoComplete="new-password"
        />
      </Field>
      <Field label="Confirm Password" id="reg-confirm">
        <PasswordInput
          id="reg-confirm"
          value={data.confirm_password}
          onChange={(e) => setData("confirm_password", e.target.value)}
          placeholder="••••••••"
          autoComplete="new-password"
        />
      </Field>

      <ErrorBanner message={error} />
      <Btn type="submit" className="w-full">Continue →</Btn>
    </form>
  );
}

// step 2: profile
function Step2Profile({ data, setData, onNext, onBack, error }) {
  return (
    <form className="grid gap-5" onSubmit={(e) => { e.preventDefault(); onNext(); }} noValidate>
      <div className="grid gap-1">
        <h2 className="text-base font-semibold text-cortex-text">Build your profile</h2>
        <p className="text-[13px] text-cortex-text-muted">This personalises how Cortex understands you.</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Full Name *" id="reg-fullname">
          <TextInput
            id="reg-fullname"
            value={data.full_name}
            onChange={(e) => setData("full_name", e.target.value)}
            placeholder="Ada Lovelace"
            autoComplete="name"
          />
        </Field>
        <Field label="Nickname *" id="reg-nickname">
          <TextInput
            id="reg-nickname"
            value={data.nickname}
            onChange={(e) => setData("nickname", e.target.value)}
            placeholder="ada"
            autoComplete="nickname"
          />
        </Field>
      </div>

      <Field label="Bio" id="reg-bio" hint="One sentence about yourself.">
        <textarea
          id="reg-bio"
          value={data.bio}
          onChange={(e) => setData("bio", e.target.value)}
          placeholder="Engineer building AI-native systems."
          rows={2}
          className="w-full resize-none rounded-[6px] border border-cortex-border bg-cortex-bg-secondary px-4 py-[10px] text-sm text-cortex-text placeholder:text-cortex-text-muted transition-all duration-150 focus:border-cortex-cyan/40 focus:outline-none focus:ring-2 focus:ring-cortex-cyan/15"
        />
      </Field>

      <Field label="About" id="reg-description" hint="Expanded description for Cortex context.">
        <textarea
          id="reg-description"
          value={data.description}
          onChange={(e) => setData("description", e.target.value)}
          placeholder="I focus on distributed systems, Rust, and LLM tooling..."
          rows={3}
          className="w-full resize-none rounded-[6px] border border-cortex-border bg-cortex-bg-secondary px-4 py-[10px] text-sm text-cortex-text placeholder:text-cortex-text-muted transition-all duration-150 focus:border-cortex-cyan/40 focus:outline-none focus:ring-2 focus:ring-cortex-cyan/15"
        />
      </Field>

      <div className="grid gap-2">
        <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-cortex-text-muted">Handles / Social Links</span>
        <div className="grid gap-2">
          {["github", "twitter", "linkedin", "website"].map((key) => (
            <div key={key} className="flex items-center gap-2">
              <span className="w-20 shrink-0 font-mono text-[10px] uppercase tracking-[0.1em] text-cortex-text-muted">{key}</span>
              <TextInput
                id={`reg-handle-${key}`}
                value={data.handles?.[key] || ""}
                onChange={(e) => setData("handles", { ...(data.handles || {}), [key]: e.target.value })}
                placeholder={key === "github" ? "github.com/username" : key === "website" ? "https://example.com" : `@username`}
              />
            </div>
          ))}
        </div>
      </div>

      <ErrorBanner message={error} />
      <div className="flex gap-3">
        <Btn variant="ghost" className="flex-1" onClick={onBack}>← Back</Btn>
        <Btn type="submit" className="flex-1">Continue →</Btn>
      </div>
    </form>
  );
}

// step 3: vault password
function Step3Vault({ data, setData, onNext, onBack, error }) {
  return (
    <form className="grid gap-5" onSubmit={(e) => { e.preventDefault(); onNext(); }} noValidate>
      <div className="grid gap-1">
        <h2 className="text-base font-semibold text-cortex-text">Create a Vault Password</h2>
        <p className="text-[13px] text-cortex-text-muted">
          This password is <strong className="text-cortex-text font-semibold">exclusively</strong> for unlocking your Cortex Vault. It is never used for login.
        </p>
      </div>

      <div className="rounded-[6px] border border-cortex-cyan/20 bg-cortex-cyan/5 p-4 grid gap-2">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 h-[5px] w-[5px] shrink-0 rounded-full bg-cortex-cyan" />
          <p className="text-[12px] leading-5 text-cortex-text-muted">
            Account password — used for login only<br />
            <span className="text-cortex-cyan font-mono">Vault password — used for vault access only</span>
          </p>
        </div>
        <p className="text-[11px] text-cortex-text-muted pl-[17px]">
          Both are hashed independently. Neither can decrypt the other.
        </p>
      </div>

      <Field label="Vault Password" id="reg-vault-pw">
        <PasswordInput
          id="reg-vault-pw"
          value={data.vault_password}
          onChange={(e) => setData("vault_password", e.target.value)}
          placeholder="••••••••"
          autoComplete="new-password"
        />
      </Field>
      <Field label="Confirm Vault Password" id="reg-vault-confirm">
        <PasswordInput
          id="reg-vault-confirm"
          value={data.vault_password_confirm}
          onChange={(e) => setData("vault_password_confirm", e.target.value)}
          placeholder="••••••••"
          autoComplete="new-password"
        />
      </Field>

      <ErrorBanner message={error} />
      <div className="flex gap-3">
        <Btn variant="ghost" className="flex-1" onClick={onBack}>← Back</Btn>
        <Btn type="submit" className="flex-1">Continue →</Btn>
      </div>
    </form>
  );
}

// step 4: storage location
const STORAGE_PRESETS = [
  { label: "~/CortexVault", value: "~/CortexVault" },
  { label: "~/Documents/CortexVault", value: "~/Documents/CortexVault" },
  { label: "Custom path…", value: "" },
];

function Step4Storage({ data, setData, onNext, onBack, error }) {
  const [preset, setPreset] = useState(STORAGE_PRESETS[0].value);
  const [custom, onCustom] = useField("");
  const isCustom = preset === "";

  useEffect(() => {
    if (!isCustom) setData("personal_storage_path", preset);
  }, [preset]);

  function handleNext(e) {
    e.preventDefault();
    const finalPath = isCustom ? custom.trim() : preset;
    setData("personal_storage_path", finalPath);
    onNext();
  }

  return (
    <form className="grid gap-5" onSubmit={handleNext} noValidate>
      <div className="grid gap-1">
        <h2 className="text-base font-semibold text-cortex-text">Choose Storage Location</h2>
        <p className="text-[13px] text-cortex-text-muted">
          Cortex will store your personal vault files here. This path lives on your local machine.
        </p>
      </div>

      <div className="rounded-[6px] border border-cortex-border bg-cortex-bg-secondary/60 p-4 grid gap-3">
        <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-cortex-text-muted">Select a location</span>
        <div className="grid gap-2">
          {STORAGE_PRESETS.map((p) => (
            <label
              key={p.label}
              className={cn(
                "flex cursor-pointer items-center gap-3 rounded-[6px] border px-3 py-2.5 transition-all duration-150",
                preset === p.value
                  ? "border-cortex-cyan/35 bg-cortex-cyan/8 text-cortex-text"
                  : "border-cortex-border bg-transparent text-cortex-text-muted hover:border-cortex-border/80 hover:text-cortex-text"
              )}
            >
              <input
                type="radio"
                name="storage-preset"
                value={p.value}
                checked={preset === p.value}
                onChange={() => setPreset(p.value)}
                className="accent-[rgb(0,245,255)]"
              />
              <span className="font-mono text-[12px]">{p.label}</span>
            </label>
          ))}
        </div>

        {isCustom && (
          <Field label="Custom path" id="reg-custom-path" hint="Absolute or ~ path. e.g. ~/CortexVault or /data/cortex">
            <TextInput
              id="reg-custom-path"
              value={custom}
              onChange={onCustom}
              placeholder="~/CortexVault"
              autoComplete="off"
            />
          </Field>
        )}
      </div>

      <div className="rounded-[6px] border border-cortex-border/50 bg-cortex-bg-secondary/40 px-4 py-3 grid gap-1.5">
        <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-cortex-text-muted">What's stored here</span>
        <ul className="grid gap-1 text-[12px] text-cortex-text-muted leading-5 list-none pl-0">
          {["Vault files (encrypted)", "Workspace metadata database", "Embeddings & vector index", "Sync state & activity logs"].map((item) => (
            <li key={item} className="flex items-center gap-2">
              <span className="text-cortex-cyan font-mono">→</span> {item}
            </li>
          ))}
        </ul>
      </div>

      <ErrorBanner message={error} />
      <div className="flex gap-3">
        <Btn variant="ghost" className="flex-1" onClick={onBack}>← Back</Btn>
        <Btn type="submit" className="flex-1">Continue →</Btn>
      </div>
    </form>
  );
}

// step 5: review & create
function Step5Review({ data, onBack, onSubmit, loading, error }) {
  const profileRows = [
    { label: "Username", value: data.username },
    { label: "Full Name", value: data.full_name },
    { label: "Nickname", value: data.nickname },
    { label: "Bio", value: data.bio || "—" },
    { label: "Storage", value: data.personal_storage_path || "~/CortexVault" },
    { label: "Vault Password", value: "●●●●●●●●" },
  ];

  return (
    <div className="grid gap-5">
      <div className="grid gap-1">
        <h2 className="text-base font-semibold text-cortex-text">Review & Create</h2>
        <p className="text-[13px] text-cortex-text-muted">Confirm your identity before initializing Cortex.</p>
      </div>

      <div className="rounded-[6px] border border-cortex-border overflow-hidden">
        {profileRows.map(({ label, value }, i) => (
          <div
            key={label}
            className={cn(
              "flex items-start gap-4 px-4 py-2.5 text-sm",
              i !== profileRows.length - 1 && "border-b border-cortex-border/50"
            )}
          >
            <span className="w-28 shrink-0 font-mono text-[10px] uppercase tracking-[0.12em] text-cortex-text-muted pt-0.5">
              {label}
            </span>
            <span className="text-cortex-text break-all">{value}</span>
          </div>
        ))}
      </div>

      {data.bio && (
        <p className="text-[12px] leading-5 text-cortex-text-muted italic px-0.5">
          "{data.bio}"
        </p>
      )}

      <ErrorBanner message={error} />

      <div className="flex gap-3">
        <Btn variant="ghost" className="flex-1" onClick={onBack} disabled={loading}>← Back</Btn>
        <Btn className="flex-1" loading={loading} onClick={onSubmit}>
          Initialize Cortex →
        </Btn>
      </div>
    </div>
  );
}

// ─── REGISTRATION WIZARD ────────────────────────────────────────────────────────

const TOTAL_STEPS = 5;

function validate(step, data) {
  switch (step) {
    case 0:
      if (!data.username.trim()) return "Username is required.";
      if (data.password.length < 8) return "Password must be at least 8 characters.";
      if (!/[a-zA-Z]/.test(data.password) || !/[0-9]/.test(data.password))
        return "Password must contain at least one letter and one number.";
      if (data.password !== data.confirm_password) return "Passwords do not match.";
      return null;
    case 1:
      if (!data.full_name.trim()) return "Full name is required.";
      if (!data.nickname.trim()) return "Nickname is required.";
      return null;
    case 2:
      if (!data.vault_password || data.vault_password.length < 8)
        return "Vault password must be at least 8 characters.";
      if (!/[a-zA-Z]/.test(data.vault_password) || !/[0-9]/.test(data.vault_password))
        return "Vault password must contain at least one letter and one number.";
      if (data.vault_password !== data.vault_password_confirm)
        return "Vault passwords do not match.";
      return null;
    case 3:
      if (!data.personal_storage_path?.trim()) return "Please choose a storage location.";
      return null;
    default:
      return null;
  }
}

function RegisterWizard({ onSwitch }) {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setAllData] = useState({
    username: "", password: "", confirm_password: "",
    full_name: "", nickname: "", bio: "", description: "",
    handles: {},
    vault_password: "", vault_password_confirm: "",
    personal_storage_path: "~/CortexVault",
    preferences: {},
  });

  function setField(key, val) {
    setAllData((prev) => ({ ...prev, [key]: val }));
  }

  function goNext() {
    const err = validate(step, data);
    if (err) { setError(err); return; }
    setError("");
    setStep((s) => Math.min(s + 1, TOTAL_STEPS - 1));
  }

  function goBack() {
    setError("");
    setStep((s) => Math.max(s - 1, 0));
  }

  async function handleSubmit() {
    setLoading(true);
    setError("");
    try {
      // Clean up handles — remove empty values
      const cleanHandles = Object.fromEntries(
        Object.entries(data.handles || {}).filter(([, v]) => v.trim())
      );
      const payload = {
        username: data.username.trim(),
        password: data.password,
        confirm_password: data.confirm_password,
        full_name: data.full_name.trim(),
        nickname: data.nickname.trim(),
        bio: data.bio.trim() || null,
        description: data.description.trim() || null,
        handles: cleanHandles,
        vault_password: data.vault_password,
        personal_storage_path: data.personal_storage_path.trim(),
        preferences: {},
      };
      const result = await apiRegister(payload);
      setSession(result.access_token, result.user);
      router.replace("/");
    } catch (err) {
      setError(err.message || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const stepProps = { data, setData: setField, onNext: goNext, onBack: goBack, error };

  return (
    <div className="animate-cortex-fade-in grid gap-6 p-7">
      {/* header */}
      <div className="grid gap-3">
        <div className="flex items-center gap-2">
          <div className="h-[6px] w-[6px] rounded-full bg-cortex-cyan/70" />
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-cortex-cyan">Cortex · Init</span>
        </div>
        <StepIndicator current={step} total={TOTAL_STEPS} />
      </div>

      {step === 0 && <Step1Account {...stepProps} />}
      {step === 1 && <Step2Profile {...stepProps} />}
      {step === 2 && <Step3Vault {...stepProps} />}
      {step === 3 && <Step4Storage {...stepProps} />}
      {step === 4 && (
        <Step5Review
          data={data}
          onBack={goBack}
          onSubmit={handleSubmit}
          loading={loading}
          error={error}
        />
      )}

      <div className="border-t border-cortex-border/50 pt-3">
        <Btn variant="ghost" className="w-full text-xs" onClick={onSwitch} disabled={loading}>
          ← Already have an account? Sign in
        </Btn>
      </div>
    </div>
  );
}

// ─── ROOT PAGE ──────────────────────────────────────────────────────────────────

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const token = getSessionToken();
    if (token) { router.replace("/"); return; }
    setMounted(true);
  }, [router]);

  if (!mounted) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-cortex-bg">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-cortex-cyan/30 border-t-cortex-cyan" />
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-cortex-bg px-4 py-12 overflow-hidden">
      {/* ambient background glow */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/3 top-0 h-[500px] w-[500px] -translate-x-1/2 rounded-full bg-cortex-cyan/[0.03] blur-[120px]" />
        <div className="absolute right-1/4 bottom-0 h-[400px] w-[400px] rounded-full bg-[rgba(120,80,255,0.04)] blur-[100px]" />
      </div>

      {/* wordmark */}
      <div className="absolute top-6 left-7 flex items-center gap-2">
        <div className="h-2 w-2 rounded-full bg-cortex-cyan shadow-[0_0_10px_rgba(0,245,255,0.5)]" />
        <span className="font-mono text-[11px] uppercase tracking-[0.22em] text-cortex-text-muted">CORTEX</span>
      </div>

      <div className="relative z-10 w-full" style={{ maxWidth: mode === "register" ? 540 : 440 }}>
        <Panel>
          {mode === "login" ? (
            <LoginForm key="login" onSwitch={() => setMode("register")} />
          ) : (
            <RegisterWizard key="register" onSwitch={() => setMode("login")} />
          )}
        </Panel>

        <p className="mt-4 text-center font-mono text-[10px] uppercase tracking-[0.12em] text-cortex-text-muted/50">
          Local-first · Private by default
        </p>
      </div>
    </div>
  );
}
