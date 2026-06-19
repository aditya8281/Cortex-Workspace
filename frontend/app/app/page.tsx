"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import { Lock, User, Brain, Shield, Calendar, Hash } from "lucide-react";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { apiVaultStatus } from "../../src/shared/auth/cortexApi";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import PageTransition from "../../src/shared/ui/PageTransition";
import StaggerChildren from "../../src/shared/ui/StaggerChildren";
import Card from "../../src/shared/ui/Card";
import Badge from "../../src/shared/ui/Badge";
import type { VaultStatus } from "../../src/shared/types";

function AnimatedCounter({ value, duration = 1.2 }: { value: number; duration?: number }) {
  const count = useMotionValue(0);
  const rounded = useTransform(count, (v) => Math.round(v));
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const controls = animate(count, value, {
      duration,
      ease: [0.25, 0.46, 0.45, 0.94],
    });
    const unsubscribe = rounded.on("change", (v) => setDisplay(v));
    return () => {
      controls.stop();
      unsubscribe();
    };
  }, [value, count, rounded, duration]);

  return <span>{display}</span>;
}

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

  const memberCount = 1;
  const entryCount = 0;

  return (
    <DashboardShell>
      <PageTransition className="max-w-5xl mx-auto space-y-8">
        {/* ── Welcome Section ──────────────────────────────────── */}
        <div className="flex items-center gap-5">
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="relative h-14 w-14 rounded-full bg-bg-surface border border-border-subtle flex items-center justify-center text-lg font-semibold text-accent overflow-hidden shrink-0 cursor-default"
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
            {/* Glow ring on hover */}
            <motion.div
              className="absolute inset-0 rounded-full"
              initial={{ boxShadow: "0 0 0 0px rgba(6,182,212,0)" }}
              whileHover={{
                boxShadow: "0 0 0 3px rgba(6,182,212,0.3), 0 0 20px rgba(6,182,212,0.15)",
              }}
              transition={{ duration: 0.3 }}
            />
          </motion.div>
          <div>
            <h1 className="text-2xl font-semibold text-text font-display tracking-tight">
              Welcome back, {user.full_name?.split(" ")[0] || user.username}
            </h1>
            <p className="text-sm text-text-secondary mt-0.5">
              {user.role === "admin" ? (
                <span className="flex items-center gap-1.5">
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

        {/* ── Stat Cards ───────────────────────────────────────── */}
        <StaggerChildren className="grid grid-cols-2 sm:grid-cols-4 gap-4" staggerDelay={0.06}>
          <Card className="p-4 group">
            <div className="flex items-center justify-between mb-3">
              <div className="h-9 w-9 rounded-lg bg-accent-faint border border-accent/10 flex items-center justify-center">
                <Shield className="h-4 w-4 text-accent" />
              </div>
              <Badge variant="accent">Role</Badge>
            </div>
            <p className="text-2xl font-semibold text-text font-display capitalize">
              {user.role}
            </p>
            <p className="text-xs text-text-muted mt-1">Account type</p>
          </Card>

          <Card className="p-4 group">
            <div className="flex items-center justify-between mb-3">
              <div className="h-9 w-9 rounded-lg bg-accent-faint border border-accent/10 flex items-center justify-center">
                <Calendar className="h-4 w-4 text-accent" />
              </div>
              <Badge variant="default">Joined</Badge>
            </div>
            <p className="text-2xl font-semibold text-text font-display">
              {user.created_at
                ? new Date(user.created_at).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                  })
                : "—"}
            </p>
            <p className="text-xs text-text-muted mt-1">
              {user.created_at ? new Date(user.created_at).getFullYear() : "Year"}
            </p>
          </Card>

          <Card className="p-4 group">
            <div className="flex items-center justify-between mb-3">
              <div className="h-9 w-9 rounded-lg bg-accent-faint border border-accent/10 flex items-center justify-center">
                <Hash className="h-4 w-4 text-accent" />
              </div>
              <Badge variant="default">ID</Badge>
            </div>
            <p className="text-2xl font-semibold text-text font-display font-mono">
              <AnimatedCounter value={user.id} />
            </p>
            <p className="text-xs text-text-muted mt-1">User identifier</p>
          </Card>

          <Card className="p-4 group">
            <div className="flex items-center justify-between mb-3">
              <div className="h-9 w-9 rounded-lg bg-accent-faint border border-accent/10 flex items-center justify-center">
                <Lock className="h-4 w-4 text-accent" />
              </div>
              {vaultStatus && (
                <motion.span
                  className={`h-2.5 w-2.5 rounded-full ${vaultStatus.locked ? "bg-error" : "bg-success"}`}
                  animate={{
                    boxShadow: vaultStatus.locked
                      ? ["0 0 4px rgba(239,68,68,0.4)", "0 0 10px rgba(239,68,68,0.6)", "0 0 4px rgba(239,68,68,0.4)"]
                      : ["0 0 4px rgba(34,197,94,0.4)", "0 0 10px rgba(34,197,94,0.6)", "0 0 4px rgba(34,197,94,0.4)"],
                  }}
                  transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                />
              )}
            </div>
            <p className="text-2xl font-semibold text-text font-display">
              {vaultStatus ? (vaultStatus.locked ? "Locked" : "Active") : "—"}
            </p>
            <p className="text-xs text-text-muted mt-1">Vault status</p>
          </Card>
        </StaggerChildren>

        {/* ── Quick Actions ────────────────────────────────────── */}
        <div>
          <h2 className="text-xs font-mono tracking-[0.2em] uppercase text-text-muted mb-4">
            Quick Actions
          </h2>
          <StaggerChildren className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" staggerDelay={0.06}>
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
                    {vaultStatus
                      ? vaultStatus.locked
                        ? "Locked · Click to unlock"
                        : "Unlocked · Active"
                      : "Loading..."}
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
                    Knowledge base and entries
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
                    Manage your account settings
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
                      Manage users and system
                    </p>
                  </div>
                </div>
              </Card>
            )}
          </StaggerChildren>
        </div>
      </PageTransition>
    </DashboardShell>
  );
}
