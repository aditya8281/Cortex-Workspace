"use client";

import { useState, useEffect } from "react";
import { Button, Card, Input } from "@/components/ui/base";
import { useAuth } from "@/hooks/useAuth";

export default function SettingsPage() {
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
  });

  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || "",
        email: user.email || "",
      });
    }
  }, [user]);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Settings</h1>

      <Card>
        <h2 className="text-xl font-bold mb-4">Profile Settings</h2>
        <div className="space-y-4">
          <Input
            label="Full Name"
            value={formData.full_name}
            onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
          />
          <Input
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          />
          <Button>Save Changes</Button>
        </div>
      </Card>

      <Card>
        <h2 className="text-xl font-bold mb-4">Privacy & Security</h2>
        <div className="space-y-2">
          <Button variant="secondary">Change Password</Button>
          <Button variant="secondary">Enable 2FA</Button>
        </div>
      </Card>
    </div>
  );
}
