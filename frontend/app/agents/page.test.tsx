import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import AgentsPage from "./page";

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

vi.mock("../../src/shared/api/agent", () => ({
  agentApi: {
    list: vi.fn(),
    create: vi.fn(),
    listRuns: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

vi.mock("../../src/shared/ui/Button", () => ({
  default: ({ children, onClick, loading, ...props }: any) => (
    <button onClick={onClick} disabled={loading} {...props}>{children}</button>
  ),
}));

vi.mock("../../src/shared/layout/DashboardShell", () => ({
  default: ({ children }: any) => <div>{children}</div>,
}));

vi.mock("../../src/shared/ui/CollapsiblePanel", () => ({
  CollapsiblePanel: ({ children, header }: any) => (
    <div>
      <div data-testid="panel-header">{header}</div>
      {children}
    </div>
  ),
}));

vi.mock("./AgentChat", () => ({
  default: ({ agent }: any) => <div data-testid="agent-chat">{agent.name}</div>,
}));

vi.mock("./AgentEditor", () => ({
  default: ({ open, onClose }: any) =>
    open ? <div data-testid="agent-editor"><button onClick={onClose}>Close</button></div> : null,
}));

vi.mock("../../src/shared/ui/NeuralNetwork", () => ({
  default: () => <div data-testid="neural-network" />,
}));

const { agentApi } = await import("../../src/shared/api/agent");

const mockAgents = [
  { id: 1, name: "Test Agent", description: "A test agent", system_prompt: "You are a test", tools: [], is_active: true, model_id: null, created_at: "2024-01-01T00:00:00Z", updated_at: null },
];

const mockRuns = [
  { id: 1, agent_id: 1, input: "Test input", status: "completed", output: "Test output", created_at: "2024-01-01T00:00:00Z", updated_at: null },
];

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(agentApi.list).mockResolvedValue({ agents: mockAgents });
  vi.mocked(agentApi.listRuns).mockResolvedValue({ runs: mockRuns });
  vi.mocked(agentApi.create).mockResolvedValue({
    agent: { id: 2, name: "New Agent", description: "New", system_prompt: "New prompt", tools: [], is_active: true, model_id: null, created_at: "2024-01-02T00:00:00Z", updated_at: null },
  });
});

describe("Agents Page", () => {
  it("renders agent list", async () => {
    render(<AgentsPage />);
    await waitFor(() => {
      expect(screen.getByText("Test Agent")).toBeInTheDocument();
    });
  });

  it("creates new agent", async () => {
    render(<AgentsPage />);
    await waitFor(() => {
      expect(screen.getByText("Test Agent")).toBeInTheDocument();
    });
    const buttons = screen.getAllByRole("button");
    const plusButton = buttons.find((btn) => btn.querySelector("svg"));
    if (plusButton) {
      fireEvent.click(plusButton);
    }
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Create Agent" })).toBeInTheDocument();
    });
  });

  it("opens agent chat", async () => {
    render(<AgentsPage />);
    await waitFor(() => {
      expect(screen.getByText("Test Agent")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Test Agent"));
    await waitFor(() => {
      expect(screen.getByTestId("agent-chat")).toBeInTheDocument();
    });
  });

  it("shows agent configuration", async () => {
    render(<AgentsPage />);
    await waitFor(() => {
      expect(screen.getByText("Test Agent")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Test Agent"));
    await waitFor(() => {
      expect(screen.getByText("Edit")).toBeInTheDocument();
    });
  });
});
