"use client";

import { useState, useEffect } from "react";
import { Card, Badge, Spinner, Button } from "@/components/ui/base";
import { adminService } from "@/services/api/admin";
import type { User } from "@/types/api";

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
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
    fetchUsers();
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">User Management</h1>

      {error && <p className="text-danger">{error}</p>}

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="border-b border-border">
              <tr>
                <th className="pb-2 text-gray-400">Name</th>
                <th className="pb-2 text-gray-400">Email</th>
                <th className="pb-2 text-gray-400">Role</th>
                <th className="pb-2 text-gray-400">Created</th>
                <th className="pb-2 text-gray-400">Actions</th>
              </tr>
            </thead>
            <tbody className="space-y-2">
              {users.map((user) => (
                <tr key={user.id} className="border-b border-border hover:bg-surface">
                  <td className="py-2 font-medium">{user.full_name}</td>
                  <td className="py-2 text-sm text-gray-400">{user.email}</td>
                  <td className="py-2">
                    <Badge variant={user.role === "admin" ? "danger" : "secondary"}>
                      {user.role}
                    </Badge>
                  </td>
                  <td className="py-2 text-sm text-gray-400">
                    {user.created_at
                      ? new Date(user.created_at).toLocaleDateString()
                      : "-"}
                  </td>
                  <td className="py-2">
                    <Button size="sm" variant="ghost">
                      Edit
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
