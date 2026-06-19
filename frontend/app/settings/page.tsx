"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { apiDeleteAccount } from "../../src/shared/auth/cortexApi";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import Button from "../../src/shared/ui/Button";
import Input from "../../src/shared/ui/Input";
import Card from "../../src/shared/ui/Card";

export default function SettingsPage() {
  const router = useRouter();
  const { user, logout, loading: authLoading } = useAuth();

  useEffect(() => { if (!authLoading && !user) router.replace("/auth"); }, [user, authLoading, router]);

  const [deletePassword, setDeletePassword] = useState("");
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState("");
  const [deleteConfirmStep, setDeleteConfirmStep] = useState(false);

  async function handleDeleteAccount() {
    if (!deletePassword) {
      setDeleteError("Password is required to delete your account");
      return;
    }
    setDeleteLoading(true);
    setDeleteError("");
    try {
      await apiDeleteAccount(deletePassword);
      await logout();
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Failed to delete account");
      setDeleteLoading(false);
    }
  }

  if (authLoading || !user) return null;

  return (
    <DashboardShell>
      <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
        <div className="page-header">
          <h1 className="text-xl font-semibold text-text">Settings</h1>
          <p className="text-sm text-text-muted mt-1">Manage your account.</p>
        </div>

        <div className="appear-stagger space-y-6">
          <Card className="p-5">
            <h2 className="text-sm font-medium text-text mb-3">Account Information</h2>
            <div className="grid gap-2">
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-xs text-text-muted">Username</span>
                <span className="text-sm text-text font-mono">@{user.username}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-xs text-text-muted">Role</span>
                <span className="text-sm text-text capitalize">{user.role}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-xs text-text-muted">User ID</span>
                <span className="text-sm text-text-muted font-mono">#{user.id}</span>
              </div>
              {user.storage_root && (
                <div className="flex items-center justify-between py-2">
                  <span className="text-xs text-text-muted">Storage Root</span>
                  <span className="text-sm text-text font-mono truncate max-w-[280px]">{user.storage_root}</span>
                </div>
              )}
            </div>
            <div className="mt-4 flex justify-end">
              <Button variant="secondary" size="sm" onClick={() => router.push("/profile")}>Edit Profile</Button>
            </div>
          </Card>

          <Card className="p-5 border-error/20 bg-error/[0.02]">
            <div className="flex items-center gap-3 mb-4">
              <div className="h-8 w-8 rounded-md bg-error/10 border border-error/10 flex items-center justify-center shrink-0">
                <svg className="h-4 w-4 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                </svg>
              </div>
              <div>
                <h2 className="text-sm font-medium text-error">Delete Account</h2>
                <p className="text-xs text-text-muted">Permanently delete your account and all associated data.</p>
              </div>
            </div>

            {!deleteConfirmStep ? (
              <div className="flex justify-end">
                <Button variant="danger" size="sm" onClick={() => setDeleteConfirmStep(true)}>
                  Delete account
                </Button>
              </div>
            ) : (
              <div className="grid gap-3">
                <div className="rounded-md bg-error/10 border border-error/10 p-3">
                  <p className="text-sm text-error leading-relaxed">
                    This action is <span className="font-semibold">irreversible</span>. All your data, vault files, and settings will be permanently deleted.
                  </p>
                </div>
                <Input
                  label="Enter your password to confirm"
                  type="password"
                  placeholder="Your login password"
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleDeleteAccount()}
                />
                {deleteError && <p className="text-sm text-error bg-error/10 rounded-md px-3 py-2 border border-error/10">{deleteError}</p>}
                <div className="flex gap-3 justify-end">
                  <Button variant="ghost" size="sm" onClick={() => { setDeleteConfirmStep(false); setDeletePassword(""); setDeleteError(""); }}>
                    Cancel
                  </Button>
                  <Button variant="danger" size="sm" loading={deleteLoading} onClick={handleDeleteAccount}>
                    Permanently delete
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>
    </DashboardShell>
  );
}
