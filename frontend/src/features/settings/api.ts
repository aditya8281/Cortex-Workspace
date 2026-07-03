/**
 * Settings API — profile, consent, vault status
 */
import { apiFetch } from "@/shared/api/client";

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  nickname: string | null;
  bio: string | null;
  is_active: boolean;
  created_at: string;
}

export interface ConsentItem {
  id: number;
  user_id: number;
  consent_type: string;
  scope: string | null;
  granted: boolean;
  context: Record<string, any> | null;
  created_at: string;
}

export const settingsApi = {
  getProfile: () => apiFetch<UserProfile>("/auth/me"),
  updateProfile: (data: Partial<{ nickname: string; bio: string; full_name: string }>) =>
    apiFetch<UserProfile>("/me/profile", {
      method: "PUT",
      body: data,
    }),

  getConsents: () => apiFetch<ConsentItem[]>("/privacy/consent"),
  grantConsent: (consentType: string, scope?: string) =>
    apiFetch<ConsentItem>("/privacy/consent/grant", {
      method: "POST",
      body: { consent_type: consentType, scope },
    }),
  revokeConsent: (consentType: string, reason?: string) => {
    const qs = new URLSearchParams({ consent_type: consentType });
    if (reason) qs.set("reason", reason);
    return apiFetch<{ consent_type: string; success: boolean }>(
      `/privacy/consent/revoke?${qs}`,
    );
  },

  getVaultStatus: () =>
    apiFetch<{ locked: boolean; has_vault_password: boolean }>("/privacy/vault/status"),
};
