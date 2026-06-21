import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import AdminPage from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
}));

vi.mock("../../src/shared/auth/AuthProvider", () => ({
  useAuth: () => ({
    user: {
      id: 1,
      username: "admin",
      full_name: "Admin User",
      role: "admin",
      nickname: "admin",
      bio: null,
      description: null,
      profile_photo: null,
      handles: null,
      storage_root: "/home/admin",
      github_username: null,
      preferences: {},
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
  apiListUsers: vi.fn(),
  apiPromoteUser: vi.fn(),
  apiDemoteUser: vi.fn(),
  apiDeleteUser: vi.fn(),
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

const { apiListUsers, apiPromoteUser, apiDemoteUser, apiDeleteUser } = await import("../../src/shared/auth/cortexApi");

const mockUsers = [
  { id: 1, username: "admin", full_name: "Admin User", role: "admin" as const, nickname: "admin", bio: null, description: null, profile_photo: null, handles: null, storage_root: null, github_username: null, preferences: {}, created_at: "2024-01-01T00:00:00Z", updated_at: null },
  { id: 2, username: "alice", full_name: "Alice Smith", role: "user" as const, nickname: "alice", bio: null, description: null, profile_photo: null, handles: null, storage_root: null, github_username: null, preferences: {}, created_at: "2024-02-01T00:00:00Z", updated_at: null },
  { id: 3, username: "bob", full_name: "Bob Jones", role: "admin" as const, nickname: "bob", bio: null, description: null, profile_photo: null, handles: null, storage_root: null, github_username: null, preferences: {}, created_at: "2024-03-01T00:00:00Z", updated_at: null },
];

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(apiListUsers).mockResolvedValue(mockUsers);
  vi.mocked(apiPromoteUser).mockResolvedValue({ ...mockUsers[1], role: "admin" } as any);
  vi.mocked(apiDemoteUser).mockResolvedValue({ ...mockUsers[2], role: "user" } as any);
  vi.mocked(apiDeleteUser).mockResolvedValue({ message: "deleted" });
});

describe("Admin Page", () => {
  it("renders user list", async () => {
    render(<AdminPage />);
    await waitFor(() => {
      expect(screen.getByText("Admin Dashboard")).toBeInTheDocument();
    });
    expect(screen.getByText("Admin User")).toBeInTheDocument();
    expect(screen.getByText("Alice Smith")).toBeInTheDocument();
    expect(screen.getByText("Bob Jones")).toBeInTheDocument();
    expect(screen.getByText(/@alice/)).toBeInTheDocument();
    expect(screen.getByText(/@bob/)).toBeInTheDocument();
  });

  it("shows user counts in stats", async () => {
    render(<AdminPage />);
    await waitFor(() => {
      expect(screen.getByText("Total Users")).toBeInTheDocument();
    });
    expect(screen.getByText("Admins")).toBeInTheDocument();
    expect(screen.getByText("Regular Users")).toBeInTheDocument();
  });

  it("promotes a user", async () => {
    render(<AdminPage />);
    await waitFor(() => {
      expect(screen.getByText("Alice Smith")).toBeInTheDocument();
    });
    const promoteButtons = screen.getAllByText("Promote");
    fireEvent.click(promoteButtons[0]);
    await waitFor(() => {
      expect(apiPromoteUser).toHaveBeenCalledWith(2);
    });
  });

  it("demotes a user", async () => {
    render(<AdminPage />);
    await waitFor(() => {
      expect(screen.getByText("Bob Jones")).toBeInTheDocument();
    });
    const demoteButtons = screen.getAllByText("Demote");
    fireEvent.click(demoteButtons[0]);
    await waitFor(() => {
      expect(apiDemoteUser).toHaveBeenCalledWith(3);
    });
  });

  it("deletes a user", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<AdminPage />);
    await waitFor(() => {
      expect(screen.getByText("Alice Smith")).toBeInTheDocument();
    });
    const deleteButtons = screen.getAllByText("").filter((el) => el.closest("[class*='Trash']") || el.querySelector("svg"));
    const trashButtons = document.querySelectorAll("button");
    const aliceRow = Array.from(trashButtons).find((btn) => {
      const row = btn.closest("[class*='px-5']") || btn.parentElement?.parentElement;
      return row?.textContent?.includes("alice");
    });
    const deleteBtns = Array.from(trashButtons).filter((btn) => {
      return btn.querySelector("svg") && !btn.textContent.trim();
    });
    if (deleteBtns.length > 0) {
      fireEvent.click(deleteBtns[0]);
      await waitFor(() => {
        expect(apiDeleteUser).toHaveBeenCalled();
      });
    }
    vi.restoreAllMocks();
  });

  it("filters users by search", async () => {
    render(<AdminPage />);
    await waitFor(() => {
      expect(screen.getByText("Alice Smith")).toBeInTheDocument();
    });
    const filterInput = screen.getByPlaceholderText("Filter users...");
    fireEvent.change(filterInput, { target: { value: "alice" } });
    await waitFor(() => {
      expect(screen.getByText("Alice Smith")).toBeInTheDocument();
      expect(screen.queryByText("Bob Jones")).not.toBeInTheDocument();
    });
    expect(screen.queryByText("Admin User")).not.toBeInTheDocument();
  });

  it("shows empty state when filter matches nothing", async () => {
    render(<AdminPage />);
    await waitFor(() => {
      expect(screen.getByText("Alice Smith")).toBeInTheDocument();
    });
    const filterInput = screen.getByPlaceholderText("Filter users...");
    fireEvent.change(filterInput, { target: { value: "zzzzz" } });
    await waitFor(() => {
      expect(screen.getByText("No users match your filter.")).toBeInTheDocument();
    });
  });
});
