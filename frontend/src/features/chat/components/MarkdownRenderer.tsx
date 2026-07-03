"use client";

import { useMemo } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { CodeBlock } from "./CodeBlock";
import { MermaidDiagram } from "./MermaidDiagram";

interface MarkdownRendererProps {
  content: string;
}

/**
 * Full-featured markdown renderer for assistant responses.
 * Handles GFM (tables, strikethrough, task lists), syntax highlighting,
 * mermaid diagrams, and inline code.
 */
export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <div className="markdown-body space-y-3">
      <Markdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          // Code blocks: detect mermaid, otherwise syntax-highlighted code
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            const lang = match?.[1] ?? "";
            const text = String(children).replace(/\n$/, "");

            // Mermaid diagram
            if (lang === "mermaid") {
              return <MermaidDiagram code={text} />;
            }

            // Inline code (single backtick, no language)
            if (!className && !text.includes("\n")) {
              return (
                <code
                  className="rounded-md bg-bg-surface px-1.5 py-0.5 text-[13px] font-mono text-accent-cyan/90 border border-border-subtle"
                  {...props}
                >
                  {children}
                </code>
              );
            }

            // Fenced code block with language
            return <CodeBlock language={lang}>{text}</CodeBlock>;
          },

          // Tables — styled for dark theme
          table({ children }) {
            return (
              <div className="my-3 overflow-x-auto rounded-lg border border-border-subtle">
                <table className="w-full text-sm">{children}</table>
              </div>
            );
          },
          thead({ children }) {
            return <thead className="bg-bg-elevated border-b border-border-subtle">{children}</thead>;
          },
          th({ children }) {
            return <th className="px-3 py-2 text-left text-xs font-medium text-text-secondary">{children}</th>;
          },
          td({ children }) {
            return <td className="px-3 py-2 text-text-primary border-t border-border-subtle">{children}</td>;
          },

          // Headings — tight hierarchy
          h1({ children }) {
            return <h1 className="text-lg font-semibold text-text-primary tracking-tight mt-4 mb-2">{children}</h1>;
          },
          h2({ children }) {
            return <h2 className="text-base font-semibold text-text-primary tracking-tight mt-4 mb-2">{children}</h2>;
          },
          h3({ children }) {
            return <h3 className="text-sm font-semibold text-text-secondary mt-3 mb-1">{children}</h3>;
          },

          // Paragraphs — relaxed leading
          p({ children }) {
            return <p className="text-sm text-text-primary leading-relaxed">{children}</p>;
          },

          // Lists
          ul({ children }) {
            return <ul className="list-disc list-inside text-sm text-text-primary leading-relaxed space-y-0.5 marker:text-text-muted">{children}</ul>;
          },
          ol({ children }) {
            return <ol className="list-decimal list-inside text-sm text-text-primary leading-relaxed space-y-0.5 marker:text-text-muted">{children}</ol>;
          },
          li({ children }) {
            return <li className="pl-1">{children}</li>;
          },

          // Blockquotes
          blockquote({ children }) {
            return (
              <blockquote className="my-2 border-l-2 border-l-accent-cyan/30 pl-3 text-sm text-text-secondary italic">
                {children}
              </blockquote>
            );
          },

          // Horizontal rules
          hr() {
            return <hr className="my-4 border-t border-border-subtle" />;
          },

          // Links — accent colored
          a({ href, children }) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent-cyan/80 hover:text-accent-cyan underline underline-offset-2 decoration-accent-cyan/30 hover:decoration-accent-cyan/60 motion-safe:transition-colors motion-safe:duration-150"
              >
                {children}
              </a>
            );
          },

          // Strong / emphasis
          strong({ children }) {
            return <strong className="font-semibold text-text-primary">{children}</strong>;
          },
          em({ children }) {
            return <em className="italic text-text-secondary">{children}</em>;
          },

          // Task lists (GFM)
          input({ checked, ...props }) {
            return (
              <input
                type="checkbox"
                checked={checked}
                readOnly
                className="mr-1.5 accent-accent-cyan align-middle"
                {...props}
              />
            );
          },
        }}
      >
        {content}
      </Markdown>
    </div>
  );
}
