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
  getProfile: () => apiFetch<UserProfile>("/me"),
  updateProfile: (data: Partial<{ username: string; email: string }>) =>
    apiFetch<UserProfile>("/me", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  getConsents: () => apiFetch<ConsentItem[]>("/consent"),
  grantConsent: (consentId: string) =>
    apiFetch<{ status: string }>("/consent/grant", {
      method: "POST",
      body: JSON.stringify({ consent_id: consentId }),
    }),
  revokeConsent: (consentId: string) =>
    apiFetch<{ status: string }>("/consent/revoke", {
      method: "POST",
      body: JSON.stringify({ consent_id: consentId }),
    }),

  getVaultStatus: () =>
    apiFetch<{ locked: boolean; file_count: number }>("/vault/status"),
};
