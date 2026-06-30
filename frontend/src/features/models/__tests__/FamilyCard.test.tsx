import { render, screen, fireEvent } from "@testing-library/react";
import { FamilyCard } from "../components/FamilyCard";

const mockFamily = {
  family: "qwen3",
  display_name: "Qwen3",
  model_count: 5,
  capabilities: ["chat", "thinking"],
  default_variant: {
    model_id: "qwen3:8b",
    parameter_count: 8.0,
    size_gb: 4.7,
    size_bytes: 4700000000,
    quantization: "Q4_K_M",
    context_length: 4096,
    downloaded: false,
    license: "Apache-2.0",
    embedding_dim: null,
  },
  context_range: [4096, 131072] as [number, number],
  param_range: [0.6, 235.0] as [number, number],
  license: "Apache-2.0",
  embedding_dim: null,
};

describe("FamilyCard", () => {
  it("renders family name", () => {
    render(<FamilyCard family={mockFamily} ram_gb={32} />);
    expect(screen.getByText("Qwen3")).toBeInTheDocument();
  });

  it("renders variant count summary", () => {
    render(<FamilyCard family={mockFamily} ram_gb={32} />);
    expect(screen.getByText(/5 variants/)).toBeInTheDocument();
  });

  it("shows default variant name", () => {
    render(<FamilyCard family={mockFamily} ram_gb={32} />);
    expect(screen.getByText("qwen3:8b")).toBeInTheDocument();
  });

  it("shows download button when not downloaded", () => {
    const onDownload = vi.fn();
    render(<FamilyCard family={mockFamily} ram_gb={32} onDownload={onDownload} />);
    expect(screen.getByText("Download")).toBeInTheDocument();
  });

  it("shows installed badge when downloaded", () => {
    const downloadedFamily = {
      ...mockFamily,
      default_variant: { ...mockFamily.default_variant, downloaded: true },
    };
    render(<FamilyCard family={downloadedFamily} ram_gb={32} />);
    expect(screen.getByText("Installed")).toBeInTheDocument();
  });

  it("calls onViewDetail when View Details clicked", () => {
    const onViewDetail = vi.fn();
    render(<FamilyCard family={mockFamily} ram_gb={32} onViewDetail={onViewDetail} />);
    fireEvent.click(screen.getByText("View Details"));
    expect(onViewDetail).toHaveBeenCalledWith("qwen3");
  });
});
