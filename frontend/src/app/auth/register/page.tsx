"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { apiFetch } from "@/shared/api/client";

// ── Validation helpers ─────────────────────────────────────────────────────

const COMMON_PASSWORDS = new Set([
  "password", "123456", "12345678", "qwerty", "abc123", "monkey", "1234567",
  "letmein", "trustno1", "dragon", "baseball", "iloveyou", "master", "sunshine",
  "ashley", "bailey", "passw0rd", "shadow", "123123", "654321", "superman",
  "qazwsx", "michael", "football", "password1", "password123", "admin",
]);

function validatePassword(pw: string): { ok: boolean; errors: string[] } {
  const errors: string[] = [];
  if (pw.length < 8) errors.push("At least 8 characters");
  if (!/[A-Z]/.test(pw)) errors.push("One uppercase letter");
  if (!/[a-z]/.test(pw)) errors.push("One lowercase letter");
  if (!/[0-9]/.test(pw)) errors.push("One digit");
  if (!/[^A-Za-z0-9]/.test(pw)) errors.push("One special character");
  if (COMMON_PASSWORDS.has(pw.toLowerCase())) errors.push("Not a common password");
  return { ok: errors.length === 0, errors };
}

function passwordStrength(pw: string): 0 | 1 | 2 | 3 | 4 {
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  return Math.min(4, score) as 0 | 1 | 2 | 3 | 4;
}

const STRENGTH_LABELS = ["", "Weak", "Fair", "Strong", "Very strong"];
const STRENGTH_COLORS = ["", "text-danger", "text-warning", "text-success", "text-success"];

// ── Debounced username check ───────────────────────────────────────────────

type UsernameStatus = "idle" | "checking" | "available" | "taken" | "invalid";

function useUsernameCheck() {
  const [status, setStatus] = useState<UsernameStatus>("idle");
  const [message, setMessage] = useState("");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const check = useCallback((username: string) => {
    if (timerRef.current) clearTimeout(timerRef.current);

    const trimmed = username.trim();
    if (trimmed.length < 3) {
      setStatus(trimmed.length === 0 ? "idle" : "invalid");
      setMessage(trimmed.length === 0 ? "" : "At least 3 characters");
      return;
    }
    if (!/^[a-zA-Z0-9_-]+$/.test(trimmed)) {
      setStatus("invalid");
      setMessage("Letters, numbers, hyphens, underscores only");
      return;
    }

    setStatus("checking");
    setMessage("");

    timerRef.current = setTimeout(async () => {
      try {
        const res = await apiFetch<{ available: boolean; message: string }>("/auth/check-username", {
          method: "POST",
          body: { username: trimmed },
        });
        setStatus(res.available ? "available" : "taken");
        setMessage(res.message);
      } catch {
        setStatus("idle");
        setMessage("");
      }
    }, 500);
  }, []);

  return { status, message, check };
}

// ── Password strength bar ──────────────────────────────────────────────────

function StrengthBar({ score }: { score: 0 | 1 | 2 | 3 | 4 }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex gap-1 flex-1">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded-full transition-colors duration-200 ${
              i <= score
                ? score <= 1
                  ? "bg-danger"
                  : score <= 2
                    ? "bg-warning"
                    : "bg-success"
                : "bg-border-subtle"
            }`}
          />
        ))}
      </div>
      {score > 0 && (
        <span className={`text-xs font-medium ${STRENGTH_COLORS[score]}`}>
          {STRENGTH_LABELS[score]}
        </span>
      )}
    </div>
  );
}

// ── Step indicator ─────────────────────────────────────────────────────────

function StepIndicator({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center gap-1.5">
      {Array.from({ length: total }, (_, i) => (
        <div
          key={i}
          className={`h-1 flex-1 rounded-full transition-colors duration-200 ${
            i < current ? "bg-accent" : i === current ? "bg-accent/60" : "bg-border-subtle"
          }`}
        />
      ))}
    </div>
  );
}

// ── Main registration page ─────────────────────────────────────────────────

export default function RegisterPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);

  // Step 1: Account
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // Step 2: Identity
  const [fullName, setFullName] = useState("");
  const [nickname, setNickname] = useState("");
  const [bio, setBio] = useState("");

  // Step 3: Vault & Storage
  const [vaultPassword, setVaultPassword] = useState("");
  const [storageRoot, setStorageRoot] = useState("");

  // Step 4: Optional
  const [github, setGithub] = useState("");
  const [description, setDescription] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const usernameCheck = useUsernameCheck();
  const pwValidation = validatePassword(password);
  const vpValidation = validatePassword(vaultPassword);

  // Live username check on change
  useEffect(() => {
    if (username.length >= 3) {
      usernameCheck.check(username);
    }
  }, [username]);

  // Default storage path
  useEffect(() => {
    if (username && !storageRoot) {
      setStorageRoot(`~/CortexStorage/${username.toLowerCase().replace(/[^a-z0-9_-]/g, "_")}`);
    }
  }, [username]);

  const passwordsMatch = password === confirmPassword && confirmPassword.length > 0;
  const passwordsMismatch = confirmPassword.length > 0 && password !== confirmPassword;

  // Step validation
  const canProceed = [
    // Step 0: Account
    username.length >= 3 &&
      /^[a-zA-Z0-9_-]+$/.test(username) &&
      usernameCheck.status === "available" &&
      pwValidation.ok &&
      passwordsMatch,

    // Step 1: Identity
    fullName.length >= 1 && nickname.length >= 1,

    // Step 2: Vault & Storage
    vpValidation.ok,

    // Step 3: Optional — always valid
    true,
  ];

  const handleSubmit = async () => {
    setError("");
    setLoading(true);
    try {
      await apiFetch("/auth/register", {
        method: "POST",
        body: {
          username: username.trim(),
          password,
          confirm_password: confirmPassword,
          full_name: fullName.trim(),
          nickname: nickname.trim(),
          vault_password: vaultPassword,
          bio: bio.trim() || null,
          description: description.trim() || null,
          storage_root: storageRoot.trim() || null,
          handles: github.trim() ? { github: github.trim() } : null,
        },
      });
      window.location.href = "/";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  const STEP_LABELS = ["Account", "Identity", "Vault", "Optional"];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="mb-3 flex justify-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/12 text-accent">
            <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 0L16 8L8 16L0 8L8 0Z" />
            </svg>
          </div>
        </div>
        <h1 className="text-title font-semibold text-text-primary">Create account</h1>
        <p className="mt-1 text-sm text-text-secondary">Set up your CORTEX brain</p>
      </div>

      {/* Step indicator */}
      <div>
        <StepIndicator current={step} total={4} />
        <div className="flex justify-between mt-2">
          {STEP_LABELS.map((label, i) => (
            <span
              key={label}
              className={`text-[0.625rem] font-medium transition-colors duration-150 ${
                i === step ? "text-accent" : i < step ? "text-text-muted" : "text-text-muted/50"
              }`}
            >
              {label}
            </span>
          ))}
        </div>
      </div>

      {/* Steps */}
      <Card className="p-5 min-h-[280px]">
        {/* Step 0: Account */}
        {step === 0 && (
          <div className="space-y-4">
            <div>
              <Input
                label="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                placeholder="your-name"
                error={
                  usernameCheck.status === "taken"
                    ? usernameCheck.message
                    : usernameCheck.status === "invalid"
                      ? usernameCheck.message
                      : undefined
                }
              />
              {usernameCheck.status === "available" && (
                <p className="text-xs text-success mt-1">{usernameCheck.message}</p>
              )}
              {usernameCheck.status === "checking" && (
                <p className="text-xs text-text-muted mt-1">Checking availability…</p>
              )}
            </div>

            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              placeholder="At least 8 characters"
            />
            {password.length > 0 && (
              <div className="space-y-1.5">
                <StrengthBar score={passwordStrength(password)} />
                {!pwValidation.ok && (
                  <div className="flex flex-wrap gap-1">
                    {pwValidation.errors.map((e) => (
                      <Badge key={e} variant={pwValidation.ok ? "success" : "default"}>
                        {e}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            )}

            <Input
              label="Confirm password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              autoComplete="new-password"
              placeholder="Re-enter password"
              error={passwordsMismatch ? "Passwords do not match" : undefined}
            />
            {passwordsMatch && (
              <p className="text-xs text-success">Passwords match</p>
            )}
          </div>
        )}

        {/* Step 1: Identity */}
        {step === 1 && (
          <div className="space-y-4">
            <Input
              label="Full name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Jane Smith"
              autoComplete="name"
            />
            <Input
              label="Nickname"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              placeholder="What should we call you?"
              autoComplete="nickname"
            />
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">
                Bio
              </label>
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                rows={3}
                placeholder="Tell us about yourself (optional)"
                className="w-full rounded-lg border border-border-default bg-bg-surface px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent/50 focus:outline-none focus:ring-1 focus:ring-accent/25 transition-colors duration-150"
              />
            </div>
          </div>
        )}

        {/* Step 2: Vault & Storage */}
        {step === 2 && (
          <div className="space-y-4">
            <div>
              <p className="text-xs text-text-secondary mb-3">
                Your vault password encrypts personal data locally. It cannot be recovered if lost.
              </p>
              <Input
                label="Vault password"
                type="password"
                value={vaultPassword}
                onChange={(e) => setVaultPassword(e.target.value)}
                autoComplete="new-password"
                placeholder="At least 8 characters"
              />
              {vaultPassword.length > 0 && (
                <div className="space-y-1.5 mt-1.5">
                  <StrengthBar score={passwordStrength(vaultPassword)} />
                  {!vpValidation.ok && (
                    <div className="flex flex-wrap gap-1">
                      {vpValidation.errors.map((e) => (
                        <Badge key={e} variant="default">{e}</Badge>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            <Input
              label="Storage path"
              value={storageRoot}
              onChange={(e) => setStorageRoot(e.target.value)}
              placeholder="~/CortexStorage/username"
              className="font-mono text-xs"
            />
            <p className="text-xs text-text-muted">
              Local directory for your files, notes, and knowledge. Default is fine for most users.
            </p>
          </div>
        )}

        {/* Step 3: Optional */}
        {step === 3 && (
          <div className="space-y-4">
            <Input
              label="GitHub username"
              value={github}
              onChange={(e) => setGithub(e.target.value)}
              placeholder="optional"
              autoComplete="off"
            />
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                placeholder="What are you building? (optional)"
                className="w-full rounded-lg border border-border-default bg-bg-surface px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent/50 focus:outline-none focus:ring-1 focus:ring-accent/25 transition-colors duration-150"
              />
            </div>
            <p className="text-xs text-text-muted">
              All optional fields. You can fill these later in Settings.
            </p>
          </div>
        )}
      </Card>

      {/* Error */}
      {error && (
        <p className="text-sm text-danger text-center">{error}</p>
      )}

      {/* Navigation */}
      <div className="flex gap-3">
        {step > 0 && (
          <Button
            variant="ghost"
            onClick={() => { setStep(step - 1); setError(""); }}
            className="flex-1"
          >
            Back
          </Button>
        )}
        {step < 3 ? (
          <Button
            variant="primary"
            onClick={() => { setStep(step + 1); setError(""); }}
            disabled={!canProceed[step]}
            className="flex-1"
          >
            Continue
          </Button>
        ) : (
          <Button
            variant="primary"
            onClick={handleSubmit}
            disabled={!canProceed[step]}
            loading={loading}
            className="flex-1"
          >
            Create account
          </Button>
        )}
      </div>

      <p className="text-center text-sm text-text-muted">
        Already have an account?{" "}
        <Link href="/auth" className="text-accent hover:text-accent/80 transition-colors duration-150">
          Sign in
        </Link>
      </p>
    </div>
  );
}
