"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Lock, Brain, Shield, User, Server } from "lucide-react";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { apiVaultStatus } from "../../src/shared/auth/cortexApi";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import PageTransition from "../../src/shared/ui/PageTransition";
import StaggerChildren from "../../src/shared/ui/StaggerChildren";
import Card from "../../src/shared/ui/Card";
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

  const initials = (user.full_name || user.username || "?")
    .charAt(0)
    .toUpperCase();

  const memberSince = user.created_at
    ? new Date(user.created_at).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : "—";

  return (
    <DashboardShell>
      <PageTransition className="max-w-5xl mx-auto space-y-8">
        {/* ── Hero Welcome ──────────────────────────────────── */}
        <div className="flex items-center gap-5">
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="relative h-16 w-16 rounded-full bg-accent flex items-center justify-center text-xl font-bold text-[#050508] overflow-hidden shrink-0 cursor-default"
          >
            {user.profile_photo ? (
              <img
                src={`/api/v1/me/profile/photo/${user.id}`}
                alt=""
                className="h-full w-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = "none";
                }}
              />
            ) : (
              initials
            )}
            <motion.div
              className="absolute inset-0 rounded-full"
              initial={{ boxShadow: "0 0 0 0px rgba(6,182,212,0)" }}
              whileHover={{
                boxShadow:
                  "0 0 0 3px rgba(6,182,212,0.3), 0 0 20px rgba(6,182,212,0.15)",
              }}
              transition={{ duration: 0.3 }}
            />
          </motion.div>
          <div>
            <h1 className="text-2xl font-semibold text-text font-display tracking-tight">
              Welcome back, {user.full_name?.split(" ")[0] || user.username}
            </h1>
            <p className="text-sm text-text-secondary mt-0.5 flex items-center gap-1.5">
              {user.role === "admin" ? (
                <span className="inline-flex items-center gap-1">
                  <Shield className="h-3.5 w-3.5 text-accent" />
                  Admin
                </span>
              ) : (
                "Member"
              )}{" "}
              · @{user.username}
            </p>
          </div>
        </div>

        {/* ── System Status ───────────────────────────────── */}
        <div>
          <h2 className="text-xs font-mono tracking-[0.2em] uppercase text-text-muted mb-4">
            System Status
          </h2>
          <StaggerChildren
            className="grid grid-cols-2 sm:grid-cols-4 gap-4"
            staggerDelay={0.06}
          >
            <Card className="p-4 group">
              <div className="flex items-center justify-between mb-3">
                <div className="h-9 w-9 rounded-lg bg-accent-faint border border-accent/10 flex items-center justify-center">
                  <Lock className="h-4 w-4 text-accent" />
                </div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">
                  Vault
                </span>
              </div>
              <p className="text-2xl font-semibold text-text font-display">
                {vaultStatus ? (vaultStatus.locked ? "Locked" : "Active") : "—"}
              </p>
              <p className="text-xs text-text-muted mt-1">Vault status</p>
            </Card>

            <Card className="p-4 group">
              <div className="flex items-center justify-between mb-3">
                <div className="h-9 w-9 rounded-lg bg-accent-faint border border-accent/10 flex items-center justify-center">
                  <Brain className="h-4 w-4 text-accent" />
                </div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">
                  Memory
                </span>
              </div>
              <p className="text-2xl font-semibold text-text font-display">
                0 entries
              </p>
              <p className="text-xs text-text-muted mt-1">Knowledge base</p>
            </Card>

            <Card className="p-4 group">
              <div className="flex items-center justify-between mb-3">
                <div className="h-9 w-9 rounded-lg bg-accent-faint border border-accent/10 flex items-center justify-center">
                  <User className="h-4 w-4 text-accent" />
                </div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">
                  Account
                </span>
              </div>
              <p className="text-lg font-semibold text-text font-display">
                {memberSince}
              </p>
              <p className="text-xs text-text-muted mt-1">Member since</p>
            </Card>

            <Card className="p-4 group">
              <div className="flex items-center justify-between mb-3">
                <div className="h-9 w-9 rounded-lg bg-accent-faint border border-accent/10 flex items-center justify-center">
                  <Server className="h-4 w-4 text-accent" />
                </div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">
                  Server
                </span>
              </div>
              <p className="text-2xl font-semibold text-text font-display">
                Connected
              </p>
              <p className="text-xs text-text-muted mt-1">Server status</p>
            </Card>
          </StaggerChildren>
        </div>

        {/* ── Quick Actions ────────────────────────────────── */}
        <div>
          <h2 className="text-xs font-mono tracking-[0.2em] uppercase text-text-muted mb-4">
            Quick Actions
          </h2>
          <StaggerChildren
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
            staggerDelay={0.06}
          >
            <Card
              hover
              className="p-5 cursor-pointer"
              onClick={() => router.push("/vault")}
            >
              <div className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-lg bg-accent-faint border border-accent/10 flex items-center justify-center shrink-0">
                  <Lock className="h-5 w-5 text-accent" />
                </div>
                <div className="min-w-0">
                  <h3 className="text-sm font-medium text-text">Vault</h3>
                  <p className="text-xs text-text-muted truncate">
                    Manage encrypted files
                  </p>
                </div>
              </div>
            </Card>

            <Card
              hover
              className="p-5 cursor-pointer"
              onClick={() => router.push("/memory")}
            >
              <div className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-lg bg-accent-faint border border-accent/10 flex items-center justify-center shrink-0">
                  <Brain className="h-5 w-5 text-accent" />
                </div>
                <div className="min-w-0">
                  <h3 className="text-sm font-medium text-text">Memory</h3>
                  <p className="text-xs text-text-muted truncate">
                    Knowledge base (coming soon)
                  </p>
                </div>
              </div>
            </Card>

            <Card
              hover
              className="p-5 cursor-pointer"
              onClick={() => router.push("/profile")}
            >
              <div className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-lg bg-accent-faint border border-accent/10 flex items-center justify-center shrink-0">
                  <User className="h-5 w-5 text-accent" />
                </div>
                <div className="min-w-0">
                  <h3 className="text-sm font-medium text-text">Profile</h3>
                  <p className="text-xs text-text-muted truncate">
                    Account settings
                  </p>
                </div>
              </div>
            </Card>

            {user.role === "admin" && (
              <Card
                hover
                className="p-5 cursor-pointer"
                onClick={() => router.push("/admin")}
              >
                <div className="flex items-center gap-4">
                  <div className="h-10 w-10 rounded-lg bg-accent-faint border border-accent/10 flex items-center justify-center shrink-0">
                    <Shield className="h-5 w-5 text-accent" />
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-sm font-medium text-text">Admin</h3>
                    <p className="text-xs text-text-muted truncate">
                      User management (admin only)
                    </p>
                  </div>
                </div>
              </Card>
            )}
          </StaggerChildren>
        </div>

        {/* ── Recent Activity ──────────────────────────────── */}
        <div>
          <h2 className="text-xs font-mono tracking-[0.2em] uppercase text-text-muted mb-4">
            Recent Activity
          </h2>
          <Card className="p-8 text-center">
            <p className="text-sm text-text-muted">
              Activity tracking coming soon
            </p>
          </Card>
        </div>
      </PageTransition>
    </DashboardShell>
  );
}
