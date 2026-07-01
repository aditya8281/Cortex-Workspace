"use client";

import { useState } from "react";
import { CodeIcon } from "@/shared/ui/icons";

type TabKey = "github" | "lsp" | "skills" | "mcp";

const TABS: { key: TabKey; label: string; status: "live" | "soon" }[] = [
  { key: "github", label: "GitHub", status: "live" },
  { key: "lsp", label: "LSP", status: "soon" },
  { key: "skills", label: "Skills", status: "soon" },
  { key: "mcp", label: "MCP", status: "soon" },
];

export default function CodePage() {
  const [activeTab, setActiveTab] = useState<TabKey>("github");

  return (
    <div className="flex h-full flex-col">
      {/* Tabs */}
      <div className="flex gap-1 border-b border-border-subtle px-4">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`relative px-3 py-2.5 text-xs font-medium motion-safe:transition-colors motion-safe:duration-150 ${
              activeTab === t.key
                ? "text-text-primary after:absolute after:bottom-0 after:left-2 after:right-2 after:h-0.5 after:rounded-full after:bg-accent-red"
                : "text-text-muted hover:text-text-secondary"
            }`}
          >
            {t.label}
            {t.status === "soon" && (
              <span className="ml-1.5 rounded-full bg-accent-cyan/10 px-1.5 py-0.5 text-[10px] text-accent-cyan">v1.12</span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === "github" && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-text-muted mb-4">
              <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
            </svg>
            <p className="text-sm text-text-muted">Connect a GitHub account in Settings to browse repos and PRs</p>
          </div>
        )}

        {activeTab === "lsp" && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <CodeIcon className="text-text-muted" size={32} />
            <p className="mt-3 text-sm font-medium text-text-primary">LSP Integration</p>
            <p className="mt-1 text-sm text-text-muted">Language server protocol support coming in v1.12</p>
          </div>
        )}

        {activeTab === "skills" && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <CodeIcon className="text-text-muted" size={32} />
            <p className="mt-3 text-sm font-medium text-text-primary">Skills Manager</p>
            <p className="mt-1 text-sm text-text-muted">Skill development and management toolkit coming in v1.12</p>
          </div>
        )}

        {activeTab === "mcp" && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <CodeIcon className="text-text-muted" size={32} />
            <p className="mt-3 text-sm font-medium text-text-primary">MCP Servers</p>
            <p className="mt-1 text-sm text-text-muted">MCP server management coming in v1.12</p>
          </div>
        )}
      </div>
    </div>
  );
}
