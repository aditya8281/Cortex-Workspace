"use client";

import React, { Component, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

interface Props {
  content: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class MarkdownErrorBoundary extends Component<
  { children: ReactNode; fallback?: ReactNode },
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <div className="rounded-lg border border-error/20 bg-error/5 p-4 text-sm text-error">
            Failed to render markdown. Please check the content and try again.
          </div>
        )
      );
    }
    return this.props.children;
  }
}

export function MarkdownRenderer({ content }: Props) {
  return (
    <MarkdownErrorBoundary>
      <ReactMarkdown
        components={{
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            const code = String(children).replace(/\n$/, "");
            if (match) {
              return (
                <SyntaxHighlighter
                  style={oneDark}
                  language={match[1]}
                  PreTag="div"
                  className="rounded-md my-2"
                >
                  {code}
                </SyntaxHighlighter>
              );
            }
            return (
              <code className="bg-muted px-1.5 py-0.5 rounded text-sm" {...props}>
                {children}
              </code>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </MarkdownErrorBoundary>
  );
}
