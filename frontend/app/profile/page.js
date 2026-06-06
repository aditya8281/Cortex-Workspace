"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { getSessionUser, setSession, clearSession } from "../../src/shared/auth/session";
import { apiGetMe, apiUpdateMe } from "../../src/shared/auth/cortexApi";
import { cn, useField, Field, TextInput, Textarea, PasswordInput, Btn, ErrorBanner, SuccessBanner, SectionDivider } from "../../src/shared/ui/form";

// ─── avatar initials ───────────────────────────────────────────────────────────

function Avatar({ name, size = "lg" }) {
  const initials = (name || "?")
    .split(" ")
    .slice(0, 2)
    .map(w => w[0]?.toUpperCase() || "")
    .join("");
  const sizes = { sm: "h-9 w-9 text-sm", md: "h-12 w-12 text-base", lg: "h-16 w-16 text-xl" };
  return (
    <div className={cn(
      "flex shrink-0 items-center justify-center rounded-full font-semibold",
      "border border-cortex-cyan/25 bg-cortex-cyan/10 text-cortex-cyan",
      "shadow-[0_0_20px_rgba(0,245,255,0.12)]",
      sizes[size]
    )}>
      {initials}
    </div>
  );
}

// ─── handle row ────────────────────────────────────────────────────────────────

const HANDLE_KEYS = ["github", "twitter", "linkedin", "website"];

function HandleRow({ handleKey, value, onChange }) {
  return (
    <div className="flex items-center gap-3">
      <span className="w-20 shrink-0 font-mono text-[10px] uppercase tracking-[0.1em] text-cortex-text-muted">
        {handleKey}
      </span>
      <TextInput
        id={`handle-${handleKey}`}
        value={value}
        onChange={onChange}
        placeholder={handleKey === "github" ? "github.com/username" : handleKey === "website" ? "https://example.com" : "@username"}
      />
    </div>
  );
}

// ─── section: edit profile ─────────────────────────────────────────────────────

function EditProfileSection({ user, onSaved }) {
  const [fullName, onFullName, setFullName] = useField(user?.full_name || "");
  const [nickname, onNickname, setNickname] = useField(user?.nickname || "");
  const [bio, onBio, setBio] = useField(user?.bio || "");
  const [description, onDescription, setDescription] = useField(user?.description || "");
  const [handles, setHandles] = useState(user?.handles || {});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleSave(e) {
    e.preventDefault();
    if (!fullName.trim()) { setError("Full name is required."); return; }
    if (!nickname.trim()) { setError("Nickname is required."); return; }
    setLoading(true); setError(""); setSuccess("");
    try {
      const cleanHandles = Object.fromEntries(
        Object.entries(handles).filter(([, v]) => v?.trim())
      );
      const updated = await apiUpdateMe({
        full_name: fullName.trim(),
        nickname: nickname.trim(),
        bio: bio.trim() || null,
        description: description.trim() || null,
        handles: cleanHandles,
      });
      setSuccess("Profile updated.");
      onSaved?.(updated);
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.message || "Failed to update profile.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="grid gap-4" onSubmit={handleSave} noValidate>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Full Name *" id="pf-fullname">
          <TextInput id="pf-fullname" value={fullName} onChange={onFullName} placeholder="Ada Lovelace" autoComplete="name" disabled={loading} />
        </Field>
        <Field label="Nickname *" id="pf-nickname">
          <TextInput id="pf-nickname" value={nickname} onChange={onNickname} placeholder="ada" disabled={loading} />
        </Field>
      </div>
      <Field label="Bio" id="pf-bio" hint="Short summary — visible across Cortex.">
        <Textarea id="pf-bio" value={bio} onChange={onBio} placeholder="Engineer building AI-native systems." rows={2} disabled={loading} />
      </Field>
      <Field label="About" id="pf-description" hint="Extended context. Cortex uses this to personalise responses.">
        <Textarea id="pf-description" value={description} onChange={onDescription} placeholder="I focus on distributed systems, Rust, and LLM tooling…" rows={3} disabled={loading} />
      </Field>

      <SectionDivider label="Handles" />
      <div className="grid gap-2">
        {HANDLE_KEYS.map(k => (
          <HandleRow key={k} handleKey={k}
            value={handles?.[k] || ""}
            onChange={e => setHandles(h => ({ ...h, [k]: e.target.value }))}
          />
        ))}
      </div>

      <ErrorBanner message={error} />
      <SuccessBanner message={success} />
      <Btn type="submit" loading={loading} className="w-full sm:w-auto">Save Profile</Btn>
    </form>
  );
}

// ─── section: change account password ─────────────────────────────────────────

function ChangePasswordSection() {
  const [current, onCurrent] = useField();
  const [next, onNext] = useField();
  const [confirm, onConfirm] = useField();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleSave(e) {
    e.preventDefault();
    if (!current) { setError("Current password is required."); return; }
    if (next.length < 8) { setError("New password must be at least 8 characters."); return; }
    if (!/[a-zA-Z]/.test(next) || !/[0-9]/.test(next)) { setError("New password must contain a letter and a number."); return; }
    if (next !== confirm) { setError("Passwords do not match."); return; }
    setLoading(true); setError(""); setSuccess("");
    try {
      await apiUpdateMe({ current_password: current, password: next });
      setSuccess("Account password changed.");
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.message || "Failed to change password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="grid gap-4" onSubmit={handleSave} noValidate>
      <div className="rounded-[6px] border border-cortex-border/50 bg-cortex-bg-secondary/40 px-4 py-3">
        <p className="text-[12px] leading-5 text-cortex-text-muted">
          Your <span className="text-cortex-text font-medium">account password</span> is used only for login. It is independent of your vault password.
        </p>
      </div>
      <Field label="Current Password" id="pw-current">
        <PasswordInput id="pw-current" value={current} onChange={onCurrent} placeholder="••••••••" autoComplete="current-password" disabled={loading} />
      </Field>
      <Field label="New Password" id="pw-new" hint="Min 8 chars, must include a letter and a number.">
        <PasswordInput id="pw-new" value={next} onChange={onNext} placeholder="••••••••" autoComplete="new-password" disabled={loading} />
      </Field>
      <Field label="Confirm New Password" id="pw-confirm">
        <PasswordInput id="pw-confirm" value={confirm} onChange={onConfirm} placeholder="••••••••" autoComplete="new-password" disabled={loading} />
      </Field>
      <ErrorBanner message={error} />
      <SuccessBanner message={success} />
      <Btn type="submit" loading={loading}>Update Password</Btn>
    </form>
  );
}

// ─── section: change vault password ───────────────────────────────────────────

function ChangeVaultPasswordSection() {
  const [accountPw, onAccountPw] = useField();
  const [vaultNext, onVaultNext] = useField();
  const [vaultConfirm, onVaultConfirm] = useField();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleSave(e) {
    e.preventDefault();
    if (!accountPw) { setError("Account password is required to change vault password."); return; }
    if (vaultNext.length < 8) { setError("Vault password must be at least 8 characters."); return; }
    if (!/[a-zA-Z]/.test(vaultNext) || !/[0-9]/.test(vaultNext)) { setError("Vault password must contain a letter and a number."); return; }
    if (vaultNext !== vaultConfirm) { setError("Vault passwords do not match."); return; }
    setLoading(true); setError(""); setSuccess("");
    try {
      await apiUpdateMe({ current_password: accountPw, vault_password: vaultNext });
      setSuccess("Vault password updated.");
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.message || "Failed to update vault password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="grid gap-4" onSubmit={handleSave} noValidate>
      <div className="rounded-[6px] border border-cortex-cyan/20 bg-cortex-cyan/5 px-4 py-3">
        <p className="text-[12px] leading-5 text-cortex-text-muted">
          Your <span className="text-cortex-cyan font-medium">vault password</span> is stored as an independent hash. It never grants account access.
        </p>
      </div>
      <Field label="Account Password (to confirm identity)" id="vp-account">
        <PasswordInput id="vp-account" value={accountPw} onChange={onAccountPw} placeholder="••••••••" autoComplete="current-password" disabled={loading} />
      </Field>
      <Field label="New Vault Password" id="vp-new" hint="Min 8 chars, must include a letter and a number.">
        <PasswordInput id="vp-new" value={vaultNext} onChange={onVaultNext} placeholder="••••••••" autoComplete="new-password" disabled={loading} />
      </Field>
      <Field label="Confirm Vault Password" id="vp-confirm">
        <PasswordInput id="vp-confirm" value={vaultConfirm} onChange={onVaultConfirm} placeholder="••••••••" autoComplete="new-password" disabled={loading} />
      </Field>
      <ErrorBanner message={error} />
      <SuccessBanner message={success} />
      <Btn type="submit" loading={loading}>Update Vault Password</Btn>
    </form>
  );
}

// ─── tab nav ───────────────────────────────────────────────────────────────────

const TABS = [
  { id: "profile", label: "Edit Profile" },
  { id: "password", label: "Account Password" },
  { id: "vault", label: "Vault Password" },
];

function TabNav({ active, onChange }) {
  return (
    <div className="flex gap-1 rounded-[8px] border border-cortex-border bg-cortex-bg-secondary/60 p-1">
      {TABS.map(t => (
        <button
          key={t.id}
          type="button"
          onClick={() => onChange(t.id)}
          className={cn(
            "flex-1 rounded-[6px] px-3 py-2 text-xs font-medium tracking-wide transition-all duration-150 focus:outline-none",
            active === t.id
              ? "bg-cortex-surface border border-cortex-border text-cortex-text shadow-sm"
              : "border border-transparent text-cortex-text-muted hover:text-cortex-text"
          )}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

// ─── handle display ────────────────────────────────────────────────────────────

function HandlesList({ handles }) {
  const entries = Object.entries(handles || {}).filter(([, v]) => v?.trim());
  if (!entries.length) return <span className="text-[12px] text-cortex-text-muted italic">No handles set</span>;
  return (
    <div className="flex flex-wrap gap-2">
      {entries.map(([key, val]) => (
        <div key={key} className="flex items-center gap-1.5 rounded-full border border-cortex-border bg-cortex-bg-secondary px-3 py-1">
          <span className="font-mono text-[9px] uppercase tracking-[0.12em] text-cortex-text-muted">{key}</span>
          <span className="text-[11px] text-cortex-text">{val}</span>
        </div>
      ))}
    </div>
  );
}

// ─── profile card ──────────────────────────────────────────────────────────────

function ProfileCard({ user }) {
  return (
    <div className="rounded-[10px] border border-cortex-border bg-cortex-surface/60 backdrop-blur-xl p-6 grid gap-5">
      {/* identity row */}
      <div className="flex items-start gap-4">
        <Avatar name={user?.full_name || user?.username} size="lg" />
        <div className="grid gap-0.5 min-w-0">
          <h1 className="text-lg font-semibold text-cortex-text truncate">
            {user?.full_name || user?.username}
          </h1>
          <div className="flex items-center gap-2">
            <span className="text-[13px] text-cortex-text-muted">
              @{user?.username}
            </span>
            {user?.nickname && user.nickname !== user.full_name && (
              <>
                <span className="text-cortex-border">·</span>
                <span className="text-[13px] text-cortex-cyan/80">{user.nickname}</span>
              </>
            )}
          </div>
          <div className="mt-1">
            <span className={cn(
              "inline-flex items-center rounded-full border px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.14em]",
              user?.role === "admin"
                ? "border-[rgba(255,180,0,0.3)] text-[rgba(255,200,50,0.9)]"
                : "border-cortex-border text-cortex-text-muted"
            )}>
              {user?.role || "user"}
            </span>
          </div>
        </div>
      </div>

      {/* bio */}
      {user?.bio && (
        <p className="text-[13px] leading-6 text-cortex-text-muted border-l-2 border-cortex-cyan/25 pl-4">
          {user.bio}
        </p>
      )}

      {/* about */}
      {user?.description && (
        <div className="grid gap-1.5">
          <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-cortex-text-muted">About</span>
          <p className="text-[13px] leading-6 text-cortex-text-muted">{user.description}</p>
        </div>
      )}

      {/* handles */}
      <div className="grid gap-2">
        <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-cortex-text-muted">Handles</span>
        <HandlesList handles={user?.handles} />
      </div>

      {/* storage */}
      {user?.personal_storage_path && (
        <div className="flex items-center gap-3 rounded-[6px] border border-cortex-border/50 bg-cortex-bg-secondary/50 px-3 py-2">
          <span className="font-mono text-[9px] uppercase tracking-[0.12em] text-cortex-text-muted shrink-0">Vault path</span>
          <span className="font-mono text-[11px] text-cortex-text truncate">{user.personal_storage_path}</span>
        </div>
      )}
    </div>
  );
}

// ─── root page ─────────────────────────────────────────────────────────────────

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [tab, setTab] = useState("profile");
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState("");

  useEffect(() => {
    let alive = true;
    async function load() {
      try {
        const data = await apiGetMe();
        if (alive) setUser(data);
      } catch (err) {
        if (alive) {
          if (err.status === 401) { router.replace("/auth"); return; }
          setFetchError(err.message || "Failed to load profile.");
        }
      } finally {
        if (alive) setLoading(false);
      }
    }
    load();
    return () => { alive = false; };
  }, [router]);

  function handleLogout() {
    clearSession();
    router.replace("/auth");
  }

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="flex items-center gap-3 text-cortex-text-muted">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-cortex-cyan/30 border-t-cortex-cyan" />
          <span className="font-mono text-[11px] uppercase tracking-[0.14em]">Loading identity…</span>
        </div>
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="mx-auto max-w-2xl py-12">
        <div className="rounded-[8px] border border-cortex-error/35 bg-cortex-error/8 px-5 py-4 font-mono text-sm text-cortex-error">
          {fetchError}
        </div>
      </div>
    );
  }

  return (
    <div className="animate-cortex-fade-in mx-auto grid w-full max-w-3xl gap-6 py-2">
      {/* page header */}
      <div className="flex items-start justify-between gap-4">
        <div className="grid gap-0.5">
          <div className="flex items-center gap-2 mb-1">
            <div className="h-[5px] w-[5px] rounded-full bg-cortex-cyan shadow-[0_0_7px_rgba(0,245,255,0.5)]" />
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-cortex-cyan">Identity</span>
          </div>
          <h1 className="text-xl font-semibold text-cortex-text">Profile</h1>
          <p className="text-[13px] text-cortex-text-muted">Manage your Cortex identity and security.</p>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          className="shrink-0 rounded-[6px] border border-cortex-border bg-transparent px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.12em] text-cortex-text-muted transition-all hover:border-cortex-error/40 hover:text-cortex-error"
        >
          Sign out
        </button>
      </div>

      {/* profile card */}
      <ProfileCard user={user} />

      {/* tab editor */}
      <div className="rounded-[10px] border border-cortex-border bg-cortex-surface/60 backdrop-blur-xl p-6 grid gap-5">
        <TabNav active={tab} onChange={setTab} />

        <div className="animate-cortex-fade-in">
          {tab === "profile" && (
            <EditProfileSection user={user} onSaved={(updated) => setUser(prev => ({ ...prev, ...updated }))} />
          )}
          {tab === "password" && <ChangePasswordSection />}
          {tab === "vault" && <ChangeVaultPasswordSection />}
        </div>
      </div>
    </div>
  );
}
