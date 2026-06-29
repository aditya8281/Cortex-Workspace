"use client";

import { useEffect, useState } from "react";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Skeleton } from "@/shared/ui/Skeleton";
import { accessControl, type Role, type Permission } from "../api";

export function AccessControlCard() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const [rolesRes, permsRes] = await Promise.all([
          accessControl.roles(),
          accessControl.permissions(),
        ]);
        if (!cancelled) {
          setRoles(Array.isArray(rolesRes) ? rolesRes : []);
          setPermissions(Array.isArray(permsRes) ? permsRes : []);
        }
      } catch {
        if (!cancelled) setError("Failed to load access control data");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <Card>
        <h3 className="text-sm font-semibold text-text-primary">Access Control</h3>
        <p className="mt-1 text-xs text-danger">{error}</p>
      </Card>
    );
  }

  return (
    <Card>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary">Access Control</h3>
        {!loading && (
          <span className="text-xs text-text-muted tabular-nums">
            {permissions.length} permission{permissions.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      <div className="mt-3">
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-20" />
          </div>
        ) : roles.length === 0 ? (
          <p className="text-xs text-text-muted">No roles assigned</p>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {roles.map((role) => (
              <Badge key={role.id}>{role.name}</Badge>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}
