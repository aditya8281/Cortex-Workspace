"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { apiVaultStatus } from "../../src/shared/auth/cortexApi";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import Card from "../../src/shared/ui/Card";
import Button from "../../src/shared/ui/Button";
import type { VaultStatus } from "../../src/shared/types";

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [vaultStatus, setVaultStatus] = useState<VaultStatus | null>(null);

  useEffect(() => {
    if (!loading && !user) router.replace("/auth");
  }, [user, loading, router]);

  useEffect(() => {
    if (!user) return;
    apiVaultStatus().then(setVaultStatus).catch(() => {});
  }, [user]);

  if (loading || !user) return null;

  const initials = (user.full_name || user.username || "?").charAt(0).toUpperCase();

  return (
    <DashboardShell>
      <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
        <div className="appear-stagger grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="stat-card p-4 rounded-lg bg-bg-card border border-border">
            <p className="text-xs text-text-muted mb-1">Role</p>
            <p className="text-lg font-semibold text-text capitalize">{user.role}</p>
          </div>
          <div className="stat-card p-4 rounded-lg bg-bg-card border border-border">
            <p className="text-xs text-text-muted mb-1">Joined</p>
            <p className="text-lg font-semibold text-text">{user.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}</p>
          </div>
          <div className="stat-card p-4 rounded-lg bg-bg-card border border-border">
            <p className="text-xs text-text-muted mb-1">User ID</p>
            <p className="text-lg font-semibold text-text font-mono">#{user.id}</p>
          </div>
          <div className="stat-card p-4 rounded-lg bg-bg-card border border-border">
            <p className="text-xs text-text-muted mb-1">Vault</p>
            <p className="text-lg font-semibold text-text">{vaultStatus ? (vaultStatus.locked ? "Locked" : "Active") : "..."}</p>
          </div>
        </div>

        <div className="page-header flex items-center gap-4">
          <div className="h-12 w-12 rounded-full bg-bg-elevated border border-border flex items-center justify-center text-lg font-semibold text-accent overflow-hidden shrink-0">
            {user.profile_photo ? (
              <img src={`/api/v1/me/profile/photo/${user.id}`} alt="" className="h-full w-full object-cover" onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
            ) : (
              initials
            )}
          </div>
          <div>
            <h1 className="text-xl font-semibold text-text">Welcome back, {user.full_name?.split(" ")[0] || user.username}</h1>
            <p className="text-sm text-text-muted">{user.role === "admin" ? "Admin" : "Member"} · @{user.username}</p>
          </div>
        </div>

        <div className="appear-stagger grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card hover className="interactive-card p-5" onClick={() => router.push("/vault")}>
            <div className="flex items-center justify-between mb-3">
              <div className="h-9 w-9 rounded-md bg-accent-faint border border-accent/10 flex items-center justify-center">
                <svg className="h-4.5 w-4.5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                </svg>
              </div>
              {vaultStatus && (
                <span className={`h-2 w-2 rounded-full ${vaultStatus.locked ? "bg-error" : "bg-success"}`} />
              )}
            </div>
            <h3 className="text-sm font-medium text-text mb-1">Secure Vault</h3>
            <p className="text-xs text-text-muted">
              {vaultStatus ? (vaultStatus.locked ? "Locked · Click to unlock" : "Unlocked · Active") : "Loading..."}
            </p>
          </Card>

          <Card hover className="interactive-card p-5" onClick={() => router.push("/profile")}>
            <div className="flex items-center justify-between mb-3">
              <div className="h-9 w-9 rounded-md bg-accent-faint border border-accent/10 flex items-center justify-center">
                <svg className="h-4.5 w-4.5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                </svg>
              </div>
            </div>
            <h3 className="text-sm font-medium text-text mb-1">Profile</h3>
            <p className="text-xs text-text-muted">Manage your account settings</p>
          </Card>

          <Card hover className="interactive-card p-5" onClick={() => router.push("/memory")}>
            <div className="flex items-center justify-between mb-3">
              <div className="h-9 w-9 rounded-md bg-accent-faint border border-accent/10 flex items-center justify-center">
                <svg className="h-4.5 w-4.5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5" />
                </svg>
              </div>
            </div>
            <h3 className="text-sm font-medium text-text mb-1">Memory</h3>
            <p className="text-xs text-text-muted">Knowledge base and entries</p>
          </Card>

          {user.role === "admin" && (
            <Card hover className="interactive-card p-5" onClick={() => router.push("/admin")}>
              <div className="flex items-center justify-between mb-3">
                <div className="h-9 w-9 rounded-md bg-accent-faint border border-accent/10 flex items-center justify-center">
                  <svg className="h-4.5 w-4.5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                  </svg>
                </div>
              </div>
              <h3 className="text-sm font-medium text-text mb-1">Admin Panel</h3>
              <p className="text-xs text-text-muted">Manage users and system</p>
            </Card>
          )}
        </div>

        <Card className="p-5">
          <h2 className="text-sm font-medium text-text mb-3">Account Details</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <span className="text-xs text-text-muted font-bold uppercase tracking-wider block mb-1">User ID</span>
              <span className="text-sm text-text font-mono">#{user.id}</span>
            </div>
            <div>
              <span className="text-xs text-text-muted font-bold uppercase tracking-wider block mb-1">Role</span>
              <span className="text-sm text-text capitalize">{user.role}</span>
            </div>
            <div>
              <span className="text-xs text-text-muted font-bold uppercase tracking-wider block mb-1">Created</span>
              <span className="text-sm text-text">{user.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}</span>
            </div>
            <div>
              <span className="text-xs text-text-muted font-bold uppercase tracking-wider block mb-1">Storage</span>
              <span className="text-sm text-text truncate block" title={user.storage_root || ""}>{user.storage_root ? user.storage_root.split("/").pop() : "—"}</span>
            </div>
          </div>
        </Card>

        <div className="flex gap-3 flex-wrap">
          <Button variant="secondary" size="sm" onClick={() => router.push("/vault")}>Open Vault</Button>
          <Button variant="secondary" size="sm" onClick={() => router.push("/memory")}>Memory</Button>
          <Button variant="secondary" size="sm" onClick={() => router.push("/profile")}>Edit Profile</Button>
          <Button variant="ghost" size="sm" onClick={() => router.push("/settings")}>Settings</Button>
        </div>
      </div>
    </DashboardShell>
  );
}
