"use client";

/**
 * PasswordStrength — Visual password strength indicator.
 * Shows a segmented bar with strength label.
 */

export default function PasswordStrength({ password }) {
  const score = getPasswordScore(password);
  const labels = ["", "Weak", "Fair", "Good", "Strong"];
  const colors = ["", "bg-error", "bg-amber-500", "bg-yellow-400", "bg-success"];

  if (!password) return null;

  return (
    <div className="grid gap-1">
      <div className="flex gap-1">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className={[
              "h-1 flex-1 rounded-full transition-all duration-300",
              i <= score ? colors[score] : "bg-bg-surface",
            ].join(" ")}
          />
        ))}
      </div>
      {score > 0 && (
        <p
          className={[
            "text-[11px] font-medium",
            score <= 1 ? "text-error" : score <= 2 ? "text-amber-500" : score <= 3 ? "text-yellow-400" : "text-success",
          ].join(" ")}
        >
          {labels[score]}
        </p>
      )}
    </div>
  );
}

function getPasswordScore(pw) {
  if (!pw) return 0;
  let score = 0;
  // Must match backend: length >= 8, has letter, has digit
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  return Math.min(4, score);
}

/** Check if password meets backend requirements (length >= 8, has letter, has digit). */
export function meetsBackendRequirements(pw) {
  if (!pw || pw.length < 8) return false;
  return /[a-zA-Z]/.test(pw) && /[0-9]/.test(pw);
}
