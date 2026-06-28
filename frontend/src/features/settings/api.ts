import { apiFetch } from "@/shared/api/client";

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface ConsentItem {
  id: string;
  name: string;
  description: string;
  granted: boolean;
}

export const settingsApi = {
  getProfile: () => apiFetch<UserProfile>("/auth/me"),
  updateProfile: (data: Partial<{ username: string; email: string }>) =>
    apiFetch<UserProfile>("/auth/me", {
      method: "PUT",
      body: data,
    }),

  getConsents: () => apiFetch<ConsentItem[]>("/privacy/consent"),
  grantConsent: (consentId: string) =>
    apiFetch<{ status: string }>("/privacy/consent/grant", {
      method: "POST",
      body: { consent_id: consentId },
    }),
  revokeConsent: (consentId: string) =>
    apiFetch<{ status: string }>("/privacy/consent/revoke", {
      method: "POST",
      body: { consent_id: consentId },
    }),

  getVaultStatus: () =>
    apiFetch<{ locked: boolean; file_count: number }>("/privacy/vault/status"),
};
