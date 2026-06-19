"use client";

/**
 * AuthRedirect — Redirects authenticated users to /app.
 * Used inside server component pages to preserve redirect behavior.
 * With httpOnly cookies, we can't check auth from JS, so this is a no-op.
 * The auth page handles redirect via its own bootstrap effect.
 */

export default function AuthRedirect() {
  return null;
}
