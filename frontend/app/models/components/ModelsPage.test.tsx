import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import HardwareBar from "./HardwareBar";

const mockHardware = {
  gpu: { available: true, name: "RTX 4090", type: "cuda", vram_gb: 24, vram_available_gb: 24, memory_bandwidth_gbps: 1008, compute_capability: "8.9", arch: "ada" },
  ram_gb: 64, ram_available_gb: 32, ram_percent: 50,
  cpu_count: 16, cpu_threads: 32, cpu_freq_mhz: 3500, cpu_arch: "x86_64",
  disk_free_gb: 200, supports_cuda: true, supports_metal: false,
};

describe("HardwareBar", () => {
  it("renders GPU name and VRAM", () => {
    render(<HardwareBar hardware={mockHardware} activeDownloads={0} />);
    expect(screen.getByText(/RTX 4090/)).toBeDefined();
    expect(screen.getByText(/24/)).toBeDefined();
  });

  it("shows CUDA badge when supports_cuda is true", () => {
    render(<HardwareBar hardware={mockHardware} activeDownloads={0} />);
    expect(screen.getByText(/CUDA/)).toBeDefined();
  });

  it("shows active download count when > 0", () => {
    render(<HardwareBar hardware={mockHardware} activeDownloads={3} />);
    expect(screen.getByText("3 downloading")).toBeDefined();
  });
});

import PickCard from "./PickCard";

const mockRec = {
  model_id: "llama-3.1-8b",
  display_name: "Llama 3.1 8B",
  family: "llama",
  parameter_count: "8B",
  capabilities: ["chat", "reasoning"],
  description: "Best balance of speed and quality",
  score: 0.82,
  variant: { quantization: "Q5_K_M", size_gb: 4.2, vram_required_gb: 5.1, quality_score: 0.85 },
  performance: { tokens_per_second: 45, prompt_eval_tps: 52, memory_usage_gb: 4.2, vram_usage_gb: 5.1, quantization_quality: "high", quality_notes: "", speed_rating: "fast", fit_rating: "excellent", context_length_max: 128000 },
  explanation: { why: "Best balance for your hardware", tradeoff: "Slightly slower than Q4", suitability: "Excellent fit" },
};

describe("PickCard", () => {
  it("renders model name and fit score", () => {
    render(<PickCard recommendation={mockRec} isActive={true} onDownload={vi.fn()} />);
    expect(screen.getByText(/Llama 3.1 8B/)).toBeDefined();
    expect(screen.getByText(/82%/)).toBeDefined();
  });

  it("shows variant chips when active", () => {
    render(<PickCard recommendation={mockRec} isActive={true} onDownload={vi.fn()} />);
    expect(screen.getByText(/Q5_K_M/)).toBeDefined();
  });

  it("hides variant chips when not active", () => {
    render(<PickCard recommendation={mockRec} isActive={false} onDownload={vi.fn()} />);
    expect(screen.queryByText(/Q5_K_M/)).toBeNull();
  });
});

import TopPicksCarousel from "./TopPicksCarousel";

const mockRecs = Array.from({ length: 10 }, (_, i) => ({
  ...mockRec,
  model_id: `model-${i}`,
  display_name: `Model ${i}`,
  score: 0.9 - i * 0.05,
}));

describe("TopPicksCarousel", () => {
  it("renders all recommendation cards", () => {
    render(<TopPicksCarousel recommendations={mockRecs} onDownload={vi.fn()} />);
    expect(screen.getByText(/Model 0/)).toBeDefined();
    expect(screen.getByText(/Model 9/)).toBeDefined();
  });

  it("shows navigation arrows", () => {
    render(<TopPicksCarousel recommendations={mockRecs} onDownload={vi.fn()} />);
    expect(screen.getByRole("button", { name: /previous/i })).toBeDefined();
    expect(screen.getByRole("button", { name: /next/i })).toBeDefined();
  });

  it("shows dot indicators", () => {
    render(<TopPicksCarousel recommendations={mockRecs} onDownload={vi.fn()} />);
    const dots = screen.getAllByRole("button", { name: /go to slide/i });
    expect(dots.length).toBe(10);
  });
});

import WorkloadColumns from "./WorkloadColumns";

const mockWorkloads = {
  chat: { label: "Chat", description: "Conversational AI", recommendations: [mockRec, { ...mockRec, model_id: "phi-3", display_name: "Phi-3 14B", score: 0.75 }] },
  code: { label: "Code", description: "Code generation", recommendations: [{ ...mockRec, model_id: "codestral", display_name: "Codestral 7B", score: 0.78 }] },
};

describe("WorkloadColumns", () => {
  it("renders workload headers", () => {
    render(<WorkloadColumns workloads={mockWorkloads} onDownload={vi.fn()} />);
    expect(screen.getByText("Chat")).toBeDefined();
    expect(screen.getByText("Code")).toBeDefined();
  });

  it("renders top 3 models per workload", () => {
    render(<WorkloadColumns workloads={mockWorkloads} onDownload={vi.fn()} />);
    expect(screen.getByText(/Llama 3.1 8B/)).toBeDefined();
    expect(screen.getByText(/Phi-3 14B/)).toBeDefined();
    expect(screen.getByText(/Codestral 7B/)).toBeDefined();
  });
});

import { fireEvent, waitFor } from "@testing-library/react";
import CatalogTable from "./CatalogTable";

const mockCatalogModels = [
  { model_id: "llama-3.1-8b", name: "llama-3.1-8b", display_name: "Llama 3.1 8B", description: "", provider: "Meta", model_type: "chat" as const, parameter_count: "8B", context_length: 128000, capabilities: [], hardware_requirements: null, recommended: false, downloaded: false, size_bytes: 4500000000, variants: ["Q4_K_M", "Q5_K_M"], family: "llama", architecture: "transformer", license: "llama" },
  { model_id: "codestral-7b", name: "codestral-7b", display_name: "Codestral 7B", description: "", provider: "Mistral", model_type: "code" as const, parameter_count: "7B", context_length: 32000, capabilities: [], hardware_requirements: null, recommended: false, downloaded: false, size_bytes: 5100000000, variants: ["Q6_K"], family: "codestral", architecture: "transformer", license: "apache" },
];

describe("CatalogTable", () => {
  it("renders model names", () => {
    render(<CatalogTable models={mockCatalogModels} onDownload={vi.fn()} />);
    expect(screen.getByText("Llama 3.1 8B")).toBeDefined();
    expect(screen.getByText("Codestral 7B")).toBeDefined();
  });

  it("renders filter pills", () => {
    render(<CatalogTable models={mockCatalogModels} onDownload={vi.fn()} />);
    const allButtons = screen.getAllByText("All");
    expect(allButtons.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Chat")).toBeDefined();
    expect(screen.getByText("Code")).toBeDefined();
    expect(screen.getByText("Vision")).toBeDefined();
    expect(screen.getByText("Embed")).toBeDefined();
  });

  it("filters by type when pill is clicked", async () => {
    render(<CatalogTable models={mockCatalogModels} onDownload={vi.fn()} />);
    fireEvent.click(screen.getByText("Code"));
    await waitFor(() => {
      expect(screen.getByText("Codestral 7B")).toBeDefined();
      expect(screen.queryByText("Llama 3.1 8B")).toBeNull();
    });
  });
});

import InstalledBar from "./InstalledBar";

const mockInstalled = [
  { model_id: "llama-3.1-8b", display_name: "Llama 3.1 8B", variant: "Q5_K_M", size_gb: 4.2, last_used: "2h ago", usage_count: 1247 },
  { model_id: "codestral-7b", display_name: "Codestral 7B", variant: "Q6_K", size_gb: 5.1, last_used: "1d ago", usage_count: 89 },
];

describe("InstalledBar", () => {
  it("renders model count and storage", () => {
    render(<InstalledBar models={mockInstalled} onManage={vi.fn()} onChat={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.getByText(/2 installed/)).toBeDefined();
    expect(screen.getByText(/9.3 GB/)).toBeDefined();
  });

  it("expands to show model list on click", async () => {
    render(<InstalledBar models={mockInstalled} onManage={vi.fn()} onChat={vi.fn()} onDelete={vi.fn()} />);
    fireEvent.click(screen.getByText(/2 installed/));
    await waitFor(() => {
      expect(screen.getByText(/Llama 3.1 8B/)).toBeDefined();
      expect(screen.getByText(/Codestral 7B/)).toBeDefined();
    });
  });
});
