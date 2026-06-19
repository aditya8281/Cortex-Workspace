import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import AuthPage from "../page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
}));

vi.mock("@/shared/auth/cortexApi", () => ({
  apiLogin: vi.fn(),
  apiRegister: vi.fn(),
  apiCheckUsername: vi.fn(),
  apiConnectGitHub: vi.fn(),
}));

import type { User } from "@/shared/types";

const mockUser: User = {
  id: 1, username: "testuser", full_name: "Test", role: "user",
  nickname: "tester", bio: null, description: null, profile_photo: null,
  handles: null, storage_root: null, github_username: null,
  preferences: null, created_at: null, updated_at: null,
};

vi.mock("@/shared/auth/AuthProvider", () => ({
  useAuth: () => ({ user: null, loading: false, login: vi.fn() }),
}));

describe("Login", () => {
  it("renders heading and tagline", () => {
    render(<AuthPage />);
    expect(screen.getAllByText("Cortex").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Local-first/).length).toBeGreaterThanOrEqual(1);
  });

  it("renders username and password fields", () => {
    render(<AuthPage />);
    expect(screen.getByPlaceholderText("operator-01")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("••••••••")).toBeInTheDocument();
  });

  it("renders mode toggle and submit button", () => {
    render(<AuthPage />);
    const buttons = screen.getAllByText("Sign in");
    expect(buttons).toHaveLength(2);
  });

  it("calls apiLogin on form submission", async () => {
    const { apiLogin } = await import("@/shared/auth/cortexApi");
    vi.mocked(apiLogin).mockResolvedValueOnce({
      access_token: "test-token", token_type: "bearer", user: mockUser,
    });

    render(<AuthPage />);

    fireEvent.change(screen.getByPlaceholderText("operator-01"), {
      target: { value: "testuser" },
    });
    fireEvent.change(screen.getByPlaceholderText("••••••••"), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getAllByText("Sign in")[1]);

    await waitFor(() => {
      expect(apiLogin).toHaveBeenCalledWith({
        username: "testuser",
        password: "password123",
      });
    });
  });
});
