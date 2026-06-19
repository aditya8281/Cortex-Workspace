"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { apiListUsers, apiPromoteUser, apiDemoteUser, apiDeleteUser } from "../../src/shared/auth/cortexApi";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import Button from "../../src/shared/ui/Button";
import Card from "../../src/shared/ui/Card";
import { cn } from "../../src/lib/utils";
import { Shield, Users, ArrowUp, ArrowDown, Trash2, RefreshCw, Search, UserCheck, Loader2 } from "lucide-react";
import type { User } from "../../src/shared/types";

export default function AdminPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    if (!authLoading && !user) router.replace("/auth");
    if (!authLoading && user && user.role !== "admin") router.replace("/app");
  }, [user, authLoading, router]);

  useEffect(() => {
    if (!user || user.role !== "admin") return;
    fetchUsers();
  }, [user]);

  async function fetchUsers() {
    setLoading(true);
    setError("");
    try {
      const data = await apiListUsers();
      setUsers(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  }

  async function handlePromote(userId: number) {
    try { await apiPromoteUser(userId); fetchUsers(); } catch (err) { setError(err instanceof Error ? err.message : ""); }
  }

  async function handleDemote(userId: number) {
    try { await apiDemoteUser(userId); fetchUsers(); } catch (err) { setError(err instanceof Error ? err.message : ""); }
  }

  async function handleDelete(userId: number) {
    if (!confirm("Are you sure you want to delete this user? This cannot be undone.")) return;
    try { await apiDeleteUser(userId); fetchUsers(); } catch (err) { setError(err instanceof Error ? err.message : ""); }
  }

  const staggerContainer = {
    animate: {
      transition: {
        staggerChildren: 0.08,
      },
    },
  };

  const itemVariant = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { type: "spring" as const, damping: 25, stiffness: 200 },
  };

  const filteredUsers = useMemo(() => {
    if (!searchQuery.trim()) return users;
    const q = searchQuery.toLowerCase();
    return users.filter(
      (u) =>
        (u.full_name || "").toLowerCase().includes(q) ||
        (u.username || "").toLowerCase().includes(q)
    );
  }, [users, searchQuery]);

  if (authLoading || !user || user.role !== "admin") return null;

  const adminCount = users.filter((u) => u.role === "admin").length;
  const userCount = users.filter((u) => u.role === "user").length;

  return (
    <DashboardShell>
      <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
        <div className="page-header">
          <h1 className="text-xl font-semibold text-text">Admin Dashboard</h1>
          <p className="text-sm text-text-muted mt-1">Manage users and system settings.</p>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <motion.div {...itemVariant} className="stat-card p-4 rounded-lg bg-bg-card border border-border">
            <div className="flex items-center gap-2 mb-2">
              <Users className="h-4 w-4 text-text-muted" />
              <p className="text-xs text-text-muted">Total Users</p>
            </div>
            <p className="text-2xl font-semibold text-text">{users.length}</p>
          </motion.div>
          <motion.div {...itemVariant} className="stat-card p-4 rounded-lg bg-bg-card border border-border">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="h-4 w-4 text-accent" />
              <p className="text-xs text-text-muted">Admins</p>
            </div>
            <p className="text-2xl font-semibold text-accent">{adminCount}</p>
          </motion.div>
          <motion.div {...itemVariant} className="stat-card p-4 rounded-lg bg-bg-card border border-border">
            <div className="flex items-center gap-2 mb-2">
              <UserCheck className="h-4 w-4 text-text-muted" />
              <p className="text-xs text-text-muted">Regular Users</p>
            </div>
            <p className="text-2xl font-semibold text-text">{userCount}</p>
          </motion.div>
        </div>

        <Card className="overflow-hidden">
          <div className="px-5 py-3 border-b border-border-subtle flex items-center justify-between gap-4">
            <h2 className="text-sm font-medium text-text">User Management</h2>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-muted" />
                <input
                  type="text"
                  placeholder="Filter users..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="h-8 pl-8 pr-3 rounded-lg bg-bg-surface border border-border-subtle text-xs text-text placeholder:text-text-muted outline-none transition-all focus:border-accent/40 focus:ring-1 focus:ring-accent/20 w-48"
                />
              </div>
              <Button variant="ghost" size="sm" onClick={fetchUsers}>
                <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin")} />
                Refresh
              </Button>
            </div>
          </div>
          {error && <div className="px-5 py-2 bg-error/10 text-sm text-error border-b border-border">{error}</div>}
          {loading ? (
            <div className="px-5 py-8 flex flex-col items-center gap-3">
              <Loader2 className="h-6 w-6 text-accent animate-spin" />
              <p className="text-sm text-text-muted">Loading users...</p>
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="px-5 py-8 text-center text-sm text-text-muted">
              {searchQuery ? "No users match your filter." : "No users found."}
            </div>
          ) : (
            <motion.div
              variants={staggerContainer}
              initial="initial"
              animate="animate"
              className="divide-y divide-border"
            >
              {filteredUsers.map((u) => (
                <motion.div
                  key={u.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ type: "spring" as const, damping: 25, stiffness: 200 }}
                  className="px-5 py-3 flex items-center justify-between gap-4 hover:bg-bg-hover/50 transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="h-9 w-9 rounded-full bg-bg-elevated border border-border-subtle flex items-center justify-center text-xs font-medium text-accent shrink-0">
                      {(u.full_name || u.username || "?").charAt(0).toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm text-text truncate">{u.full_name || u.username}</p>
                      <p className="text-xs text-text-muted truncate">@{u.username} &middot; #{u.id}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span
                      className={cn(
                        "text-xs font-medium px-2.5 py-1 rounded-full",
                        u.role === "admin"
                          ? "bg-accent/10 text-accent border border-accent/15"
                          : "bg-bg-surface text-text-muted border border-border-subtle"
                      )}
                    >
                      {u.role}
                    </span>
                    {u.id !== user.id && (
                      <>
                        {u.role === "user" ? (
                          <Button variant="ghost" size="sm" onClick={() => handlePromote(u.id)}>
                            <ArrowUp className="h-3.5 w-3.5" />
                            Promote
                          </Button>
                        ) : (
                          <Button variant="ghost" size="sm" onClick={() => handleDemote(u.id)}>
                            <ArrowDown className="h-3.5 w-3.5" />
                            Demote
                          </Button>
                        )}
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(u.id)}>
                          <Trash2 className="h-3.5 w-3.5 text-error" />
                        </Button>
                      </>
                    )}
                  </div>
                </motion.div>
              ))}
            </motion.div>
          )}
        </Card>
      </div>
    </DashboardShell>
  );
}
