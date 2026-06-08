/**
 * Profile page — Edit profile info, avatar, and passwords.
 * Protected route — redirects to /auth if not logged in.
 */
"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import {
  apiGetProfile,
  apiUpdateProfile,
  apiUploadAvatar,
  apiRemoveAvatar,
  apiChangePassword,
  apiChangeVaultPassword,
  getProfilePhotoUrl,
} from "../../src/shared/auth/cortexApi";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import Button from "../../src/shared/ui/Button";
import Input from "../../src/shared/ui/Input";
import Card from "../../src/shared/ui/Card";

export default function ProfilePage() {
  const router = useRouter();
  const { user, loading: authLoading, updateUser } = useAuth();
  const fileInputRef = useRef(null);

  // Profile data
  const [fullName, setFullName] = useState("");
  const [nickname, setNickname] = useState("");
  const [bio, setBio] = useState("");
  const [description, setDescription] = useState("");
  const [hasPhoto, setHasPhoto] = useState(false);

  // Passwords
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [vaultCurrentPassword, setVaultCurrentPassword] = useState("");
  const [newVaultPassword, setNewVaultPassword] = useState("");
  const [confirmVaultPassword, setConfirmVaultPassword] = useState("");

  // UI state
  const [saving, setSaving] = useState(false);
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [vaultSaving, setVaultSaving] = useState(false);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [msg, setMsg] = useState({ type: "", text: "" });
  const [pwMsg, setPwMsg] = useState({ type: "", text: "" });
  const [vaultMsg, setVaultMsg] = useState({ type: "", text: "" });

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !user) router.replace("/auth");
  }, [user, authLoading, router]);

  // Load profile data
  useEffect(() => {
    if (!user) return;
    setFullName(user.full_name || "");
    setNickname(user.nickname || "");
    setBio(user.bio || "");
    setDescription(user.description || "");
    setHasPhoto(!!user.profile_photo);
  }, [user]);

  // ── Avatar ──────────────────────────────────────────────────────
  async function handleAvatarUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      setMsg({ type: "error", text: "Image must be under 2 MB." });
      return;
    }
    setAvatarUploading(true);
    try {
      await apiUploadAvatar(file);
      setHasPhoto(true);
      updateUser({ ...user, profile_photo: "uploaded" });
      setMsg({ type: "success", text: "Avatar updated." });
    } catch (err) {
      setMsg({ type: "error", text: err.message || "Upload failed." });
    } finally {
      setAvatarUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleRemoveAvatar() {
    setAvatarUploading(true);
    try {
      await apiRemoveAvatar();
      setHasPhoto(false);
      updateUser({ ...user, profile_photo: null });
      setMsg({ type: "success", text: "Avatar removed." });
    } catch (err) {
      setMsg({ type: "error", text: err.message || "Remove failed." });
    } finally {
      setAvatarUploading(false);
    }
  }

  // ── Profile info ────────────────────────────────────────────────
  async function handleSaveProfile(e) {
    e.preventDefault();
    setSaving(true);
    setMsg({ type: "", text: "" });
    try {
      const updated = await apiUpdateProfile({
        full_name: fullName.trim(),
        nickname: nickname.trim(),
        bio: bio.trim() || null,
        description: description.trim() || null,
      });
      updateUser(updated);
      setMsg({ type: "success", text: "Profile saved." });
    } catch (err) {
      setMsg({ type: "error", text: err.message || "Save failed." });
    } finally {
      setSaving(false);
    }
  }

  // ── Password change ─────────────────────────────────────────────
  async function handleChangePassword(e) {
    e.preventDefault();
    setPasswordSaving(true);
    setPwMsg({ type: "", text: "" });
    try {
      if (newPassword !== confirmPassword) {
        setPwMsg({ type: "error", text: "New passwords do not match." });
        setPasswordSaving(false);
        return;
      }
      if (newPassword.length < 8) {
        setPwMsg({ type: "error", text: "Password must be at least 8 characters." });
        setPasswordSaving(false);
        return;
      }
      await apiChangePassword({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      setPwMsg({ type: "success", text: "Password updated." });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setPwMsg({ type: "error", text: err.message || "Failed." });
    } finally {
      setPasswordSaving(false);
    }
  }

  // ── Vault password change ───────────────────────────────────────
  async function handleChangeVaultPassword(e) {
    e.preventDefault();
    setVaultSaving(true);
    setVaultMsg({ type: "", text: "" });
    try {
      if (newVaultPassword !== confirmVaultPassword) {
        setVaultMsg({ type: "error", text: "Vault passwords do not match." });
        setVaultSaving(false);
        return;
      }
      if (newVaultPassword.length < 8) {
        setVaultMsg({ type: "error", text: "Vault password must be at least 8 characters." });
        setVaultSaving(false);
        return;
      }
      await apiChangeVaultPassword({
        account_password: vaultCurrentPassword,
        new_vault_password: newVaultPassword,
        confirm_vault_password: confirmVaultPassword,
      });
      setVaultMsg({ type: "success", text: "Vault password updated." });
      setVaultCurrentPassword("");
      setNewVaultPassword("");
      setConfirmVaultPassword("");
    } catch (err) {
      setVaultMsg({ type: "error", text: err.message || "Failed." });
    } finally {
      setVaultSaving(false);
    }
  }

  if (authLoading || !user) return null;

  const initials = (user.full_name || user.username || "?").charAt(0).toUpperCase();

  return (
    <DashboardShell>
      <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
        {/* ── Avatar Section ──────────────────────────────────── */}
        <Card className="p-6">
          <h2 className="text-sm font-medium text-text mb-4">Profile Photo</h2>
          <div className="flex items-center gap-5">
            <div className="relative group">
              <div className="h-20 w-20 rounded-full bg-bg-elevated border border-border flex items-center justify-center overflow-hidden">
                {hasPhoto ? (
                  <img
                    src={getProfilePhotoUrl()}
                    alt="Avatar"
                    className="h-full w-full object-cover"
                    onError={() => setHasPhoto(false)}
                  />
                ) : (
                  <span className="text-2xl font-medium text-accent">{initials}</span>
                )}
              </div>
              {avatarUploading && (
                <div className="absolute inset-0 rounded-full bg-black/50 flex items-center justify-center">
                  <svg className="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                </div>
              )}
            </div>
            <div className="flex flex-col gap-2">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={handleAvatarUpload}
              />
              <Button
                size="sm"
                variant="secondary"
                onClick={() => fileInputRef.current?.click()}
                loading={avatarUploading}
              >
                Upload photo
              </Button>
              {hasPhoto && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handleRemoveAvatar}
                  disabled={avatarUploading}
                >
                  Remove
                </Button>
              )}
              <p className="text-[11px] text-text-muted">JPEG, PNG, or WebP. Max 2 MB.</p>
            </div>
          </div>
        </Card>

        {/* ── Profile Info ────────────────────────────────────── */}
        <Card className="p-6">
          <h2 className="text-sm font-medium text-text mb-4">Profile Information</h2>
          <form onSubmit={handleSaveProfile} className="grid gap-4">
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Full name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Ada Lovelace"
              />
              <Input
                label="Nickname"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                placeholder="ada"
              />
            </div>
            <div className="grid gap-1.5">
              <label className="text-xs font-medium text-text-secondary">Bio</label>
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="One sentence about yourself."
                rows={2}
                className="w-full rounded-md bg-bg-surface border border-border px-3 py-2 text-sm text-text placeholder:text-text-muted outline-none transition-colors focus:border-accent/40 focus:ring-1 focus:ring-accent/20 resize-none"
              />
            </div>
            <div className="grid gap-1.5">
              <label className="text-xs font-medium text-text-secondary">About</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Expanded description for Cortex context..."
                rows={3}
                className="w-full rounded-md bg-bg-surface border border-border px-3 py-2 text-sm text-text placeholder:text-text-muted outline-none transition-colors focus:border-accent/40 focus:ring-1 focus:ring-accent/20 resize-none"
              />
            </div>

            {msg.text && (
              <p className={`text-xs rounded-md px-3 py-2 ${
                msg.type === "error" ? "text-error bg-error-muted" : "text-success bg-success-muted"
              }`}>{msg.text}</p>
            )}

            <div className="flex justify-end">
              <Button type="submit" loading={saving}>Save changes</Button>
            </div>
          </form>
        </Card>

        {/* ── Change Password ─────────────────────────────────── */}
        <Card className="p-6">
          <h2 className="text-sm font-medium text-text mb-1">Change Password</h2>
          <p className="text-xs text-text-muted mb-4">Used for logging into your account.</p>
          <form onSubmit={handleChangePassword} className="grid gap-4">
            <Input
              label="Current password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
            />
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="New password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="new-password"
              />
              <Input
                label="Confirm new password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="new-password"
              />
            </div>

            {pwMsg.text && (
              <p className={`text-xs rounded-md px-3 py-2 ${
                pwMsg.type === "error" ? "text-error bg-error-muted" : "text-success bg-success-muted"
              }`}>{pwMsg.text}</p>
            )}

            <div className="flex justify-end">
              <Button type="submit" loading={passwordSaving} variant="secondary">
                Update password
              </Button>
            </div>
          </form>
        </Card>

        {/* ── Change Vault Password ───────────────────────────── */}
        <Card className="p-6">
          <h2 className="text-sm font-medium text-text mb-1">Change Vault Password</h2>
          <p className="text-xs text-text-muted mb-4">
            Used exclusively for encrypting your private files. Never used for login.
          </p>
          <form onSubmit={handleChangeVaultPassword} className="grid gap-4">
            <Input
              label="Current account password"
              type="password"
              value={vaultCurrentPassword}
              onChange={(e) => setVaultCurrentPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
            />
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="New vault password"
                type="password"
                value={newVaultPassword}
                onChange={(e) => setNewVaultPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="new-password"
              />
              <Input
                label="Confirm vault password"
                type="password"
                value={confirmVaultPassword}
                onChange={(e) => setConfirmVaultPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="new-password"
              />
            </div>

            {vaultMsg.text && (
              <p className={`text-xs rounded-md px-3 py-2 ${
                vaultMsg.type === "error" ? "text-error bg-error-muted" : "text-success bg-success-muted"
              }`}>{vaultMsg.text}</p>
            )}

            <div className="flex justify-end">
              <Button type="submit" loading={vaultSaving} variant="secondary">
                Update vault password
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </DashboardShell>
  );
}
