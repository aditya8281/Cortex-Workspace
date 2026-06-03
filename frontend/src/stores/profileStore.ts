import { create } from "zustand";
import { persist } from "zustand/middleware";

export type UserProfile = {
  displayName: string;
  email: string;
  jobTitle: string;
  location: string;
  bio: string;
  interests: string[];
  goals: string[];
  focusAreas: string[];
  primaryLanguages: string[];
  onboardingStep: number;
  onboardingComplete: boolean;
  avatarColor: string;
};

const DEFAULT_PROFILE: UserProfile = {
  displayName: "",
  email: "",
  jobTitle: "",
  location: "",
  bio: "",
  interests: [],
  goals: [],
  focusAreas: [],
  primaryLanguages: [],
  onboardingStep: 0,
  onboardingComplete: false,
  avatarColor: "#5b9dff",
};

type ProfileState = {
  profile: UserProfile;
  setProfile: (patch: Partial<UserProfile>) => void;
  addInterest: (item: string) => void;
  addGoal: (item: string) => void;
  removeInterest: (item: string) => void;
  removeGoal: (item: string) => void;
  resetProfile: () => void;
  completionPercent: () => number;
};

export const useProfileStore = create<ProfileState>()(
  persist(
    (set, get) => ({
      profile: { ...DEFAULT_PROFILE },

      setProfile: (patch) =>
        set((s) => ({ profile: { ...s.profile, ...patch } })),

      addInterest: (item) => {
        const trimmed = item.trim();
        if (!trimmed) return;
        set((s) => ({
          profile: {
            ...s.profile,
            interests: [...new Set([...s.profile.interests, trimmed])],
          },
        }));
      },

      addGoal: (item) => {
        const trimmed = item.trim();
        if (!trimmed) return;
        set((s) => ({
          profile: {
            ...s.profile,
            goals: [...new Set([...s.profile.goals, trimmed])],
          },
        }));
      },

      removeInterest: (item) =>
        set((s) => ({
          profile: { ...s.profile, interests: s.profile.interests.filter((i) => i !== item) },
        })),

      removeGoal: (item) =>
        set((s) => ({
          profile: { ...s.profile, goals: s.profile.goals.filter((g) => g !== item) },
        })),

      resetProfile: () => set({ profile: { ...DEFAULT_PROFILE } }),

      completionPercent: () => {
        const p = get().profile;
        const fields = [
          p.displayName,
          p.bio,
          p.jobTitle,
          p.interests.length > 0,
          p.goals.length > 0,
          p.focusAreas.length > 0,
        ];
        const done = fields.filter(Boolean).length;
        return Math.round((done / fields.length) * 100);
      },
    }),
    { name: "cortex-profile" },
  ),
);
