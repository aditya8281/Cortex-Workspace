import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";
import { cn } from "@/lib/utils";
import { CodeBlock } from "./CodeBlock";

type Props = {
  content: string;
  className?: string;
};

const components: Components = {
  code({ className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || "");
    const code = String(children).replace(/\n$/, "");
    const isBlock = match || code.includes("\n");

    if (isBlock) {
      return <CodeBlock code={code} language={match?.[1]} />;
    }

    return (
      <code
        className="rounded bg-cortex-elevated px-1 py-0.5 font-mono text-[0.85em] text-cortex-accent"
        {...props}
      >
        {children}
      </code>
    );
  },
  pre({ children }) {
    return <>{children}</>;
  },
};

export function MarkdownMessage({ content, className }: Props) {
  return (
    <div
      className={cn(
        "markdown-body prose prose-invert max-w-none text-sm prose-p:my-2 prose-headings:text-cortex-text prose-a:text-cortex-accent prose-table:text-sm",
        className,
      )}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
