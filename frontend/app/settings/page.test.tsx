import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import SettingsPage from "./page";

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
      bio: null,
      description: null,
      profile_photo: null,
      handles: null,
      storage_root: "/home/test",
      github_username: null,
      preferences: { accent_color: "cyan", font_size: "md", sidebar_default: "expanded" },
      created_at: "2024-01-01T00:00:00Z",
      updated_at: null,
    },
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
    updateUser: vi.fn(),
  }),
}));

vi.mock("../../src/shared/auth/cortexApi", () => ({
  apiUpdateProfile: vi.fn(),
  apiDeleteAccount: vi.fn(),
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
      <label>{label}</label>
      <input value={value} onChange={onChange} {...props} />
    </div>
  ),
}));

vi.mock("../../src/shared/ui/Card", () => ({
  default: ({ children, ...props }: any) => <div {...props}>{children}</div>,
}));

vi.mock("./IndexingConfigForm", () => ({
  default: () => <div data-testid="indexing-config" />,
}));

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

const { apiUpdateProfile } = await import("../../src/shared/auth/cortexApi");

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(apiUpdateProfile).mockResolvedValue({
    id: 1,
    username: "testuser",
    full_name: "Test User",
    role: "user",
    nickname: "tester",
    bio: null,
    description: null,
    profile_photo: null,
    handles: null,
    storage_root: null,
    github_username: null,
    preferences: { accent_color: "purple", font_size: "md", sidebar_default: "expanded" },
    created_at: "2024-01-01T00:00:00Z",
    updated_at: null,
  });
});

describe("Settings Page", () => {
  it("renders account info section", async () => {
    render(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText("Settings")).toBeInTheDocument();
      expect(screen.getByText("Account Information")).toBeInTheDocument();
      expect(screen.getByText("@testuser")).toBeInTheDocument();
      expect(screen.getByText("user")).toBeInTheDocument();
    });
  });

  it("updates preferences (accent color, font, sidebar)", async () => {
    render(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText("Preferences")).toBeInTheDocument();
    });
    const purpleButton = screen.getByLabelText("purple accent");
    fireEvent.click(purpleButton);
    const saveButton = screen.getByText("Save preferences");
    fireEvent.click(saveButton);
    await waitFor(() => {
      expect(apiUpdateProfile).toHaveBeenCalled();
    });
  });

  it("shows indexing config", async () => {
    render(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByTestId("indexing-config")).toBeInTheDocument();
    });
  });

  it("handles save action", async () => {
    render(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText("Save preferences")).toBeInTheDocument();
    });
    const saveButton = screen.getByText("Save preferences");
    fireEvent.click(saveButton);
    await waitFor(() => {
      expect(apiUpdateProfile).toHaveBeenCalled();
    });
  });
});
