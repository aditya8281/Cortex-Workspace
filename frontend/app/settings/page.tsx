"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { apiDeleteAccount } from "../../src/shared/auth/cortexApi";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import Button from "../../src/shared/ui/Button";
import Input from "../../src/shared/ui/Input";
import Card from "../../src/shared/ui/Card";
import { AlertTriangle, Trash2, User, Shield, Hash, HardDrive, ExternalLink } from "lucide-react";

export default function SettingsPage() {
  const router = useRouter();
  const { user, logout, loading: authLoading } = useAuth();

  useEffect(() => { if (!authLoading && !user) router.replace("/auth"); }, [user, authLoading, router]);

  const [deletePassword, setDeletePassword] = useState("");
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState("");
  const [deleteConfirmStep, setDeleteConfirmStep] = useState(false);

  const fadeUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { type: "spring" as const, damping: 25, stiffness: 200 },
  };

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

        <div className="space-y-6">
          <motion.div {...fadeUp}>
            <Card className="p-5">
              <h2 className="text-sm font-medium text-text mb-4">Account Information</h2>
              <div className="grid gap-0">
                <div className="flex items-center justify-between py-2.5 border-b border-border-subtle">
                  <span className="text-xs text-text-muted flex items-center gap-2">
                    <User className="h-3.5 w-3.5" />
                    Username
                  </span>
                  <span className="text-sm text-text font-mono">@{user.username}</span>
                </div>
                <div className="flex items-center justify-between py-2.5 border-b border-border-subtle">
                  <span className="text-xs text-text-muted flex items-center gap-2">
                    <Shield className="h-3.5 w-3.5" />
                    Role
                  </span>
                  <span className="text-sm text-text capitalize">{user.role}</span>
                </div>
                <div className="flex items-center justify-between py-2.5 border-b border-border-subtle">
                  <span className="text-xs text-text-muted flex items-center gap-2">
                    <Hash className="h-3.5 w-3.5" />
                    User ID
                  </span>
                  <span className="text-sm text-text-muted font-mono">#{user.id}</span>
                </div>
                {user.storage_root && (
                  <div className="flex items-center justify-between py-2.5">
                    <span className="text-xs text-text-muted flex items-center gap-2">
                      <HardDrive className="h-3.5 w-3.5" />
                      Storage Root
                    </span>
                    <span className="text-sm text-text font-mono truncate max-w-[280px]">{user.storage_root}</span>
                  </div>
                )}
              </div>
              <div className="mt-4 flex justify-end">
                <Button variant="secondary" size="sm" onClick={() => router.push("/profile")}>
                  <ExternalLink className="h-3.5 w-3.5" />
                  Edit Profile
                </Button>
              </div>
            </Card>
          </motion.div>

          <motion.div {...fadeUp} transition={{ ...fadeUp.transition, delay: 0.08 }}>
            <Card className="p-5 border-error/20 bg-error/[0.02]">
              <div className="flex items-center gap-3 mb-4">
                <div className="h-9 w-9 rounded-md bg-error/10 border border-error/15 flex items-center justify-center shrink-0">
                  <AlertTriangle className="h-4.5 w-4.5 text-error" />
                </div>
                <div>
                  <h2 className="text-sm font-medium text-error">Delete Account</h2>
                  <p className="text-xs text-text-muted">Permanently delete your account and all associated data.</p>
                </div>
              </div>

              {!deleteConfirmStep ? (
                <div className="flex justify-end">
                  <Button variant="danger" size="sm" onClick={() => setDeleteConfirmStep(true)}>
                    <Trash2 className="h-3.5 w-3.5" />
                    Delete account
                  </Button>
                </div>
              ) : (
                <AnimatePresence mode="wait">
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ type: "spring", damping: 25, stiffness: 300 }}
                    className="overflow-hidden"
                  >
                    <div className="grid gap-3">
                      <div className="rounded-xl bg-error/10 border border-error/15 p-3">
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
                          <Trash2 className="h-3.5 w-3.5" />
                          Permanently delete
                        </Button>
                      </div>
                    </div>
                  </motion.div>
                </AnimatePresence>
              )}
            </Card>
          </motion.div>
        </div>
      </div>
    </DashboardShell>
  );
}
