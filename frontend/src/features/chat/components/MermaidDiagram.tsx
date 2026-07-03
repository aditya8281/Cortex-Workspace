"use client";

import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";

// Initialize once with dark theme matching Cortex palette.
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
  // securityLevel: "loose" means mermaid returns error SVGs on syntax
  // errors instead of throwing. We detect them post-render.
  securityLevel: "loose",
});

interface MermaidDiagramProps {
  code: string;
}

/** Regex patterns that indicate an SVG is a Mermaid error indicator. */
const ERROR_SVG_PATTERNS = [
  /class\s*=\s*"error/,
  /class\s*=\s*"flowchart-error/,
  /\.error-icon/,
  /\.error-text/,
  /mermaid-error/,
  /diagram-error/,
  /syntax error/i,
  />error</i,
  // Mermaid v11 error SVG metadata
  /data-name\s*=\s*"error/,
  /flowchart-label\s+error/,
];

/** Check if an SVG string looks like a Mermaid error indicator. */
function isErrorSvg(svg: string): boolean {
  return ERROR_SVG_PATTERNS.some((re) => re.test(svg));
}

export function MermaidDiagram({ code }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const id = `mermaid-${Math.random().toString(36).slice(2, 9)}`;

    // Skip rendering during streaming — partial diagram syntax always errors
    if (!code.trim()) {
      setError("Empty diagram definition");
      setSvg("");
      return;
    }

    mermaid
      .render(id, code.trim())
      .then(({ svg: result }) => {
        if (cancelled) return;
        // Mermaid sometimes returns error SVGs instead of throwing —
        // check for error indicator patterns in the SVG text.
        if (isErrorSvg(result)) {
          setSvg("");
          setError("Diagram contains syntax errors");
        } else {
          setSvg(result);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err?.message || "Failed to render diagram");
          setSvg("");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [code]);

  // Inject rendered SVG (safe — parsed, not innerHTML)
  useEffect(() => {
    if (!svg || !containerRef.current) return;
    const parser = new DOMParser();
    const doc = parser.parseFromString(svg, "image/svg+xml");
    const svgEl = doc.querySelector("svg");
    if (!svgEl) return;
    // Double-check the parsed element isn't an error SVG
    if (isErrorSvg(svgEl.outerHTML)) {
      setSvg("");
      setError("Diagram contains syntax errors");
      return;
    }
    containerRef.current.replaceChildren(svgEl);
  }, [svg]);

  // On error, show raw code in a pre block
  if (error) {
    return (
      <pre className="my-3 overflow-x-auto rounded-lg border border-border-subtle bg-bg-elevated p-4 font-mono text-xs leading-relaxed text-text-secondary whitespace-pre-wrap">
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
