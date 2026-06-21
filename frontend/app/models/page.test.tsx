import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ModelsPage from "./ModelsPage";

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

const mockRecommendedEnhanced = vi.fn();

vi.mock("@/shared/api", () => ({
  modelsApi: {
    recommendedEnhanced: (...args: any[]) => mockRecommendedEnhanced(...args),
  },
}));

vi.mock("@/shared/ui/NeuralNetwork", () => ({
  default: () => <div data-testid="neural-network" />,
}));

vi.mock("@/shared/ui/Card", () => ({
  default: ({ children, ...props }: any) => <div>{children}</div>,
}));

vi.mock("@/shared/ui/Button", () => ({
  default: ({ children, ...props }: any) => <button {...props}>{children}</button>,
}));

vi.mock("@/shared/ui/TabGroup", () => ({
  TabGroup: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TabPanel: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/shared/layout/DashboardShell", () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("./HardwareOverview", () => ({
  default: ({ hardware }: any) => (
    <div data-testid="hardware-overview">
      RAM: {hardware?.ram_gb}GB
    </div>
  ),
}));

vi.mock("./WorkloadRecommendations", () => ({
  default: ({ workloads }: any) => (
    <div data-testid="workload-recommendations">
      {Object.keys(workloads || {}).join(", ")}
    </div>
  ),
}));

vi.mock("./ModelBrowser", () => ({
  default: () => <div data-testid="model-browser" />,
}));

vi.mock("./InstalledModelsPanel", () => ({
  default: () => <div data-testid="installed-models" />,
}));

vi.mock("./DownloadQueuePanel", () => ({
  default: () => <div data-testid="download-queue" />,
}));

beforeEach(() => {
  vi.clearAllMocks();
  mockRecommendedEnhanced.mockResolvedValue({
    hardware: { ram_gb: 32, ram_available_gb: 16, ram_percent: 50, cpu_count: 8, cpu_threads: 16, cpu_freq_mhz: 3600, cpu_arch: "x86_64", gpu: { available: true, name: "RTX 3080", type: "cuda", vram_gb: 10, vram_available_gb: 7, memory_bandwidth_gbps: 760, compute_capability: "8.6", arch: "ampere" }, disk_free_gb: 200, supports_cuda: true, supports_metal: false },
    workloads: {
      general: { label: "General", description: "General purpose", recommendations: [] },
      coding: { label: "Coding", description: "Code generation", recommendations: [] },
    },
  });
});

describe("Models Page", () => {
  it("renders model list heading", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByText("Models")).toBeInTheDocument();
    });
  });

  it("shows hardware overview section", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByTestId("hardware-overview")).toHaveTextContent("RAM: 32GB");
    });
  });

  it("shows download queue panel in downloads tab", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByTestId("download-queue")).toBeInTheDocument();
    });
  });

  it("handles model selection via workload recommendations", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByTestId("workload-recommendations")).toHaveTextContent("general, coding");
    });
  });

  it("shows installed models panel", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByTestId("installed-models")).toBeInTheDocument();
    });
  });
});
