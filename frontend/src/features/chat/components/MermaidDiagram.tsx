"use client";

import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";

// Initialize once with dark theme matching Cortex palette.
// securityLevel: "strict" so mermaid.render() throws on syntax errors
// instead of rendering inline error SVGs on the page.
mermaid.initialize({
  startOnLoad: false,
  theme: "dark",
  themeVariables: {
    primaryColor: "#1c1c1c",
    primaryTextColor: "#f0f0f0",
    primaryBorderColor: "rgba(0,172,193,0.3)",
    lineColor: "rgba(0,172,193,0.4)",
    secondaryColor: "#2a2a2a",
    tertiaryColor: "#1c1c1c",
    fontFamily: "Geist, system-ui, sans-serif",
    fontSize: "13px",
    noteBkgColor: "#2a2a2a",
    noteTextColor: "#f0f0f0",
    noteBorderColor: "rgba(255,255,255,0.12)",
    actorBkg: "#1c1c1c",
    actorTextColor: "#f0f0f0",
    actorBorder: "rgba(0,172,193,0.3)",
    signalColor: "#f0f0f0",
    signalTextColor: "#f0f0f0",
  },
  securityLevel: "strict",
});

interface MermaidDiagramProps {
  code: string;
}

export function MermaidDiagram({ code }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const id = `mermaid-${Math.random().toString(36).slice(2, 9)}`;

    mermaid
      .render(id, code.trim())
      .then(({ svg }) => {
        if (cancelled) return;
        // Mermaid returns an "error SVG" on syntax errors instead of
        // throwing — check for error indicator classes in the output.
        const parser = new DOMParser();
        const doc = parser.parseFromString(svg, "image/svg+xml");
        const hasError = doc.querySelector(".error-icon, .error-text") !== null;
        if (hasError) {
          setSvg("");
          setError("Diagram contains syntax errors");
        } else {
          setSvg(svg);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || "Failed to render diagram");
          setSvg("");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [code]);

  useEffect(() => {
    if (!svg || !containerRef.current) return;
    // Parse SVG string into DOM node — prevents XSS from AI-generated content
    const parser = new DOMParser();
    const doc = parser.parseFromString(svg, "image/svg+xml");
    const svgEl = doc.querySelector("svg");
    if (!svgEl) return;
    // Clear and append safely — no innerHTML involved
    containerRef.current.replaceChildren(svgEl);
  }, [svg]);

  if (error) {
    return (
      <pre className="my-3 overflow-x-auto rounded-lg border border-border-subtle bg-bg-elevated p-4 font-mono text-xs leading-relaxed text-text-secondary">
        {code}
      </pre>
    );
  }

  return (
    <div
      ref={containerRef}
      className="my-3 flex justify-center overflow-x-auto rounded-lg border border-border-subtle bg-bg-elevated p-4"
    />
  );
}
