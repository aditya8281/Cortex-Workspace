import { render, screen } from "@testing-library/react";
import { VariantRow } from "../components/VariantRow";

const mockVariant = {
  model_id: "qwen3:8b",
  parameter_count: 8.0,
  size_gb: 4.7,
  size_bytes: 4700000000,
  quantization: "Q4_K_M",
  context_length: 4096,
  downloaded: false,
  license: "Apache-2.0",
  embedding_dim: null,
};

describe("VariantRow", () => {
  it("renders model name and params", () => {
    render(<VariantRow variant={mockVariant} ramFitPercent={75} ramFitStatus="good" />);
    expect(screen.getByText("qwen3:8b")).toBeInTheDocument();
  });

  it("shows download button when not downloaded", () => {
    render(<VariantRow variant={mockVariant} ramFitPercent={75} ramFitStatus="good" />);
    expect(screen.getByText("Download")).toBeInTheDocument();
  });

  it("shows installed badge when downloaded", () => {
    render(<VariantRow variant={{ ...mockVariant, downloaded: true }} ramFitPercent={75} ramFitStatus="good" />);
    expect(screen.getByText("Installed")).toBeInTheDocument();
  });

  it("shows size in GB", () => {
    render(<VariantRow variant={mockVariant} ramFitPercent={75} ramFitStatus="good" />);
    expect(screen.getByText("4.7 GB")).toBeInTheDocument();
  });

  it("shows quantization", () => {
    render(<VariantRow variant={mockVariant} ramFitPercent={75} ramFitStatus="good" />);
    expect(screen.getByText("Q4_K_M")).toBeInTheDocument();
  });
});
