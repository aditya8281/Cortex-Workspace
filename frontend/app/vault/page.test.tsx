import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import VaultPage from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
}));

vi.mock("@/shared/auth/AuthProvider", () => ({
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
      storage_root: null,
      github_username: null,
      preferences: null,
      created_at: null,
      updated_at: null,
    },
    loading: false,
    login: vi.fn(),
  }),
}));

const mockApiVaultUnlock = vi.fn().mockResolvedValue({ unlocked: true, message: "ok" });

vi.mock("../../../src/shared/auth/cortexApi", () => ({
  apiVaultStatus: vi.fn().mockResolvedValue({ locked: true, has_vault_password: true }),
  apiVaultUnlock: (...args: any[]) => mockApiVaultUnlock(...args),
  apiVaultLock: vi.fn().mockResolvedValue({ locked: true, message: "locked" }),
  apiVaultListFiles: vi.fn().mockResolvedValue([]),
}));

vi.mock("@/shared/layout/DashboardShell", () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("./VaultLockScreen", () => ({
  default: ({ vault }: any) => (
    <div data-testid="vault-lock-screen">
      <input
        data-testid="vault-password-input"
        value={vault.vaultPassword}
        onChange={(e: any) => vault.setVaultPassword(e.target.value)}
      />
      <button data-testid="unlock-btn" onClick={vault.handleUnlock}>Unlock</button>
      {vault.error && <span data-testid="vault-error">{vault.error}</span>}
    </div>
  ),
}));

vi.mock("./VaultLayout", () => ({
  default: ({ vault }: any) => (
    <div data-testid="vault-layout">
      <button data-testid="upload-btn" onClick={() => vault.fileInputRef?.current?.click()}>Upload</button>
    </div>
  ),
}));

vi.mock("./VaultModals", () => ({
  default: () => <div data-testid="vault-modals" />,
}));

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <div>{children}</div>,
}));

const useVaultStateMock = vi.fn();

vi.mock("./useVaultState", () => ({
  default: () => useVaultStateMock(),
}));

describe("Vault Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows lock screen when vault is locked", async () => {
    useVaultStateMock.mockReturnValue({
      user: { id: 1, username: "testuser" },
      authLoading: false,
      status: { locked: true, has_vault_password: true },
      vaultPassword: "",
      setVaultPassword: vi.fn(),
      handleUnlock: vi.fn(),
      error: "",
      loading: false,
      successMsg: "",
    });

    render(<VaultPage />);
    expect(screen.getByTestId("vault-lock-screen")).toBeInTheDocument();
    expect(screen.getByTestId("vault-password-input")).toBeInTheDocument();
  });

  it("calls unlock API when user enters password and clicks unlock", async () => {
    const handleUnlock = vi.fn();
    useVaultStateMock.mockReturnValue({
      user: { id: 1, username: "testuser" },
      authLoading: false,
      status: { locked: true, has_vault_password: true },
      vaultPassword: "VaultPass1",
      setVaultPassword: vi.fn(),
      handleUnlock,
      error: "",
      loading: false,
      successMsg: "",
    });

    render(<VaultPage />);
    fireEvent.click(screen.getByTestId("unlock-btn"));
    expect(handleUnlock).toHaveBeenCalledTimes(1);
  });

  it("shows file browser when vault is unlocked", async () => {
    useVaultStateMock.mockReturnValue({
      user: { id: 1, username: "testuser" },
      authLoading: false,
      status: { locked: false, has_vault_password: true },
      files: [],
      currentFolder: "/",
      handlePanelClick: vi.fn(),
      fileInputRef: { current: null },
    });

    render(<VaultPage />);
    expect(screen.getByTestId("vault-layout")).toBeInTheDocument();
  });

  it("handles file upload trigger", async () => {
    const clickFn = vi.fn();
    useVaultStateMock.mockReturnValue({
      user: { id: 1, username: "testuser" },
      authLoading: false,
      status: { locked: false, has_vault_password: true },
      files: [],
      currentFolder: "/",
      handlePanelClick: vi.fn(),
      fileInputRef: { current: { click: clickFn } },
    });

    render(<VaultPage />);
    fireEvent.click(screen.getByTestId("upload-btn"));
    expect(clickFn).toHaveBeenCalled();
  });

  it("shows vault status indicator (locked badge on lock screen)", async () => {
    useVaultStateMock.mockReturnValue({
      user: { id: 1, username: "testuser" },
      authLoading: false,
      status: { locked: true, has_vault_password: true },
      vaultPassword: "",
      setVaultPassword: vi.fn(),
      handleUnlock: vi.fn(),
      error: "",
      loading: false,
      successMsg: "",
    });

    render(<VaultPage />);
    expect(screen.getByTestId("vault-lock-screen")).toBeInTheDocument();
  });

  it("shows error message when unlock fails", async () => {
    useVaultStateMock.mockReturnValue({
      user: { id: 1, username: "testuser" },
      authLoading: false,
      status: { locked: true, has_vault_password: true },
      vaultPassword: "wrongpass",
      setVaultPassword: vi.fn(),
      handleUnlock: vi.fn(),
      error: "Invalid vault password",
      loading: false,
      successMsg: "",
    });

    render(<VaultPage />);
    expect(screen.getByTestId("vault-error")).toHaveTextContent("Invalid vault password");
  });

  it("transitions from lock screen to workspace on successful unlock", async () => {
    const { rerender } = render(<VaultPage />);

    useVaultStateMock.mockReturnValue({
      user: { id: 1, username: "testuser" },
      authLoading: false,
      status: { locked: true, has_vault_password: true },
      vaultPassword: "",
      setVaultPassword: vi.fn(),
      handleUnlock: vi.fn(),
      error: "",
      loading: false,
      successMsg: "",
    });
    rerender(<VaultPage />);
    expect(screen.getByTestId("vault-lock-screen")).toBeInTheDocument();

    useVaultStateMock.mockReturnValue({
      user: { id: 1, username: "testuser" },
      authLoading: false,
      status: { locked: false, has_vault_password: true },
      files: [],
      currentFolder: "/",
      handlePanelClick: vi.fn(),
      fileInputRef: { current: null },
    });
    rerender(<VaultPage />);
    expect(screen.getByTestId("vault-layout")).toBeInTheDocument();
  });
});
