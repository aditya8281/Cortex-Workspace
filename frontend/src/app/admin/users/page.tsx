"use client";

import { useState, useEffect } from "react";
import { Card, Badge, Spinner, Button, Input } from "@/components/ui/base";
import { adminService } from "@/services/api/admin";
import type { User } from "@/types/api";

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [editFormData, setEditFormData] = useState({
    full_name: "",
    email: "",
    role: "user" as "user" | "admin",
  });
  const [saveLoading, setSaveLoading] = useState(false);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const data = await adminService.listUsers();
      setUsers(data);
    } catch (err: any) {
      setError(err.message || "Failed to fetch users");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const openEditModal = (user: User) => {
    setEditingUser(user);
    setEditFormData({
      full_name: user.full_name || "",
      email: user.email || "",
      role: (user.role as "user" | "admin") || "user",
    });
  };

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;
    setSaveLoading(true);
    try {
      await adminService.updateUser(editingUser.id, editFormData);
      setEditingUser(null);
      await fetchUsers();
    } catch (err: any) {
      setError(err.message || "Failed to update user");
    } finally {
      setSaveLoading(false);
    }
  };

  const handleDeleteUser = async () => {
    if (!editingUser || !window.confirm(`Are you sure you want to delete user ${editingUser.full_name}?`)) return;
    setSaveLoading(true);
    try {
      await adminService.deleteUser(editingUser.id);
      setEditingUser(null);
      await fetchUsers();
    } catch (err: any) {
      setError(err.message || "Failed to delete user");
    } finally {
      setSaveLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto animate-fade-in relative">
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-3xl font-bold font-mono tracking-wide">User Management</h1>
        <p className="text-xs text-slate-400 mt-1">Admin console to manage users, assign access privileges, and clear credentials.</p>
      </div>

      {error && <p className="text-xs text-rose-400 bg-rose-950/20 border border-rose-900/30 p-3 rounded-lg font-mono">{error}</p>}

      <Card className="bg-slate-900/40 border-slate-800/80 rounded-2xl overflow-hidden p-4">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-sans text-xs">
            <thead className="border-b border-slate-800 text-slate-400 font-mono uppercase tracking-wider">
              <tr>
                <th className="pb-3 text-[10px] font-bold">Name</th>
                <th className="pb-3 text-[10px] font-bold">Email</th>
                <th className="pb-3 text-[10px] font-bold">Role</th>
                <th className="pb-3 text-[10px] font-bold">Created</th>
                <th className="pb-3 text-[10px] font-bold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-slate-900/30 transition-colors">
                  <td className="py-3.5 font-medium text-slate-200">{user.full_name}</td>
                  <td className="py-3.5 text-slate-400 font-mono">{user.email}</td>
                  <td className="py-3.5">
                    <Badge variant={user.role === "admin" ? "danger" : "secondary"}>
                      {user.role}
                    </Badge>
                  </td>
                  <td className="py-3.5 text-slate-500 font-mono">
                    {user.created_at
                      ? new Date(user.created_at).toLocaleDateString()
                      : "-"}
                  </td>
                  <td className="py-3.5 text-right">
                    <Button size="sm" variant="ghost" onClick={() => openEditModal(user)} className="text-cyan-400 hover:text-cyan-300">
                      Edit
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Edit User Modal Dialog */}
      {editingUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <Card className="w-full max-w-md p-6 bg-slate-900 border-slate-800/80 rounded-2xl shadow-2xl relative">
            <h2 className="text-sm font-mono font-bold tracking-wider text-slate-200 uppercase mb-4 pb-2 border-b border-slate-800">
              Edit User Privileges
            </h2>

            <form onSubmit={handleUpdateUser} className="space-y-4 font-sans text-xs">
              <Input
                label="Full Name"
                value={editFormData.full_name}
                onChange={(e) => setEditFormData({ ...editFormData, full_name: e.target.value })}
                required
                className="bg-slate-950 border-slate-850 focus:border-cyan-500/40 text-slate-200 text-xs"
              />
              <Input
                label="Email"
                type="email"
                value={editFormData.email}
                onChange={(e) => setEditFormData({ ...editFormData, email: e.target.value })}
                required
                className="bg-slate-950 border-slate-850 focus:border-cyan-500/40 text-slate-200 text-xs"
              />

              <div>
                <label className="text-[10px] text-slate-400 block mb-1 font-mono uppercase">Role Selection</label>
                <select
                  value={editFormData.role}
                  onChange={(e) => setEditFormData({ ...editFormData, role: e.target.value as "user" | "admin" })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-850 focus:border-cyan-500/40 text-slate-200 rounded-xl focus:outline-none"
                >
                  <option value="user">User (Standard Access)</option>
                  <option value="admin">Admin (Full Control)</option>
                </select>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-slate-800/80">
                <Button
                  type="button"
                  variant="danger"
                  onClick={handleDeleteUser}
                  disabled={saveLoading}
                  className="bg-rose-950/30 border border-rose-900/40 text-rose-400 hover:bg-rose-900/30 rounded-xl"
                >
                  Delete User
                </Button>

                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setEditingUser(null)}
                    disabled={saveLoading}
                    className="border border-slate-800 rounded-xl bg-slate-950 text-slate-300"
                  >
                    Cancel
                  </Button>
                  <Button type="submit" loading={saveLoading} className="bg-gradient-to-r from-cyan-600 to-blue-600 rounded-xl text-white font-semibold">
                    Save Changes
                  </Button>
                </div>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}
