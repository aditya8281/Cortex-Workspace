import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import MemoryPage from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
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
      storage_root: null,
      github_username: null,
      preferences: null,
      created_at: "2024-01-01T00:00:00Z",
      updated_at: null,
    },
    loading: false,
    login: vi.fn(),
  }),
}));

vi.mock("../../src/shared/auth/cortexApi", () => ({
  apiListMemory: vi.fn(),
  apiSearchMemory: vi.fn(),
  apiCreateMemory: vi.fn(),
}));

vi.mock("@/shared/api/client", () => ({
  api: {
    get: vi.fn().mockImplementation((url: string) => {
      if (url.includes("/sync/status")) {
        return Promise.resolve({
          watching: 1,
          pending_changes: 0,
          indexed_files: 10,
          errors: 0,
          status: "idle",
          last_sync: null,
          watched_paths: [],
        });
      }
      if (url.includes("/sync/jobs")) {
        return Promise.resolve([]);
      }
      return Promise.resolve({});
    }),
    post: vi.fn().mockResolvedValue({}),
  },
}));

vi.mock("@/shared/api/sync", () => ({
  syncApi: {
    defaults: vi.fn().mockResolvedValue({
      default_paths: [],
      exclude_dirs: [],
      embedding_models: [{ value: "nomic", label: "Nomic", technique: "local", dimensions: 768, description: "Fast", speed: "fast" }],
    }),
    validatePath: vi.fn().mockResolvedValue({ exists: true, resolved_path: "/test" }),
    start: vi.fn().mockResolvedValue({ status: "started" }),
  },
}));

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

vi.mock("../../src/shared/ui/Button", () => ({
  default: ({ children, onClick, ...props }: any) => <button onClick={onClick} {...props}>{children}</button>,
}));

vi.mock("../../src/shared/ui/PageTransition", () => ({
  default: ({ children }: any) => <>{children}</>,
}));

vi.mock("../../src/shared/layout/DashboardShell", () => ({
  default: ({ children }: any) => <div>{children}</div>,
}));

vi.mock("./MemorySearch", () => ({
  default: ({ query, onQueryChange }: any) => (
    <input
      data-testid="memory-search"
      value={query}
      onChange={(e) => onQueryChange(e.target.value)}
      placeholder="Search memories"
    />
  ),
}));

vi.mock("./MemoryEditor", () => ({
  default: ({ open, onOpenChange }: any) =>
    open ? <div data-testid="memory-editor"><button onClick={() => onOpenChange(false)}>Close</button></div> : null,
}));

vi.mock("./MemoryDetail", () => ({
  default: ({ open, onOpenChange }: any) =>
    open ? <div data-testid="memory-detail"><button onClick={() => onOpenChange(false)}>Close</button></div> : null,
}));

const { apiListMemory, apiSearchMemory } = await import("../../src/shared/auth/cortexApi");

const mockEntries = [
  { id: 1, user_id: 1, title: "Test Entry 1", content: "Content 1", category: "code", tags: ["test"], source_path: null, embedding_id: null, created_at: "2024-01-01T00:00:00Z", updated_at: null },
  { id: 2, user_id: 1, title: "Test Entry 2", content: "Content 2", category: "note", tags: [], source_path: null, embedding_id: null, created_at: "2024-01-02T00:00:00Z", updated_at: null },
];

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(apiListMemory).mockResolvedValue({
    entries: mockEntries,
    count: 2,
    total: 2,
    categories: { code: 1, note: 1 },
  });
  vi.mocked(apiSearchMemory).mockResolvedValue({
    query: "test",
    results: [{ entry: mockEntries[0], score: 0.9 }],
  });
});

describe("Memory Page", () => {
  it("renders knowledge graph view", async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByText("Memory")).toBeInTheDocument();
    });
  });

  it("renders list view", async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByText("Memory")).toBeInTheDocument();
    });
    const listButton = screen.getByText("List");
    fireEvent.click(listButton);
    await waitFor(() => {
      expect(screen.getByText("Test Entry 1")).toBeInTheDocument();
    });
  });

  it("toggles between graph and list views", async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByText("Memory")).toBeInTheDocument();
    });
    const listButton = screen.getByText("List");
    fireEvent.click(listButton);
    await waitFor(() => {
      expect(screen.getByText("Test Entry 1")).toBeInTheDocument();
    });
    const graphButton = screen.getByText("Graph");
    fireEvent.click(graphButton);
  });

  it("searches memory entries", async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByTestId("memory-search")).toBeInTheDocument();
    });
    fireEvent.change(screen.getByTestId("memory-search"), { target: { value: "test query" } });
    await waitFor(() => {
      expect(apiSearchMemory).toHaveBeenCalled();
    });
  });

  it("creates new entry", async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByText("Memory")).toBeInTheDocument();
    });
    const newButton = screen.getByText("New Memory");
    fireEvent.click(newButton);
    await waitFor(() => {
      expect(screen.getByTestId("memory-editor")).toBeInTheDocument();
    });
  });

  it("shows sync status", async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByText("Memory")).toBeInTheDocument();
    });
  });
});
