"use client";

import { useState } from "react";

interface CodeBlockProps {
  language?: string;
  children: string;
}

export function CodeBlock({ language, children }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="group relative my-3 rounded-lg border border-border-subtle bg-bg-surface overflow-hidden">
      <div className="flex items-center justify-between px-3 py-1.5 bg-bg-elevated border-b border-border-subtle">
        {language ? (
          <span className="text-[10px] text-text-muted uppercase tracking-wide">{language}</span>
        ) : <span />}
        <button
          onClick={handleCopy}
          className="text-[10px] text-text-muted hover:text-text-secondary opacity-0 group-hover:opacity-100 motion-safe:transition-opacity motion-safe:duration-150 cursor-pointer"
          aria-label="Copy code"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <pre className="p-3 overflow-x-auto text-xs leading-relaxed">
        <code className="text-text-secondary font-mono">{children}</code>
      </pre>
    </div>
  );
}
