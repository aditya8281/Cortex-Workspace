import { render, type RenderOptions } from "@testing-library/react";
import React from "react";

function TestWrapper({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

export function renderWithProviders(
  ui: React.ReactElement,
  options?: Omit<RenderOptions, "wrapper">
) {
  return render(ui, { wrapper: TestWrapper, ...options });
}

export * from "@testing-library/react";
export { renderWithProviders as render };
