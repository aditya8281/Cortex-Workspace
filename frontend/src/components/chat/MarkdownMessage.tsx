import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";

type Props = {
  content: string;
  className?: string;
};

export function MarkdownMessage({ content, className }: Props) {
  return (
    <div
      className={cn(
        "prose prose-invert max-w-none text-sm prose-p:my-2 prose-pre:my-3 prose-pre:rounded-lg prose-pre:border prose-pre:border-cortex-border prose-pre:bg-cortex-bg prose-code:rounded prose-code:bg-cortex-elevated prose-code:px-1 prose-code:py-0.5 prose-code:before:content-none prose-code:after:content-none",
        className,
      )}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}
