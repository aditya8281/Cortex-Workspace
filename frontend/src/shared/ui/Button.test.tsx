import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import Button from "./Button";

describe("Button", () => {
  it("renders children", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("applies variant classes", () => {
    render(<Button variant="primary">Primary</Button>);
    const btn = screen.getByText("Primary");
    expect(btn.className).toContain("bg-accent");
  });

  it("fires click handler", () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click me</Button>);
    fireEvent.click(screen.getByText("Click me"));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("shows loading spinner when loading", () => {
    render(<Button loading>Sending</Button>);
    const btn = screen.getByRole("button");
    expect(btn.querySelector("svg")).toBeInTheDocument();
    expect(btn).toBeDisabled();
  });

  it("prevents click when disabled", () => {
    const onClick = vi.fn();
    render(<Button disabled onClick={onClick}>Disabled</Button>);
    fireEvent.click(screen.getByText("Disabled"));
    expect(onClick).not.toHaveBeenCalled();
  });

  it("prevents click when loading", () => {
    const onClick = vi.fn();
    render(<Button loading onClick={onClick}>Loading</Button>);
    fireEvent.click(screen.getByText("Loading"));
    expect(onClick).not.toHaveBeenCalled();
  });

  it("applies danger variant classes", () => {
    render(<Button variant="danger">Delete</Button>);
    const btn = screen.getByText("Delete");
    expect(btn.className).toContain("bg-error");
    expect(btn.className).toContain("text-error");
  });

  it("applies secondary variant classes", () => {
    render(<Button variant="secondary">Cancel</Button>);
    const btn = screen.getByText("Cancel");
    expect(btn.className).toContain("bg-bg-surface");
    expect(btn.className).toContain("border-border-subtle");
  });

  it("applies ghost variant classes", () => {
    render(<Button variant="ghost">Ghost</Button>);
    const btn = screen.getByText("Ghost");
    expect(btn.className).toContain("text-text-secondary");
  });
});
