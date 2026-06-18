"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import {
  apiListUsers,
  apiPromoteUser,
  apiDemoteUser,
  apiDeleteUser,
} from "../../src/shared/auth/cortexApi";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import Button from "../../src/shared/ui/Button";
import Card from "../../src/shared/ui/Card";

export default function AdminPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
      setUsers(Array.isArray(data) ? data : data.users || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handlePromote(userId) {
    try {
      await apiPromoteUser(userId);
      fetchUsers();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDemote(userId) {
    try {
      await apiDemoteUser(userId);
      fetchUsers();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(userId) {
    if (!confirm("Are you sure you want to delete this user? This cannot be undone.")) return;
    try {
      await apiDeleteUser(userId);
      fetchUsers();
    } catch (err) {
      setError(err.message);
    }
  }

  if (authLoading || !user || user.role !== "admin") return null;

  const adminCount = users.filter((u) => u.role === "admin").length;
  const userCount = users.filter((u) => u.role === "user").length;

  return (
    <DashboardShell>
      <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
        <div>
          <h1 className="text-xl font-semibold text-text">Admin Dashboard</h1>
          <p className="text-sm text-text-muted mt-1">Manage users and system settings.</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          <Card className="p-4">
            <p className="text-xs text-text-muted mb-1">Total Users</p>
            <p className="text-2xl font-semibold text-text">{users.length}</p>
          </Card>
          <Card className="p-4">
            <p className="text-xs text-text-muted mb-1">Admins</p>
            <p className="text-2xl font-semibold text-accent">{adminCount}</p>
          </Card>
          <Card className="p-4">
            <p className="text-xs text-text-muted mb-1">Regular Users</p>
            <p className="text-2xl font-semibold text-text">{userCount}</p>
          </Card>
        </div>

        {/* User Management */}
        <Card className="overflow-hidden">
          <div className="px-5 py-3 border-b border-border flex items-center justify-between">
            <h2 className="text-sm font-medium text-text">User Management</h2>
            <Button variant="ghost" size="sm" onClick={fetchUsers}>
              Refresh
            </Button>
          </div>

          {error && (
            <div className="px-5 py-2 bg-error-muted text-xs text-error">{error}</div>
          )}

          {loading ? (
            <div className="px-5 py-8 text-center text-sm text-text-muted">Loading users…</div>
          ) : users.length === 0 ? (
            <div className="px-5 py-8 text-center text-sm text-text-muted">No users found.</div>
          ) : (
            <div className="divide-y divide-border">
              {users.map((u) => (
                <div key={u.id} className="px-5 py-3 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="h-8 w-8 rounded-full bg-bg-elevated border border-border flex items-center justify-center text-xs font-medium text-accent shrink-0">
                      {(u.full_name || u.username || "?").charAt(0).toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm text-text truncate">{u.full_name || u.username}</p>
                      <p className="text-[11px] text-text-muted truncate">@{u.username} · #{u.id}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span className={[
                      "text-[10px] font-medium px-2 py-0.5 rounded-full",
                      u.role === "admin"
                        ? "bg-accent/10 text-accent"
                        : "bg-bg-surface text-text-muted",
                    ].join(" ")}>
                      {u.role}
                    </span>

                    {u.id !== user.id && (
                      <>
                        {u.role === "user" ? (
                          <Button variant="ghost" size="sm" onClick={() => handlePromote(u.id)}>
                            Promote
                          </Button>
                        ) : (
                          <Button variant="ghost" size="sm" onClick={() => handleDemote(u.id)}>
                            Demote
                          </Button>
                        )}
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(u.id)}>
                          <svg className="h-3.5 w-3.5 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                          </svg>
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </DashboardShell>
  );
}
