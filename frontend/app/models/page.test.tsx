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
const mockAutocomplete = vi.fn();
const mockDownload = vi.fn();
const mockCancel = vi.fn();

vi.mock("@/shared/api", () => ({
  modelsApi: {
    recommendedEnhanced: (...args: unknown[]) => mockRecommendedEnhanced(...args),
    list: (...args: unknown[]) => mockList(...args),
    autocomplete: (...args: unknown[]) => mockAutocomplete(...args),
    download: (...args: unknown[]) => mockDownload(...args),
    cancel: (...args: unknown[]) => mockCancel(...args),
    getSettings: vi.fn().mockResolvedValue({ inference_backend: "auto", huggingface_token: null, auto_download: true, max_concurrent_downloads: 2 }),
    updateSettings: vi.fn().mockResolvedValue({}),
  },
}));

vi.mock("@/shared/hooks/useSystemWebSocket", () => ({
  useSystemWebSocket: () => ({ status: "disconnected", close: vi.fn(), reconnect: vi.fn() }),
}));

vi.mock("@/shared/layout/DashboardShell", () => ({
  default: ({ children }: { children: React.ReactNode }) => <div data-testid="dashboard-shell">{children}</div>,
}));

vi.mock("@/shared/ui/NeuralNetwork", () => ({
  default: () => <div data-testid="neural-network" />,
}));

vi.mock("@/shared/ui/Card", () => ({
  default: ({ children, ...props }: any) => <div data-testid="card">{children}</div>,
}));

vi.mock("@/shared/ui/Button", () => ({
  default: ({ children, ...props }: any) => <button {...props}>{children}</button>,
}));

vi.mock("./components/HardwareBar", () => ({
  default: ({ hardware, activeDownloads }: any) => (
    <div data-testid="hardware-bar">
      GPU: {hardware?.gpu?.name} | Downloads: {activeDownloads}
    </div>
  ),
}));

vi.mock("./components/SearchBar", () => ({
  default: (props: any) => (
    <div data-testid="search-bar">
      <input data-testid="search-input" value={props.searchQuery} onChange={(e: any) => props.onSearchChange(e.target.value)} />
    </div>
  ),
}));

vi.mock("./components/RecommendedRow", () => ({
  default: ({ recommendations }: any) => (
    <div data-testid="recommended-row">
      {recommendations.map((rec: any) => (
        <span key={rec.model_id} data-testid={`rec-${rec.model_id}`}>{rec.display_name}</span>
      ))}
    </div>
  ),
}));

vi.mock("./components/CategorySection", () => ({
  default: ({ title, models }: any) => (
    <div data-testid="category-section" data-title={title}>
      {models.map((m: any) => (
        <span key={m.model_id} data-testid={`model-${m.model_id}`}>{m.display_name || m.name}</span>
      ))}
    </div>
  ),
}));

vi.mock("./components/ModelCard", () => ({
  default: ({ model }: any) => <div data-testid="model-card">{model.display_name}</div>,
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

const mockListResponse = {
  models: [
    { name: "llama3.1", display_name: "Llama 3.1", provider: "ollama", model_type: "chat", parameter_count: "8B", context_length: 128000, capabilities: ["chat"], description: "Meta Llama 3.1", downloaded: false, variants: ["llama3.1:8b", "llama3.1:70b"], hardware_requirements: { min_ram_gb: 8, recommended_ram_gb: 16 }, model_id: "llama3.1", family: "llama", architecture: "transformer", license: "llama3.1" },
  ],
  total_count: 1, downloaded_count: 0, available_from_providers: [],
  type_counts: { chat: 1 }, size_counts: { all: 1, "<3B": 0, "3-8B": 0, "8-14B": 1, "14B+": 0 },
};

beforeEach(() => {
  vi.clearAllMocks();
  mockRecommendedEnhanced.mockResolvedValue({
    hardware: mockHardware,
    workloads: mockWorkloads,
  });
  mockList.mockResolvedValue(mockListResponse);
  mockAutocomplete.mockResolvedValue({ suggestions: ["llama3.1", "llama3.2"] });
  mockDownload.mockResolvedValue({ download_id: "dl-1" });
  mockCancel.mockResolvedValue({ cancelled: true });
});

describe("Models Page", () => {
  it("renders the Models heading", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByText("Models")).toBeInTheDocument();
    });
  });

  it("shows loading state initially", () => {
    mockRecommendedEnhanced.mockReturnValue(new Promise(() => {}));
    mockList.mockReturnValue(new Promise(() => {}));
    render(<ModelsPage />);
    expect(document.querySelector(".shimmer-bg")).toBeInTheDocument();
  });

  it("shows hardware bar when hardware data is available", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByTestId("hardware-bar")).toBeInTheDocument();
      expect(screen.getByTestId("hardware-bar")).toHaveTextContent("RTX 3080");
    });
  });

  it("shows recommended row when recommendations exist", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByTestId("recommended-row")).toBeInTheDocument();
      expect(screen.getByTestId("rec-llama3.1:8b")).toHaveTextContent("Llama 3.1 8B");
    });
  });

  it("shows category sections for each workload", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      const sections = screen.getAllByTestId("category-section");
      expect(sections.length).toBeGreaterThanOrEqual(2);
      expect(sections[0]).toHaveAttribute("data-title", "General");
      expect(sections[1]).toHaveAttribute("data-title", "Coding");
    });
  });

  it("shows search bar", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByTestId("search-bar")).toBeInTheDocument();
    });
  });

  it("displays error state when API fails", async () => {
    mockRecommendedEnhanced.mockRejectedValue(new Error("Network error"));
    mockList.mockRejectedValue(new Error("Network error"));
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("renders inside DashboardShell", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByTestId("dashboard-shell")).toBeInTheDocument();
    });
  });
});
