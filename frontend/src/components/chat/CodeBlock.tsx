import { useEffect, useState } from "react";
import { bundledLanguages, codeToHtml } from "shiki";

type Props = {
  code: string;
  language?: string;
};

export function CodeBlock({ code, language = "text" }: Props) {
  const [html, setHtml] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const lang = language in bundledLanguages ? language : "text";

    void codeToHtml(code, {
      lang,
      theme: "github-dark-default",
    })
      .then((result) => {
        if (!cancelled) setHtml(result);
      })
      .catch(() => {
        if (!cancelled) {
          setHtml(`<pre class="shiki-fallback"><code>${escapeHtml(code)}</code></pre>`);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [code, language]);

  if (!html) {
    return (
      <pre className="overflow-x-auto rounded-lg border border-cortex-border bg-[#0d1117] p-3 text-xs font-mono text-cortex-text">
        <code>{code}</code>
      </pre>
    );
  }

  return (
    <div
      className="code-block overflow-x-auto rounded-lg border border-cortex-border text-xs [&_pre]:!m-0 [&_pre]:!bg-[#0d1117] [&_pre]:!p-3"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

function escapeHtml(text: string) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
