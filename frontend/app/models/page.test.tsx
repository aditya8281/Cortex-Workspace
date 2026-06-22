import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ModelsPage from "./ModelsPage";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
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
const mockList = vi.fn();
const mockInstalled = vi.fn();

vi.mock("@/shared/api", () => ({
  modelsApi: {
    recommendedEnhanced: (...args: unknown[]) => mockRecommendedEnhanced(...args),
    list: (...args: unknown[]) => mockList(...args),
    installed: (...args: unknown[]) => mockInstalled(...args),
    download: vi.fn().mockResolvedValue({ status: "started" }),
    delete: vi.fn().mockResolvedValue({ deleted: true }),
    autocomplete: vi.fn().mockResolvedValue({ suggestions: [] }),
    hardware: vi.fn().mockResolvedValue({}),
    health: vi.fn().mockResolvedValue({}),
    metrics: vi.fn().mockResolvedValue({}),
    progress: vi.fn().mockResolvedValue({ model: "", progress: 0 }),
    cancel: vi.fn().mockResolvedValue({ cancelled: true }),
    storage: vi.fn().mockResolvedValue({ total_disk_gb: 0, used_disk_gb: 0, free_disk_gb: 0, models_total_gb: 0, models: [], cache_gb: 0 }),
    refreshCatalogue: vi.fn().mockResolvedValue({ status: "ok", models_added: 0 }),
  },
}));

vi.mock("@/shared/hooks/useSystemWebSocket", () => ({
  useSystemWebSocket: () => ({ status: "disconnected", close: vi.fn(), reconnect: vi.fn() }),
}));

vi.mock("@/shared/layout/DashboardShell", () => ({
  default: ({ children }: { children: React.ReactNode }) => <div data-testid="dashboard-shell">{children}</div>,
}));

vi.mock("./components/HardwareBar", () => ({
  default: ({ hardware, activeDownloads }: any) => (
    <div data-testid="hardware-bar">
      GPU: {hardware?.gpu?.name} | Downloads: {activeDownloads}
    </div>
  ),
}));

vi.mock("./components/TopPicksCarousel", () => ({
  default: ({ recommendations }: any) => (
    <div data-testid="top-picks-carousel">
      {recommendations.map((rec: any) => (
        <span key={rec.model_id} data-testid={`pick-${rec.model_id}`}>{rec.display_name}</span>
      ))}
    </div>
  ),
}));

vi.mock("./components/WorkloadColumns", () => ({
  default: ({ workloads }: any) => (
    <div data-testid="workload-columns">
      {Object.entries(workloads).map(([id, wl]: [string, any]) => (
        <div key={id} data-testid={`workload-${id}`}>{wl.label}</div>
      ))}
    </div>
  ),
}));

vi.mock("./components/CatalogTable", () => ({
  default: ({ models }: any) => (
    <div data-testid="catalog-table">
      Browse all models
    </div>
  ),
}));

vi.mock("./components/InstalledBar", () => ({
  default: ({ models }: any) => (
    <div data-testid="installed-bar">
      {models.length} installed
    </div>
  ),
}));

const mockHardware = {
  ram_gb: 32, ram_available_gb: 16, ram_percent: 50,
  cpu_count: 8, cpu_threads: 16, cpu_freq_mhz: 3600, cpu_arch: "x86_64",
  gpu: { available: true, name: "RTX 3080", type: "cuda", vram_gb: 10, vram_available_gb: 7, memory_bandwidth_gbps: 760, compute_capability: "8.6", arch: "ampere" },
  disk_free_gb: 200, supports_cuda: true, supports_metal: false,
};

const mockWorkloads = {
  general: { label: "General", description: "General purpose", recommendations: [
    { model_id: "llama3.1:8b", display_name: "Llama 3.1 8B", family: "llama", parameter_count: "8B", capabilities: ["chat"], description: "Test", score: 85, variant: null, performance: null, explanation: { why: "Good", tradeoff: "None", suitability: "High" } },
  ] },
  coding: { label: "Coding", description: "Code generation", recommendations: [] },
};

describe("ModelsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRecommendedEnhanced.mockResolvedValue({
      hardware: mockHardware,
      workloads: mockWorkloads,
    });
    mockList.mockResolvedValue({ models: [], total_count: 0, downloaded_count: 0, available_from_providers: [], type_counts: {}, size_counts: {} });
    mockInstalled.mockResolvedValue({ models: [], installed_count: 0 });
  });

  it("renders the page title", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByText("Models")).toBeDefined();
    });
  });

  it("renders hardware bar with GPU info", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByTestId("hardware-bar")).toBeDefined();
      expect(screen.getByTestId("hardware-bar")).toHaveTextContent("RTX 3080");
    });
  });

  it("renders catalog section", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByTestId("catalog-table")).toBeDefined();
      expect(screen.getByText(/Browse all models/)).toBeDefined();
    });
  });

  it("renders workload columns", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByTestId("workload-columns")).toBeDefined();
      expect(screen.getByTestId("workload-general")).toHaveTextContent("General");
    });
  });

  it("renders installed bar", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByTestId("installed-bar")).toBeDefined();
    });
  });

  it("shows loading state initially", () => {
    mockRecommendedEnhanced.mockReturnValue(new Promise(() => {}));
    mockList.mockReturnValue(new Promise(() => {}));
    mockInstalled.mockReturnValue(new Promise(() => {}));
    render(<ModelsPage />);
    expect(document.querySelector(".shimmer-bg")).toBeInTheDocument();
  });

  it("displays error state when API fails", async () => {
    mockRecommendedEnhanced.mockRejectedValue(new Error("Network error"));
    mockList.mockRejectedValue(new Error("Network error"));
    mockInstalled.mockRejectedValue(new Error("Network error"));
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });
});
