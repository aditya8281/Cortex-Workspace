"use client";

import { useState } from "react";
import { cn } from "../../src/lib/utils";

interface SearchFiltersProps {
  repos: { id: number; repo_name: string }[];
  onFilterChange: (filters: {
    repo_id?: number;
    node_type?: string;
    language?: string;
    max_results: number;
  }) => void;
}

const NODE_TYPES = [
  { value: "", label: "All Types" },
  { value: "function", label: "Functions" },
  { value: "class", label: "Classes" },
  { value: "method", label: "Methods" },
  { value: "file", label: "Files" },
  { value: "code", label: "Code" },
];

const LANGUAGES = [
  { value: "", label: "All Languages" },
  { value: "python", label: "Python" },
  { value: "typescript", label: "TypeScript" },
  { value: "javascript", label: "JavaScript" },
  { value: "rust", label: "Rust" },
  { value: "go", label: "Go" },
  { value: "java", label: "Java" },
];

export default function SearchFilters({ repos, onFilterChange }: SearchFiltersProps) {
  const [repoId, setRepoId] = useState<number | undefined>(undefined);
  const [nodeType, setNodeType] = useState("");
  const [language, setLanguage] = useState("");
  const [maxResults, setMaxResults] = useState(10);

  function update(updates: Partial<typeof filters>) {
    const filters = { repo_id: repoId, node_type: nodeType || undefined, language: language || undefined, max_results: maxResults, ...updates };
    if ("repo_id" in updates) setRepoId(updates.repo_id);
    if ("node_type" in updates) setNodeType(updates.node_type || "");
    if ("language" in updates) setLanguage(updates.language || "");
    if ("max_results" in updates) setMaxResults(updates.max_results!);
    onFilterChange(filters);
  }

  const filters = { repo_id: repoId, node_type: nodeType || undefined, language: language || undefined, max_results: maxResults };

  return (
    <div className="flex flex-wrap gap-3 items-center">
      {/* Repository filter */}
      <select
        value={repoId ?? ""}
        onChange={(e) => update({ repo_id: e.target.value ? Number(e.target.value) : undefined })}
        className="rounded-xl bg-bg-surface border border-border-subtle px-3 py-2 text-sm text-text outline-none transition-all duration-200 focus:border-accent/40 focus:ring-2 focus:ring-accent/10"
      >
        <option value="">All Repos</option>
        {repos.map((repo) => (
          <option key={repo.id} value={repo.id}>
            {repo.repo_name}
          </option>
        ))}
      </select>

      {/* Node type filter */}
      <select
        value={nodeType}
        onChange={(e) => update({ node_type: e.target.value })}
        className="rounded-xl bg-bg-surface border border-border-subtle px-3 py-2 text-sm text-text outline-none transition-all duration-200 focus:border-accent/40 focus:ring-2 focus:ring-accent/10"
      >
        {NODE_TYPES.map((t) => (
          <option key={t.value} value={t.value}>
            {t.label}
          </option>
        ))}
      </select>

      {/* Language filter */}
      <select
        value={language}
        onChange={(e) => update({ language: e.target.value })}
        className="rounded-xl bg-bg-surface border border-border-subtle px-3 py-2 text-sm text-text outline-none transition-all duration-200 focus:border-accent/40 focus:ring-2 focus:ring-accent/10"
      >
        {LANGUAGES.map((l) => (
          <option key={l.value} value={l.value}>
            {l.label}
          </option>
        ))}
      </select>

      {/* Max results */}
      <select
        value={maxResults}
        onChange={(e) => update({ max_results: Number(e.target.value) })}
        className="rounded-xl bg-bg-surface border border-border-subtle px-3 py-2 text-sm text-text outline-none transition-all duration-200 focus:border-accent/40 focus:ring-2 focus:ring-accent/10"
      >
        <option value={5}>5 results</option>
        <option value={10}>10 results</option>
        <option value={25}>25 results</option>
        <option value={50}>50 results</option>
      </select>
    </div>
  );
}
