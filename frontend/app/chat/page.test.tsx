import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ChatPage from "./page";

const mockReplace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace }),
}));

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
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

const mockGet = vi.fn();
const mockPost = vi.fn();
const mockDelete = vi.fn();

vi.mock("@/shared/api/client", () => ({
  api: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
    delete: (...args: any[]) => mockDelete(...args),
  },
  getCsrfToken: vi.fn(() => "test-csrf-token"),
}));

vi.mock("@/shared/ui/Dropdown", () => ({
  default: ({ trigger, children }: any) => (
    <div data-testid="dropdown">
      {trigger}
      <div data-testid="dropdown-items">{children}</div>
    </div>
  ),
  DropdownItem: ({ children, onClick, ...props }: any) => (
    <button onClick={onClick} {...props}>{children}</button>
  ),
}));

vi.mock("@/shared/ui/Card", () => ({
  default: ({ children, ...props }: any) => <div data-testid="card">{children}</div>,
}));

vi.mock("@/shared/layout/DashboardShell", () => ({
  default: ({ children }: { children: React.ReactNode }) => <div data-testid="dashboard-shell">{children}</div>,
}));

vi.mock("@/shared/components/MarkdownRenderer", () => ({
  MarkdownRenderer: ({ content }: { content: string }) => <div data-testid="markdown">{content}</div>,
}));

vi.mock("@/shared/ui/NeuralNetwork", () => ({
  default: () => <div data-testid="neural-network" />,
}));

vi.mock("@/shared/ui/CommandPalette", () => ({
  default: () => null,
}));

vi.mock("@/shared/auth/cortexApi", () => ({
  getProfilePhotoUrl: vi.fn(),
  apiListNotifications: vi.fn().mockResolvedValue({ notifications: [], total: 0, unread_count: 0 }),
  apiVaultStatus: vi.fn().mockResolvedValue({ locked: true, has_vault_password: true }),
  apiListMemory: vi.fn().mockResolvedValue({ total: 0, entries: [], categories: {} }),
}));

const mockFetch = vi.fn();
global.fetch = mockFetch;

beforeEach(() => {
  vi.clearAllMocks();
  mockGet.mockImplementation((path: string) => {
    if (path === "/api/v1/conversations") {
      return Promise.resolve({ conversations: [] });
    }
    if (path === "/api/v1/models") {
      return Promise.resolve({ models: [] });
    }
    if (path.startsWith("/api/v1/conversations/")) {
      return Promise.resolve({ messages: [] });
    }
    return Promise.resolve({});
  });
  mockFetch.mockResolvedValue({
    ok: true,
    body: {
      getReader: () => ({
        read: async () => ({ done: true, value: undefined }),
      }),
    },
  });
});

describe("Chat Page", () => {
  it("renders chat interface with message input", async () => {
    render(<ChatPage />);
    await waitFor(() => {
      expect(screen.getByPlaceholderText("Ask Cortex anything...")).toBeInTheDocument();
    });
  });

  it("shows conversation list in sidebar", async () => {
    mockGet.mockImplementation((path: string) => {
      if (path === "/api/v1/conversations") {
        return Promise.resolve({
          conversations: [
            { id: 1, title: "Test Chat", repo_id: null, model_used: null, message_count: 0, total_tokens: 0, created_at: null, updated_at: null },
          ],
        });
      }
      if (path === "/api/v1/models") {
        return Promise.resolve({ models: [] });
      }
      if (path.startsWith("/api/v1/conversations/")) {
        return Promise.resolve({ messages: [] });
      }
      return Promise.resolve({});
    });
    render(<ChatPage />);
    await waitFor(() => {
      expect(screen.getByText("Test Chat")).toBeInTheDocument();
    });
  });

  it("creates new conversation when clicking New Chat", async () => {
    mockPost.mockResolvedValue({ id: 99 });
    render(<ChatPage />);
    await waitFor(() => {
      expect(screen.getByText("New Chat")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("New Chat"));
    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith("/api/v1/conversations", { title: "New Conversation" });
    });
  });

  it("shows model selector dropdown when models available", async () => {
    mockGet.mockImplementation((path: string) => {
      if (path === "/api/v1/conversations") {
        return Promise.resolve({ conversations: [] });
      }
      if (path === "/api/v1/models") {
        return Promise.resolve({ models: [{ name: "llama3" }, { name: "gpt-4" }] });
      }
      if (path.startsWith("/api/v1/conversations/")) {
        return Promise.resolve({ messages: [] });
      }
      return Promise.resolve({});
    });
    render(<ChatPage />);
    await waitFor(() => {
      expect(screen.getByText("llama3")).toBeInTheDocument();
    });
    expect(screen.getByText("gpt-4")).toBeInTheDocument();
    expect(screen.getAllByText("Default model").length).toBeGreaterThan(0);
  });

  it("handles empty state (no conversations)", async () => {
    render(<ChatPage />);
    await waitFor(() => {
      expect(screen.getByText("Start a conversation with Cortex.")).toBeInTheDocument();
    });
  });

  it("sends message on Enter key and calls fetch", async () => {
    mockGet.mockImplementation((path: string) => {
      if (path === "/api/v1/conversations") {
        return Promise.resolve({
          conversations: [{ id: 1, title: "Chat 1", repo_id: null, model_used: null, message_count: 0, total_tokens: 0, created_at: null, updated_at: null }],
        });
      }
      if (path === "/api/v1/models") {
        return Promise.resolve({ models: [] });
      }
      if (path.startsWith("/api/v1/conversations/")) {
        return Promise.resolve({ messages: [] });
      }
      return Promise.resolve({});
    });

    render(<ChatPage />);
    await waitFor(() => {
      expect(screen.getByPlaceholderText("Ask Cortex anything...")).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText("Ask Cortex anything...");
    fireEvent.change(input, { target: { value: "Hello Cortex" } });
    fireEvent.keyDown(input, { key: "Enter" });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/v1/conversations/1/messages",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ content: "Hello Cortex" }),
        })
      );
    });
  });

  it("sends message via Send button click", async () => {
    mockGet.mockImplementation((path: string) => {
      if (path === "/api/v1/conversations") {
        return Promise.resolve({
          conversations: [{ id: 1, title: "Chat 1", repo_id: null, model_used: null, message_count: 0, total_tokens: 0, created_at: null, updated_at: null }],
        });
      }
      if (path === "/api/v1/models") {
        return Promise.resolve({ models: [] });
      }
      if (path.startsWith("/api/v1/conversations/")) {
        return Promise.resolve({ messages: [] });
      }
      return Promise.resolve({});
    });

    render(<ChatPage />);
    await waitFor(() => {
      expect(screen.getByText("Chat 1")).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText("Ask Cortex anything...");
    fireEvent.change(input, { target: { value: "Test message" } });

    const sendBtn = document.querySelector("button.bg-accent") as HTMLButtonElement;
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/v1/conversations/1/messages",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ content: "Test message" }),
        })
      );
    });
  });

  it("displays user message in conversation after sending", async () => {
    mockGet.mockImplementation((path: string) => {
      if (path === "/api/v1/conversations") {
        return Promise.resolve({
          conversations: [{ id: 1, title: "Chat 1", repo_id: null, model_used: null, message_count: 0, total_tokens: 0, created_at: null, updated_at: null }],
        });
      }
      if (path === "/api/v1/models") {
        return Promise.resolve({ models: [] });
      }
      if (path.startsWith("/api/v1/conversations/")) {
        return Promise.resolve({ messages: [] });
      }
      return Promise.resolve({});
    });

    render(<ChatPage />);
    await waitFor(() => {
      expect(screen.getByPlaceholderText("Ask Cortex anything...")).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText("Ask Cortex anything...");
    fireEvent.change(input, { target: { value: "Visible message" } });
    fireEvent.keyDown(input, { key: "Enter" });

    await waitFor(() => {
      expect(screen.getByText("Visible message")).toBeInTheDocument();
    });
  });
});
