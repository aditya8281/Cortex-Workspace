"use client";

import { useState, useEffect } from "react";
import { Button, Card, Input } from "@/components/ui/base";
import { useAuth } from "@/hooks/useAuth";
import { authService } from "@/services/api/auth";
import { AlertCircle, CheckCircle2, ShieldAlert } from "lucide-react";

export default function SettingsPage() {
  const { user, checkAuth } = useAuth();
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
  });

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPasswordFields, setShowPasswordFields] = useState(false);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);

  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || "",
        email: user.email || "",
      });
    }
  }, [user]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatus(null);

    // Form validation
    if (!formData.full_name.trim() || !formData.email.trim()) {
      setStatus({ type: "error", message: "Full Name and Email are required." });
      setLoading(false);
      return;
    }

    const payload: any = {
      full_name: formData.full_name.trim(),
      email: formData.email.trim(),
    };

    if (showPasswordFields && password) {
      if (password.length < 8) {
        setStatus({ type: "error", message: "Password must be at least 8 characters long." });
        setLoading(false);
        return;
      }
      if (password !== confirmPassword) {
        setStatus({ type: "error", message: "Passwords do not match." });
        setLoading(false);
        return;
      }
      payload.password = password;
    }

    try {
      await authService.updateMe(payload);
      await checkAuth(); // Refresh local auth user state
      setStatus({ type: "success", message: "Profile settings saved successfully." });
      setPassword("");
      setConfirmPassword("");
      setShowPasswordFields(false);
    } catch (err: any) {
      console.error(err);
      setStatus({
        type: "error",
        message: err?.response?.data?.detail || err?.message || "Failed to update profile settings.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-4 md:p-6 space-y-6 animate-fade-in">
      <div className="border-b border-slate-800/60 pb-4">
        <h1 className="text-xl font-bold tracking-wide text-white uppercase font-mono">Profile & Settings</h1>
        <p className="text-xs text-slate-400 mt-1">Manage user account profile, passwords, and security controls.</p>
      </div>

      {status && (
        <div
          className={`flex items-start gap-2.5 p-4 rounded-xl border text-xs font-sans ${
            status.type === "success"
              ? "bg-emerald-950/20 border-emerald-900/30 text-emerald-400"
              : "bg-rose-955/20 border-rose-900/30 text-rose-400"
          }`}
        >
          {status.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          )}
          <span>{status.message}</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        <Card className="p-6 bg-slate-900/40 border-slate-800/80 rounded-2xl">
          <h2 className="text-xs font-mono font-bold tracking-wider text-slate-300 uppercase mb-4 pb-2 border-b border-slate-900">
            Account Profile Settings
          </h2>
          <div className="space-y-4">
            <Input
              label="Full Name"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              className="bg-slate-950/60 border-slate-800 focus:border-cyan-500/40 text-slate-200"
            />
            <Input
              label="Email Address"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="bg-slate-950/60 border-slate-800 focus:border-cyan-500/40 text-slate-200"
            />
          </div>
        </Card>

        {showPasswordFields && (
          <Card className="p-6 bg-slate-900/40 border-slate-800/80 rounded-2xl animate-slide-in">
            <h2 className="text-xs font-mono font-bold tracking-wider text-slate-300 uppercase mb-4 pb-2 border-b border-slate-900">
              Update Password
            </h2>
            <div className="space-y-4">
              <Input
                label="New Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                className="bg-slate-950/60 border-slate-800 focus:border-cyan-500/40 text-slate-200"
              />
              <Input
                label="Confirm Password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="bg-slate-950/60 border-slate-800 focus:border-cyan-500/40 text-slate-200"
              />
            </div>
          </Card>
        )}

        <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-slate-900/20 border border-slate-850 rounded-2xl">
          <div className="flex gap-2">
            <Button type="submit" loading={loading} className="px-5 bg-gradient-to-r from-cyan-600 to-blue-600 font-semibold text-xs rounded-xl shadow-[0_4px_12px_rgba(6,182,212,0.15)]">
              Save Changes
            </Button>
            {!showPasswordFields && (
              <Button
                type="button"
                variant="secondary"
                onClick={() => setShowPasswordFields(true)}
                className="px-4 border border-slate-800 text-xs font-semibold rounded-xl bg-slate-900/60"
              >
                Change Password
              </Button>
            )}
          </div>

          <div className="relative group">
            <Button
              type="button"
              disabled
              className="px-4 border border-slate-850 text-xs font-semibold rounded-xl bg-slate-900/20 text-slate-500 cursor-not-allowed flex items-center gap-1.5"
            >
              <ShieldAlert size={14} />
              Enable 2FA
            </Button>
            <span className="absolute bottom-full right-0 mb-2 w-48 p-2 bg-slate-950 text-slate-400 text-[10px] font-sans rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 border border-slate-800 shadow-xl pointer-events-none">
              Two-Factor Authentication is managed by organization-level security policy.
            </span>
          </div>
        </div>
      </form>
    </div>
  );
}
