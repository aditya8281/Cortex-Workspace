import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { sanitizePersistedStorage } from "@/lib/storage";
import "./index.css";
import App from "./App.tsx";
import { ErrorBoundary } from "@/components/ErrorBoundary";

sanitizePersistedStorage();

const rootEl = document.getElementById("root");
if (!rootEl) {
  throw new Error("Root element #root not found");
}

createRoot(rootEl).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
);
