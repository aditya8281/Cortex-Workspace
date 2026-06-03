import { useEffect, useState } from "react";
import { MarkdownMessage } from "./MarkdownMessage";

type Props = {
  text: string;
  animate?: boolean;
  className?: string;
};

/** Reveals assistant text progressively for a streaming feel. */
export function StreamingText({ text, animate = true, className }: Props) {
  const [visible, setVisible] = useState(animate ? "" : text);

  useEffect(() => {
    if (!animate) {
      setVisible(text);
      return;
    }
    setVisible("");
    let index = 0;
    const step = Math.max(2, Math.floor(text.length / 80));
    const id = window.setInterval(() => {
      index = Math.min(text.length, index + step);
      setVisible(text.slice(0, index));
      if (index >= text.length) window.clearInterval(id);
    }, 16);
    return () => window.clearInterval(id);
  }, [text, animate]);

  return <MarkdownMessage content={visible || " "} className={className} />;
}
