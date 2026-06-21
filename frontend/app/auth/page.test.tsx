import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import AuthPage from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
}));

vi.mock("../../src/shared/auth/AuthProvider", () => ({
  useAuth: () => ({
    user: null,
    loading: false,
    login: vi.fn(),
  }),
}));

vi.mock("../../src/shared/auth/cortexApi", () => ({
  apiLogin: vi.fn(),
  apiRegister: vi.fn(),
  apiCheckUsername: vi.fn().mockResolvedValue({ available: true, message: "Username is available" }),
  apiConnectGitHub: vi.fn(),
}));

vi.mock("../../src/shared/ui/Button", () => ({
  default: ({ children, onClick, loading, type, ...props }: any) => (
    <button type={type} onClick={onClick} disabled={loading} {...props}>{children}</button>
  ),
}));

vi.mock("../../src/shared/ui/Input", () => ({
  default: ({ label, value, onChange, type, placeholder, error, ...props }: any) => (
    <div>
      <label>{label}</label>
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        data-testid={`input-${label}`}
        {...props}
      />
      {error && <span data-testid="field-error">{error}</span>}
    </div>
  ),
}));

vi.mock("../../src/shared/ui/Card", () => ({
  default: ({ children, ...props }: any) => <div {...props}>{children}</div>,
}));

vi.mock("../../src/shared/ui/PasswordStrength", () => ({
  default: ({ password }: any) => (
    <div data-testid="password-strength">{password ? `${password.length} chars` : ""}</div>
  ),
}));

vi.mock("../../src/shared/ui/NeuralNetwork", () => ({
  default: () => <div data-testid="neural-network" />,
}));

vi.mock("../../src/shared/hooks/useFolderPicker", () => ({
  default: () => ({
    isSupported: false,
    result: null,
    pick: vi.fn(),
    clear: vi.fn(),
  }),
}));

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

const { apiLogin, apiRegister } = await import("../../src/shared/auth/cortexApi");

beforeEach(() => {
  vi.clearAllMocks();
});

function getLoginSubmitButton() {
  return screen.getAllByText("Sign in").find(
    (el) => el.tagName === "BUTTON" && el.getAttribute("type") === "submit"
  );
}

function getRegisterToggleButton() {
  return screen.getAllByText("Register").find(
    (el) => el.tagName === "BUTTON" && !el.getAttribute("type")
  );
}

describe("Auth Page", () => {
  it("renders login form by default", () => {
    render(<AuthPage />);
    expect(screen.getByTestId("input-Username")).toBeInTheDocument();
    expect(screen.getByTestId("input-Password")).toBeInTheDocument();
    expect(screen.getAllByText("Sign in").length).toBeGreaterThanOrEqual(1);
  });

  it("switches to register mode", async () => {
    render(<AuthPage />);
    fireEvent.click(getRegisterToggleButton()!);
    await waitFor(() => {
      expect(screen.getByText("Step 1 of 4")).toBeInTheDocument();
    });
  });

  it("validates login fields", async () => {
    render(<AuthPage />);
    const form = screen.getByTestId("input-Username").closest("form")!;
    fireEvent.submit(form);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("submits login form", async () => {
    vi.mocked(apiLogin).mockResolvedValue({
      access_token: "fake-token",
      token_type: "bearer",
      user: {
        id: 1,
        username: "testuser",
        full_name: "Test User",
        role: "user",
        nickname: "tester",
        bio: "",
        description: null,
        profile_photo: null,
        handles: null,
        storage_root: null,
        github_username: null,
        preferences: null,
        created_at: new Date().toISOString(),
      },
    });

    render(<AuthPage />);
    fireEvent.change(screen.getByTestId("input-Username"), { target: { value: "testuser" } });
    fireEvent.change(screen.getByTestId("input-Password"), { target: { value: "securepass123" } });

    const form = screen.getByTestId("input-Username").closest("form")!;
    fireEvent.submit(form);

    await waitFor(() => {
      expect(apiLogin).toHaveBeenCalledWith({
        username: "testuser",
        password: "securepass123",
      });
    });
  });

  it("shows login error", async () => {
    vi.mocked(apiLogin).mockRejectedValue(new Error("Invalid credentials"));

    render(<AuthPage />);
    fireEvent.change(screen.getByTestId("input-Username"), { target: { value: "wronguser" } });
    fireEvent.change(screen.getByTestId("input-Password"), { target: { value: "wrongpass" } });

    const form = screen.getByTestId("input-Username").closest("form")!;
    fireEvent.submit(form);

    await waitFor(() => {
      expect(screen.getByText("Invalid credentials")).toBeInTheDocument();
    });
  });

  it("shows register wizard steps", async () => {
    render(<AuthPage />);
    fireEvent.click(getRegisterToggleButton()!);

    await waitFor(() => {
      expect(screen.getByText("Step 1 of 4")).toBeInTheDocument();
    });

    expect(screen.getByTestId("input-Username")).toBeInTheDocument();
    expect(screen.getByTestId("input-Password")).toBeInTheDocument();
    expect(screen.getByTestId("input-Confirm password")).toBeInTheDocument();
  });

  it("validates register step 0 fields", async () => {
    render(<AuthPage />);
    fireEvent.click(getRegisterToggleButton()!);

    await waitFor(() => {
      expect(screen.getByText("Continue")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Continue"));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("navigates through register wizard steps", async () => {
    render(<AuthPage />);
    fireEvent.click(getRegisterToggleButton()!);

    await waitFor(() => {
      expect(screen.getByText("Step 1 of 4")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("input-Username"), { target: { value: "newuser" } });
    fireEvent.change(screen.getByTestId("input-Password"), { target: { value: "securepass123" } });
    fireEvent.change(screen.getByTestId("input-Confirm password"), { target: { value: "securepass123" } });

    await waitFor(() => {
      expect(screen.getByText("Continue")).toBeInTheDocument();
    });

    await new Promise((r) => setTimeout(r, 500));

    fireEvent.click(screen.getByText("Continue"));

    await waitFor(() => {
      expect(screen.getByText("Step 2 of 4")).toBeInTheDocument();
    });
  });

  it("shows neural network visualization on desktop", () => {
    render(<AuthPage />);
    expect(screen.getByTestId("neural-network")).toBeInTheDocument();
  });

  it("navigates through all 4 wizard steps and submits registration", async () => {
    vi.mocked(apiRegister).mockResolvedValue({
      access_token: "fake-token",
      token_type: "bearer",
      user: {
        id: 2,
        username: "newuser",
        full_name: "New User",
        role: "user",
        nickname: "newnick",
        bio: "test bio",
        description: null,
        profile_photo: null,
        handles: null,
        storage_root: null,
        github_username: null,
        preferences: null,
        created_at: new Date().toISOString(),
      },
    });

    render(<AuthPage />);
    fireEvent.click(getRegisterToggleButton()!);

    await waitFor(() => {
      expect(screen.getByText("Step 1 of 4")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("input-Username"), { target: { value: "newuser" } });
    fireEvent.change(screen.getByTestId("input-Password"), { target: { value: "Securepass1" } });
    fireEvent.change(screen.getByTestId("input-Confirm password"), { target: { value: "Securepass1" } });

    await waitFor(() => {
      expect(screen.getByText("Continue")).toBeInTheDocument();
    });
    await new Promise((r) => setTimeout(r, 500));
    fireEvent.click(screen.getByText("Continue"));

    await waitFor(() => {
      expect(screen.getByText("Step 2 of 4")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("input-Full name"), { target: { value: "New User" } });
    fireEvent.change(screen.getByTestId("input-Nickname"), { target: { value: "newnick" } });
    fireEvent.click(screen.getByText("Continue"));

    await waitFor(() => {
      expect(screen.getByText("Step 3 of 4")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Skip for now"));

    await waitFor(() => {
      expect(screen.getByText("Step 4 of 4")).toBeInTheDocument();
    });

    const vaultPws = screen.getAllByPlaceholderText("••••••••");
    fireEvent.change(vaultPws[0], { target: { value: "VaultPass1" } });
    fireEvent.change(vaultPws[1], { target: { value: "VaultPass1" } });
    fireEvent.click(screen.getByText("Create account"));

    await waitFor(() => {
      expect(apiRegister).toHaveBeenCalledWith({
        username: "newuser",
        password: "Securepass1",
        confirm_password: "Securepass1",
        full_name: "New User",
        nickname: "newnick",
        bio: undefined,
        vault_password: "VaultPass1",
        storage_root: "~/CortexData/newuser",
      });
    });
  });

  it("toggles between login and register resets state", async () => {
    render(<AuthPage />);
    fireEvent.click(getRegisterToggleButton()!);
    await waitFor(() => {
      expect(screen.getByText("Step 1 of 4")).toBeInTheDocument();
    });

    const signInToggle = screen.getAllByText("Sign in").find(
      (el) => el.tagName === "BUTTON" && !el.getAttribute("type")
    );
    fireEvent.click(signInToggle!);
    await waitFor(() => {
      expect(screen.getByTestId("input-Username")).toBeInTheDocument();
    });
  });
});
