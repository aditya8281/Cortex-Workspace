import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import DashboardPage from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
}));

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: any) => <a href={href} {...props}>{children}</a>,
}));

vi.mock("@/shared/auth/cortexApi", () => ({
  apiSystemMetrics: vi.fn(),
  apiSystemLogs: vi.fn(),
}));

vi.mock("@/shared/api", () => ({
  memoryApi: { list: vi.fn().mockResolvedValue({ total: 5, entries: [] }) },
  agentApi: { list: vi.fn().mockResolvedValue({ agents: [] }) },
}));

vi.mock("@/shared/hooks/useSystemWebSocket", () => ({
  useSystemWebSocket: () => {},
}));

vi.mock("@/shared/components/SyncStatus", () => ({
  default: () => <div data-testid="sync-status" />,
}));

vi.mock("@/shared/ui/NeuralNetwork", () => ({
  default: () => <div data-testid="neural-network" />,
}));

vi.mock("@/shared/ui/MetricRing", () => ({
  MetricRing: ({ label, value }: { label: string; value: number }) => (
    <div data-testid={`metric-ring-${label.toLowerCase()}`}>{label}: {value}</div>
  ),
}));

vi.mock("@/shared/ui/TabGroup", () => ({
  TabGroup: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TabPanel: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/shared/ui/Card", () => ({
  default: ({ children, ...props }: any) => <div>{children}</div>,
}));

vi.mock("@/shared/layout/DashboardShell", () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
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
      created_at: "2024-01-01T00:00:00Z",
      updated_at: null,
    },
    loading: false,
    login: vi.fn(),
  }),
}));

const { apiSystemMetrics, apiSystemLogs } = await import("@/shared/auth/cortexApi");

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(apiSystemMetrics).mockResolvedValue({
    cpu_percent: 42.5,
    ram_total_gb: 16,
    ram_used_gb: 8,
    ram_percent: 50,
    gpu_name: "NVIDIA RTX 3080",
    gpu_type: "cuda",
    gpu_percent: 30,
    disk_total_gb: 500,
    disk_used_gb: 200,
    disk_percent: 40,
    processes: [
      { pid: 1, name: "node", cpu: 5.2, memory: 3.1, status: "running" },
    ],
  });
  vi.mocked(apiSystemLogs).mockResolvedValue({
    logs: [
      { timestamp: "2024-01-01T12:00:00Z", level: "info", logger: "test", message: "System started", request_id: "1", module: "main", pathname: "main.py", lineno: 1 },
    ],
    total: 1,
  });
});

describe("Dashboard Page", () => {
  it("renders welcome message for authenticated user", async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText(/Welcome back, Test/)).toBeInTheDocument();
    });
  });

  it("shows system metrics (CPU, RAM, Disk) after data loads", async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByTestId("metric-ring-cpu")).toHaveTextContent("42.5");
      expect(screen.getByTestId("metric-ring-ram")).toHaveTextContent("50");
      expect(screen.getByTestId("metric-ring-disk")).toHaveTextContent("40");
    });
  });

  it("shows loading state while data is fetching", async () => {
    vi.mocked(apiSystemMetrics).mockReturnValue(new Promise(() => {}));
    vi.mocked(apiSystemLogs).mockReturnValue(new Promise(() => {}));
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText(/Welcome back, Test/)).toBeInTheDocument();
    });
  });

  it("handles API error gracefully", async () => {
    vi.mocked(apiSystemMetrics).mockRejectedValue(new Error("Network error"));
    vi.mocked(apiSystemLogs).mockRejectedValue(new Error("Network error"));
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText(/Welcome back, Test/)).toBeInTheDocument();
    });
  });
});
