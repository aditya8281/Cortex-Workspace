import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ProfilePage from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
}));

vi.mock("../../src/shared/auth/AuthProvider", () => ({
  useAuth: () => ({
    user: {
      id: 1,
      username: "testuser",
      full_name: "Test User",
      role: "user",
      nickname: "tester",
      bio: "I am a test user",
      description: "A longer test description",
      profile_photo: null,
      handles: null,
      storage_root: "/home/test",
      github_username: "testuser",
      preferences: {},
      created_at: "2024-01-01T00:00:00Z",
      updated_at: null,
      programming_languages: ["Python", "TypeScript"],
      frameworks: ["React", "Next.js"],
      current_projects: [{ name: "Cortex", description: "AI OS" }],
      contribution_style: "Full-stack",
      social_links: { twitter: "@test", linkedin: "linkedin.com/in/test", website: "https://test.com" },
    },
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
    updateUser: vi.fn(),
  }),
}));

vi.mock("../../src/shared/auth/cortexApi", () => ({
  apiGetMe: vi.fn(),
  apiUpdateProfile: vi.fn(),
  apiUploadAvatar: vi.fn(),
  apiRemoveAvatar: vi.fn(),
  apiConnectGitHub: vi.fn(),
  apiDisconnectGitHub: vi.fn(),
  getProfilePhotoUrl: vi.fn(() => "/mock-photo.jpg"),
}));

vi.mock("../../src/shared/layout/DashboardShell", () => ({
  default: ({ children }: any) => <div>{children}</div>,
}));

vi.mock("../../src/shared/ui/Button", () => ({
  default: ({ children, onClick, loading, ...props }: any) => (
    <button onClick={onClick} disabled={loading} {...props}>{children}</button>
  ),
}));

vi.mock("../../src/shared/ui/Input", () => ({
  default: ({ label, value, onChange, ...props }: any) => (
    <div>
      {label && <label>{label}</label>}
      <input value={value || ""} onChange={onChange} {...props} />
    </div>
  ),
}));

vi.mock("../../src/shared/ui/Card", () => ({
  default: ({ children, ...props }: any) => <div {...props}>{children}</div>,
}));

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

const { apiUpdateProfile, apiConnectGitHub, apiDisconnectGitHub, apiGetMe } = await import("../../src/shared/auth/cortexApi");

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(apiUpdateProfile).mockResolvedValue({
    id: 1,
    username: "testuser",
    full_name: "Test User",
    role: "user",
    nickname: "tester",
    bio: "I am a test user",
    description: "A longer test description",
    profile_photo: null,
    handles: null,
    storage_root: null,
    github_username: "testuser",
    preferences: {},
    created_at: "2024-01-01T00:00:00Z",
    updated_at: null,
  });
  vi.mocked(apiConnectGitHub).mockResolvedValue({ connected: true, github_username: "testuser" });
  vi.mocked(apiDisconnectGitHub).mockResolvedValue({ connected: false, github_username: "" });
  vi.mocked(apiGetMe).mockResolvedValue({
    id: 1,
    username: "testuser",
    full_name: "Test User",
    role: "user",
    nickname: "tester",
    bio: "I am a test user",
    description: "A longer test description",
    profile_photo: null,
    handles: null,
    storage_root: null,
    github_username: "testuser",
    preferences: {},
    created_at: "2024-01-01T00:00:00Z",
    updated_at: null,
  });
});

describe("Profile Page", () => {
  it("renders profile info", async () => {
    render(<ProfilePage />);
    await waitFor(() => {
      expect(screen.getByText("Your profile")).toBeInTheDocument();
    });
    expect(screen.getByText("Personal Information")).toBeInTheDocument();
    expect(screen.getByText("Profile Photo")).toBeInTheDocument();
    expect(screen.getByText("@testuser")).toBeInTheDocument();
    expect(screen.getByText("user")).toBeInTheDocument();
  });

  it("updates personal info", async () => {
    render(<ProfilePage />);
    await waitFor(() => {
      expect(screen.getByText("Save changes")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Save changes"));
    await waitFor(() => {
      expect(apiUpdateProfile).toHaveBeenCalled();
    });
  });

  it("shows GitHub connect status when connected", async () => {
    render(<ProfilePage />);
    await waitFor(() => {
      expect(screen.getByText("GitHub")).toBeInTheDocument();
    });
    expect(screen.getByText("Connected")).toBeInTheDocument();
    expect(screen.getByText("Disconnect")).toBeInTheDocument();
  });

  it("shows GitHub connect form when not connected", async () => {
    const authModule = await import("../../src/shared/auth/AuthProvider");
    const originalUseAuth = authModule.useAuth;
    (authModule as any).useAuth = () => ({
      user: {
        id: 2,
        username: "user2",
        full_name: "User Two",
        role: "user",
        nickname: "u2",
        bio: null,
        description: null,
        profile_photo: null,
        handles: null,
        storage_root: null,
        github_username: null,
        preferences: {},
        created_at: "2024-01-01T00:00:00Z",
        updated_at: null,
      },
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      updateUser: vi.fn(),
    });
    render(<ProfilePage />);
    await waitFor(() => {
      expect(screen.getByText("Connect")).toBeInTheDocument();
    });
    (authModule as any).useAuth = originalUseAuth;
  });

  it("shows social links", async () => {
    render(<ProfilePage />);
    await waitFor(() => {
      expect(screen.getByText("Social Links")).toBeInTheDocument();
    });
    expect(screen.getByDisplayValue("@test")).toBeInTheDocument();
    expect(screen.getByDisplayValue("linkedin.com/in/test")).toBeInTheDocument();
    expect(screen.getByDisplayValue("https://test.com")).toBeInTheDocument();
  });
});
