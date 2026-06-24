import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import SearchPage from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
}));

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

vi.mock("@/shared/layout/DashboardShell", () => ({
  default: ({ children }: any) => <div>{children}</div>,
}));

vi.mock("@/shared/ui/Card", () => ({
  Card: ({ children, ...props }: any) => <div {...props}>{children}</div>,
}));

vi.mock("@/shared/ui/NeuralNetwork", () => ({
  default: () => <div data-testid="neural-network" />,
}));

vi.mock("@/shared/api", () => ({
  searchApi: {
    unified: vi.fn(),
    answer: vi.fn(),
  },
}));

const { searchApi } = await import("@/shared/api");

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(searchApi.unified).mockResolvedValue({
    query: "test",
    total: 2,
    results: [
      { file_path: "src/test.ts", content: "Test content", source: "code", score: 0.9, document_id: 1, language: "typescript", chunk_type: "code" },
      { file_path: "memory/test.md", content: "Memory content", source: "memory", score: 0.8, document_id: 2, language: "markdown", chunk_type: "text" },
    ],
    next_cursor: null,
    has_more: false,
  });
  vi.mocked(searchApi.answer).mockResolvedValue({
    query: "test",
    answer: "This is an AI-generated answer about the search query.",
    results: [],
  });
});

describe("Search Page", () => {
  it("renders search input", () => {
    render(<SearchPage />);
    expect(screen.getByPlaceholderText(/Ask anything about your code/)).toBeInTheDocument();
  });

  it("performs search and displays results", async () => {
    render(<SearchPage />);
    const input = screen.getByPlaceholderText(/Ask anything about your code/);
    fireEvent.change(input, { target: { value: "test query" } });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => {
      expect(searchApi.unified).toHaveBeenCalledWith("test query", { max_results: 20 });
      expect(screen.getByText("src/test.ts")).toBeInTheDocument();
      expect(screen.getByText("memory/test.md")).toBeInTheDocument();
    });
  });

  it("shows AI answer panel", async () => {
    render(<SearchPage />);
    const input = screen.getByPlaceholderText(/Ask anything about your code/);
    fireEvent.change(input, { target: { value: "test query" } });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => {
      expect(screen.getByText("AI Answer")).toBeInTheDocument();
      expect(screen.getByText(/AI-generated answer/)).toBeInTheDocument();
    });
  });

  it("handles empty results", async () => {
    vi.mocked(searchApi.unified).mockResolvedValue({ query: "empty", total: 0, results: [], next_cursor: null, has_more: false });
    vi.mocked(searchApi.answer).mockResolvedValue({ query: "empty", answer: "No results found.", results: [] });
    render(<SearchPage />);
    const input = screen.getByPlaceholderText(/Ask anything about your code/);
    fireEvent.change(input, { target: { value: "empty query" } });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => {
      expect(screen.getByText("AI Answer")).toBeInTheDocument();
    });
  });

  it("shows loading state during search", async () => {
    vi.mocked(searchApi.unified).mockReturnValue(new Promise(() => {}));
    vi.mocked(searchApi.answer).mockReturnValue(new Promise(() => {}));
    render(<SearchPage />);
    const input = screen.getByPlaceholderText(/Ask anything about your code/);
    fireEvent.change(input, { target: { value: "loading query" } });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => {
      expect(screen.getByText("Searching...")).toBeInTheDocument();
    });
  });
});
