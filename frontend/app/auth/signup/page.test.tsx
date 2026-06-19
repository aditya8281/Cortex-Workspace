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
  apiCheckUsername: vi.fn().mockResolvedValue({
    available: true,
    message: "Available",
  }),
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

describe("Signup", () => {
  it("renders register toggle", () => {
    render(<AuthPage />);
    expect(screen.getByText("Register")).toBeInTheDocument();
  });

  it("switches to register mode and shows step 0 fields", () => {
    render(<AuthPage />);
    fireEvent.click(screen.getByText("Register"));
    expect(screen.getByText("Step 1 of 4 — Account")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("operator-01")).toBeInTheDocument();
    expect(screen.getAllByPlaceholderText("••••••••")).toHaveLength(2);
    expect(screen.getByText("Continue")).toBeInTheDocument();
  });

  it("calls apiRegister through the wizard flow", async () => {
    const { apiRegister } = await import("@/shared/auth/cortexApi");
    vi.mocked(apiRegister).mockResolvedValueOnce({
      access_token: "test-token", token_type: "bearer", user: mockUser,
    });

    render(<AuthPage />);
    fireEvent.click(screen.getByText("Register"));

    // Step 0 — Account
    fireEvent.change(screen.getByPlaceholderText("operator-01"), {
      target: { value: "testuser" },
    });
    const [pwInput, confirmPwInput] =
      screen.getAllByPlaceholderText("••••••••");
    fireEvent.change(pwInput, { target: { value: "Password1" } });
    fireEvent.change(confirmPwInput, { target: { value: "Password1" } });
    fireEvent.click(screen.getByText("Continue"));

    // Step 1 — Profile
    await waitFor(() => {
      expect(
        screen.getByText("Step 2 of 4 — Profile")
      ).toBeInTheDocument();
    });
    fireEvent.change(screen.getByPlaceholderText("Ada Lovelace"), {
      target: { value: "Test User" },
    });
    fireEvent.change(screen.getByPlaceholderText("ada"), {
      target: { value: "tester" },
    });
    fireEvent.click(screen.getByText("Continue"));

    // Step 2 — GitHub
    await waitFor(() => {
      expect(
        screen.getByText("Step 3 of 4 — GitHub")
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Skip for now"));

    // Step 3 — Vault
    await waitFor(() => {
      expect(
        screen.getByText("Step 4 of 4 — Vault")
      ).toBeInTheDocument();
    });
    const [vaultPw, vaultConfirm] =
      screen.getAllByPlaceholderText("••••••••");
    fireEvent.change(vaultPw, { target: { value: "VaultPass1" } });
    fireEvent.change(vaultConfirm, { target: { value: "VaultPass1" } });
    fireEvent.click(screen.getByText("Create account"));

    await waitFor(() => {
      expect(apiRegister).toHaveBeenCalledWith({
        username: "testuser",
        password: "Password1",
        confirm_password: "Password1",
        full_name: "Test User",
        nickname: "tester",
        bio: undefined,
        vault_password: "VaultPass1",
        storage_root: "~/CortexData/testuser",
      });
    });
  });
});
