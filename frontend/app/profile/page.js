"use client";

import React, { useEffect, useRef, useState } from "react";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import {
  apiChangePassword,
  apiChangeVaultPassword,
  apiGetMe,
  apiGetProfilePhotoUrl,
  apiUpdateProfile,
  apiUploadProfilePhoto,
} from "../../src/shared/auth/cortexApi";
import {
  cn,
  useField,
  Field,
  TextInput,
  PasswordInput,
  Textarea,
  Btn,
  ErrorBanner,
  SuccessBanner,
  SectionDivider,
  Panel,
} from "../../src/shared/ui/form";

const HANDLE_KEYS = ["github", "twitter", "linkedin", "website"];
const TABS = [
  { id: "profile", label: "Edit Profile" },
  { id: "password", label: "Account Password" },
  { id: "vault", label: "Vault Password" },
];

function Avatar({ name, photo, size = "lg" }) {
  const initials = (name || "?")
    .split(" ")
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase() || "")
    .join("");
  const sizes = { sm: "h-9 w-9 text-sm", md: "h-12 w-12 text-base", lg: "h-16 w-16 text-xl" };

  if (photo) {
    return (
      <div className={cn("overflow-hidden rounded-full border border-cortex-cyan/25", sizes[size])}>
        <img
          src={apiGetProfilePhotoUrl()}
          alt={`${name || "User"} avatar`}
          className="h-full w-full object-cover"
        />
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex shrink-0 items-center justify-center rounded-full font-semibold",
        "border border-cortex-cyan/25 bg-cortex-cyan/10 text-cortex-cyan",
        "shadow-[0_0_20px_rgba(0,245,255,0.12)]",
        sizes[size]
      )}
    >
      {initials}
    </div>
  );
}

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

function ProfileSummary({ profile, onPhotoPick, uploading }) {
  const inputRef = useRef(null);
  const name = profile?.full_name || profile?.username || "Unknown";

  return (
    <Panel className="p-5">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <Avatar name={name} photo={profile?.profile_photo} size="lg" />
          <div className="grid gap-1">
            <div className="flex items-center gap-2">
              <div className="h-[5px] w-[5px] rounded-full bg-cortex-cyan" />
              <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-cortex-cyan">Identity</span>
            </div>
            <h1 className="text-xl font-semibold text-cortex-text">{name}</h1>
            <p className="text-[13px] text-cortex-text-muted">@{profile?.nickname || profile?.username || "user"}</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Btn
            type="button"
            variant="outline"
            onClick={() => inputRef.current?.click()}
            loading={uploading}
          >
            Change Photo
          </Btn>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={onPhotoPick}
          />
        </div>
      </div>

      <div className="mt-4 grid gap-2 text-[12px] text-cortex-text-muted sm:grid-cols-3">
        <div className="rounded-[6px] border border-cortex-border/50 bg-cortex-bg-secondary/30 px-3 py-2">
          <div className="font-mono text-[10px] uppercase tracking-[0.12em]">Username</div>
          <div className="mt-1 text-cortex-text">{profile?.username || "—"}</div>
        </div>
        <div className="rounded-[6px] border border-cortex-border/50 bg-cortex-bg-secondary/30 px-3 py-2">
          <div className="font-mono text-[10px] uppercase tracking-[0.12em]">Role</div>
          <div className="mt-1 text-cortex-text">{profile?.role || "user"}</div>
        </div>
        <div className="rounded-[6px] border border-cortex-border/50 bg-cortex-bg-secondary/30 px-3 py-2">
          <div className="font-mono text-[10px] uppercase tracking-[0.12em]">Bio</div>
          <div className="mt-1 line-clamp-2 text-cortex-text">{profile?.bio || "—"}</div>
        </div>
      </div>
    </Panel>
  );
}

function EditProfileSection({ user, onSaved }) {
  const [fullName, onFullName, setFullName] = useField(user?.full_name || "");
  const [nickname, onNickname, setNickname] = useField(user?.nickname || "");
  const [bio, onBio, setBio] = useField(user?.bio || "");
  const [description, onDescription, setDescription] = useField(user?.description || "");
  const [handles, setHandles] = useState(user?.handles || {});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    setFullName(user?.full_name || "");
    setNickname(user?.nickname || "");
    setBio(user?.bio || "");
    setDescription(user?.description || "");
    setHandles(user?.handles || {});
  }, [user, setBio, setDescription, setFullName, setNickname]);

  async function handleSave(e) {
    e.preventDefault();
    if (!fullName.trim()) {
      setError("Full name is required.");
      return;
    }
    if (!nickname.trim()) {
      setError("Nickname is required.");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const cleanHandles = Object.fromEntries(Object.entries(handles).filter(([, value]) => value?.trim()));
      const updated = await apiUpdateProfile({
        full_name: fullName.trim(),
        nickname: nickname.trim(),
        bio: bio.trim() || null,
        description: description.trim() || null,
        handles: cleanHandles,
      });
      setSuccess("Profile updated.");
      onSaved?.(updated);
      window.setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.message || "Failed to update profile.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="grid gap-4" onSubmit={handleSave} noValidate>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label="Full Name *" id="pf-fullname">
          <TextInput id="pf-fullname" value={fullName} onChange={onFullName} placeholder="Ada Lovelace" autoComplete="name" disabled={loading} />
        </Field>
        <Field label="Nickname *" id="pf-nickname">
          <TextInput id="pf-nickname" value={nickname} onChange={onNickname} placeholder="ada" disabled={loading} />
        </Field>
      </div>

      <Field label="Bio" id="pf-bio" hint="Short summary - visible across Cortex.">
        <Textarea id="pf-bio" value={bio} onChange={onBio} placeholder="Engineer building AI-native systems." rows={2} disabled={loading} />
      </Field>

      <Field label="About" id="pf-description" hint="Extended context. Cortex uses this to personalise responses.">
        <Textarea id="pf-description" value={description} onChange={onDescription} placeholder="I focus on distributed systems, Rust, and LLM tooling..." rows={3} disabled={loading} />
      </Field>

      <SectionDivider label="Handles" />
      <div className="grid gap-2">
        {HANDLE_KEYS.map((key) => (
          <HandleRow
            key={key}
            handleKey={key}
            value={handles?.[key] || ""}
            onChange={(e) => setHandles((current) => ({ ...(current || {}), [key]: e.target.value }))}
          />
        ))}
      </div>

      <ErrorBanner message={error} />
      <SuccessBanner message={success} />
      <Btn type="submit" loading={loading} className="w-full sm:w-auto">
        Save Profile
      </Btn>
    </form>
  );
}

function ChangePasswordSection() {
  const [current, onCurrent] = useField();
  const [next, onNext] = useField();
  const [confirm, onConfirm] = useField();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleSave(e) {
    e.preventDefault();
    if (!current) {
      setError("Current password is required.");
      return;
    }
    if (next.length < 8) {
      setError("New password must be at least 8 characters.");
      return;
    }
    if (!/[a-zA-Z]/.test(next) || !/[0-9]/.test(next)) {
      setError("New password must contain a letter and a number.");
      return;
    }
    if (next !== confirm) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");
    try {
      await apiChangePassword({
        current_password: current,
        new_password: next,
        confirm_password: confirm,
      });
      setSuccess("Account password changed.");
      window.setTimeout(() => setSuccess(""), 3000);
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
      <Btn type="submit" loading={loading}>
        Update Password
      </Btn>
    </form>
  );
}

function ChangeVaultPasswordSection() {
  const [accountPw, onAccountPw] = useField();
  const [vaultNext, onVaultNext] = useField();
  const [vaultConfirm, onVaultConfirm] = useField();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleSave(e) {
    e.preventDefault();
    if (!accountPw) {
      setError("Account password is required to change vault password.");
      return;
    }
    if (vaultNext.length < 8) {
      setError("Vault password must be at least 8 characters.");
      return;
    }
    if (!/[a-zA-Z]/.test(vaultNext) || !/[0-9]/.test(vaultNext)) {
      setError("Vault password must contain a letter and a number.");
      return;
    }
    if (vaultNext !== vaultConfirm) {
      setError("Vault passwords do not match.");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");
    try {
      await apiChangeVaultPassword({
        account_password: accountPw,
        new_vault_password: vaultNext,
        confirm_vault_password: vaultConfirm,
      });
      setSuccess("Vault password updated.");
      window.setTimeout(() => setSuccess(""), 3000);
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
      <Btn type="submit" loading={loading}>
        Update Vault Password
      </Btn>
    </form>
  );
}

function TabNav({ active, onChange }) {
  return (
    <div className="flex gap-1 rounded-[8px] border border-cortex-border bg-cortex-bg-secondary/60 p-1">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => onChange(tab.id)}
          className={cn(
            "flex-1 rounded-[6px] px-3 py-2 text-xs font-medium tracking-wide transition-all duration-150 focus:outline-none",
            active === tab.id
              ? "border border-cortex-border bg-cortex-surface text-cortex-text shadow-sm"
              : "border border-transparent text-cortex-text-muted hover:text-cortex-text"
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

export default function ProfilePage() {
  const { user, token, login, updateUser, logout } = useAuth();
  const [profile, setProfile] = useState(user || null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("profile");

  useEffect(() => {
    let alive = true;

    async function load() {
      setLoading(true);
      try {
        const me = await apiGetMe();
        if (!alive) return;
        setProfile((current) => ({ ...(current || {}), ...me }));
        updateUser((current) => ({ ...(current || {}), ...me }));
      } catch (err) {
        if (!alive) return;
        setError(err.message || "Failed to load profile.");
      } finally {
        if (alive) setLoading(false);
      }
    }

    load();
    return () => {
      alive = false;
    };
  }, [updateUser]);

  async function handlePhotoPick(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    setUploading(true);
    setError("");
    try {
      await apiUploadProfilePhoto(file);
      const refreshed = await apiGetMe();
      setProfile(refreshed);
      updateUser((current) => ({ ...(current || {}), ...refreshed }));
    } catch (err) {
      setError(err.message || "Failed to upload profile photo.");
    } finally {
      setUploading(false);
    }
  }

  async function handleProfileSaved(updated) {
    const merged = { ...(profile || {}), ...(updated || {}) };
    setProfile(merged);
    updateUser(merged);
    if (token) {
      await login(token, merged);
    }
  }

  async function handleLogout() {
    logout();
  }

  const displayProfile = profile || user;

  if (loading && !displayProfile) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="flex items-center gap-3 text-cortex-text-muted">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-cortex-cyan/30 border-t-cortex-cyan" />
          <span className="font-mono text-[11px] uppercase tracking-[0.14em]">Loading identity…</span>
        </div>
      </div>
    );
  }

  if (error && !displayProfile) {
    return (
      <div className="mx-auto max-w-2xl py-12">
        <div className="rounded-[8px] border border-cortex-error/35 bg-cortex-error/8 px-5 py-4 font-mono text-sm text-cortex-error">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="animate-cortex-fade-in mx-auto grid w-full max-w-3xl gap-6 py-2">
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

      <ProfileSummary profile={displayProfile} onPhotoPick={handlePhotoPick} uploading={uploading} />
      {error ? <ErrorBanner message={error} /> : null}

      <div className="rounded-[10px] border border-cortex-border bg-cortex-surface/60 backdrop-blur-xl p-6 grid gap-5">
        <TabNav active={activeTab} onChange={setActiveTab} />

        <div className="animate-cortex-fade-in">
          {activeTab === "profile" && <EditProfileSection user={displayProfile} onSaved={handleProfileSaved} />}
          {activeTab === "password" && <ChangePasswordSection />}
          {activeTab === "vault" && <ChangeVaultPasswordSection />}
        </div>
      </div>
    </div>
  );
}
