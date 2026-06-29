import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

describe("App", () => {
  it("smoke: renders a basic element", () => {
    // verifies the test suite is wired correctly
    render(<div data-testid="smoke">ok</div>);
    expect(screen.getByTestId("smoke")).toHaveTextContent("ok");
  });

  it("loads testing-library matchers", () => {
    render(<div data-testid="hello">world</div>);
    expect(screen.getByTestId("hello")).toHaveTextContent("world");
  });
});
