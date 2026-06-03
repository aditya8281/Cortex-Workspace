import { api } from "./client";

export type UserProfileResponse = {
  display_name: string | null;
  email: string | null;
  job_title: string | null;
  location: string | null;
  bio: string | null;
  interests: string[];
  goals: string[];
  focus_areas: string[];
  primary_languages: string[];
  onboarding_completed: boolean;
  completion_percent: number;
};

export type UserProfileUpdate = Partial<{
  display_name: string;
  job_title: string;
  location: string;
  bio: string;
  interests: string[];
  goals: string[];
  focus_areas: string[];
  primary_languages: string[];
  onboarding_completed: boolean;
}>;

export async function getMyProfile(): Promise<UserProfileResponse> {
  const res = await api.get("/me/profile");
  return res.data;
}

export async function updateMyProfile(payload: UserProfileUpdate): Promise<UserProfileResponse> {
  const res = await api.put("/me/profile", payload);
  return res.data;
}
