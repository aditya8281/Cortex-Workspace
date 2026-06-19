"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { apiGetMe, apiUpdateProfile, apiUploadAvatar, apiRemoveAvatar, apiConnectGitHub, apiDisconnectGitHub, getProfilePhotoUrl } from "../../src/shared/auth/cortexApi";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import Button from "../../src/shared/ui/Button";
import Input from "../../src/shared/ui/Input";
import Card from "../../src/shared/ui/Card";

export default function ProfilePage() {
  const router = useRouter();
  const { user, updateUser, loading: authLoading } = useAuth();

  useEffect(() => { if (!authLoading && !user) router.replace("/auth"); }, [user, authLoading, router]);

  const [fullName, setFullName] = useState("");
  const [nickname, setNickname] = useState("");
  const [bio, setBio] = useState("");
  const [description, setDescription] = useState("");
  const [profileSaved, setProfileSaved] = useState(false);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState("");

  const [ghConnected, setGhConnected] = useState(false);
  const [ghUsername, setGhUsername] = useState("");
  const [ghToken, setGhToken] = useState("");
  const [ghLoading, setGhLoading] = useState(false);
  const [ghError, setGhError] = useState("");
  const [ghSaving, setGhSaving] = useState(false);

  const [photoFailed, setPhotoFailed] = useState(false);
  const [avatarLoading, setAvatarLoading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const [fieldsInit, setFieldsInit] = useState(false);
  useEffect(() => {
    if (!user || fieldsInit) return;
    setFullName(user.full_name || ""); setNickname(user.nickname || ""); setBio(user.bio || ""); setDescription(user.description || "");
    setGhUsername(user.github_username || ""); setGhConnected(!!user.github_username); setFieldsInit(true);
  }, [user, fieldsInit]);

  async function handleProfileSave() {
    setProfileLoading(true); setProfileError(""); setProfileSaved(false);
    try {
      const updated = await apiUpdateProfile({ full_name: fullName.trim(), nickname: nickname.trim(), bio: bio.trim() || undefined, description: description.trim() || undefined });
      updateUser({ ...user!, ...updated }); setProfileSaved(true); setTimeout(() => setProfileSaved(false), 2000);
    } catch (err) { setProfileError(err instanceof Error ? err.message : "Failed to save profile"); } finally { setProfileLoading(false); }
  }

  async function handleAvatarUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]; if (!file) return;
    setAvatarLoading(true);
    try { await apiUploadAvatar(file); setPhotoFailed(false); const me = await apiGetMe(); updateUser(me); }
    catch (err) { alert(err instanceof Error ? err.message : "Upload failed"); }
    finally { setAvatarLoading(false); if (fileRef.current) fileRef.current.value = ""; }
  }

  async function handleAvatarRemove() {
    if (!confirm("Remove your profile photo?")) return;
    setAvatarLoading(true);
    try { await apiRemoveAvatar(); setPhotoFailed(true); const me = await apiGetMe(); updateUser(me); }
    catch (err) { alert(err instanceof Error ? err.message : "Remove failed"); }
    finally { setAvatarLoading(false); }
  }

  async function handleGitHubConnect() {
    if (!ghUsername.trim() || !ghToken.trim()) { setGhError("Both username and token are required"); return; }
    setGhSaving(true); setGhError("");
    try { await apiConnectGitHub(ghUsername.trim(), ghToken); setGhConnected(true); setGhToken(""); const me = await apiGetMe(); updateUser(me); }
    catch (err) { setGhError(err instanceof Error ? err.message : "Failed to connect GitHub"); } finally { setGhSaving(false); }
  }

  async function handleGitHubDisconnect() {
    if (!confirm("Disconnect your GitHub account?")) return;
    setGhLoading(true);
    try { await apiDisconnectGitHub(); setGhConnected(false); setGhUsername(""); setGhToken(""); const me = await apiGetMe(); updateUser(me); }
    catch (err) { setGhError(err instanceof Error ? err.message : "Failed to disconnect GitHub"); } finally { setGhLoading(false); }
  }

  if (authLoading || !user) return null;
  const initials = (user?.full_name || user?.username || "?").charAt(0).toUpperCase();

  return (
    <DashboardShell>
      <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
        <div className="page-header">
          <h1 className="text-xl font-semibold text-text">Profile</h1>
          <p className="text-sm text-text-muted mt-1">Manage your account settings and connected services.</p>
        </div>

        <div className="appear-stagger space-y-6">
          <Card glass className="p-5">
            <h2 className="text-sm font-medium text-text mb-4">Profile Photo</h2>
            <div className="flex items-center gap-5">
              <div className="relative h-20 w-20 shrink-0">
                <div className="h-full w-full rounded-full bg-bg-elevated border border-border flex items-center justify-center text-2xl font-semibold text-accent overflow-hidden">
                  {user?.profile_photo && user?.id && !photoFailed ? <img src={getProfilePhotoUrl(user.id)} alt="" className="h-full w-full object-cover" onError={() => setPhotoFailed(true)} /> : initials}
                </div>
                {avatarLoading && <div className="absolute inset-0 rounded-full bg-black/50 flex items-center justify-center backdrop-blur-[2px]"><svg className="animate-spin h-7 w-7 text-white" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg></div>}
              </div>
              <div className="flex flex-col gap-2">
                <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={handleAvatarUpload} />
                <Button variant="secondary" size="sm" loading={avatarLoading} onClick={() => fileRef.current?.click()}>{user?.profile_photo && !photoFailed ? "Change photo" : "Upload photo"}</Button>
                {user?.profile_photo && !photoFailed && <Button variant="ghost" size="sm" onClick={handleAvatarRemove}>Remove</Button>}
                <p className="text-xs text-text-muted">JPEG, PNG, or WebP. Max 2 MB.</p>
              </div>
            </div>
          </Card>

          <Card className="p-5">
            <h2 className="text-sm font-medium text-text mb-4">Personal Information</h2>
            <div className="grid gap-3">
              <Input label="Full name" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Ada Lovelace" />
              <Input label="Nickname" value={nickname} onChange={(e) => setNickname(e.target.value)} placeholder="ada" />
              <div className="grid gap-1.5"><label className="text-xs font-medium text-text-secondary">Bio</label><textarea value={bio} onChange={(e) => setBio(e.target.value)} placeholder="A short bio about yourself..." rows={2} className="w-full rounded-md bg-bg-surface border border-border px-3 py-2 text-sm text-text placeholder:text-text-muted outline-none transition-colors resize-none focus:border-accent/40 focus:ring-1 focus:ring-accent/20" /></div>
              <div className="grid gap-1.5"><label className="text-xs font-medium text-text-secondary">Description</label><textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="A longer description..." rows={3} className="w-full rounded-md bg-bg-surface border border-border px-3 py-2 text-sm text-text placeholder:text-text-muted outline-none transition-colors resize-none focus:border-accent/40 focus:ring-1 focus:ring-accent/20" /></div>
              {profileError && <p className="text-sm text-error bg-error/10 rounded-md px-3 py-2 border border-error/10">{profileError}</p>}
              {profileSaved && <p className="text-sm text-success bg-success/10 rounded-md px-3 py-2 border border-success/10">Profile saved successfully.</p>}
              <div className="flex justify-end pt-1"><Button loading={profileLoading} onClick={handleProfileSave}>Save changes</Button></div>
            </div>
          </Card>

          <Card hover className="p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <svg className="h-5 w-5 text-text-secondary" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" /></svg>
                <div><h2 className="text-sm font-medium text-text">GitHub</h2><p className="text-xs text-text-muted">{ghConnected ? `Connected as @${user?.github_username || ghUsername}` : "Not connected"}</p></div>
              </div>
              {ghConnected && <span className="h-2 w-2 rounded-full bg-success shadow-[0_0_6px_rgba(34,197,94,0.4)]" />}
            </div>
            {!ghConnected ? (
              <div className="grid gap-3">
                <Input label="GitHub username" placeholder="octocat" value={ghUsername} onChange={(e) => setGhUsername(e.target.value)} />
                <Input label="Personal access token" type="password" placeholder="ghp_xxxxxxxxxxxx" value={ghToken} onChange={(e) => setGhToken(e.target.value)} />
                <p className="text-xs text-text-muted"><a href="https://github.com/settings/tokens" target="_blank" rel="noreferrer" className="text-accent hover:underline">Generate a token</a> with <code className="bg-bg-surface px-1 rounded">repo</code> scope for full access.</p>
                {ghError && <p className="text-sm text-error bg-error/10 rounded-md px-3 py-2 border border-error/10">{ghError}</p>}
                <div className="flex justify-end"><Button loading={ghSaving} onClick={handleGitHubConnect} size="sm">Connect</Button></div>
              </div>
            ) : (
              <div className="flex justify-end"><Button variant="ghost" size="sm" loading={ghLoading} onClick={handleGitHubDisconnect}>Disconnect</Button></div>
            )}
          </Card>

          <Card className="p-5">
            <h2 className="text-sm font-medium text-text mb-4">Account</h2>
            <div className="grid gap-3">
              <div className="flex items-center justify-between py-2 border-b border-border"><span className="text-xs text-text-muted">Username</span><span className="text-sm text-text font-mono">@{user?.username}</span></div>
              <div className="flex items-center justify-between py-2 border-b border-border"><span className="text-xs text-text-muted">Role</span><span className="text-sm text-text capitalize">{user?.role}</span></div>
              <div className="flex items-center justify-between py-2"><span className="text-xs text-text-muted">User ID</span><span className="text-sm text-text-muted font-mono">#{user?.id}</span></div>
            </div>
          </Card>
        </div>
      </div>
    </DashboardShell>
  );
}
