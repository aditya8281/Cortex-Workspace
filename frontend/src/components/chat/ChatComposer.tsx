import { useState, type FormEvent, type KeyboardEvent } from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useChatStore } from "@/stores/chatStore";
import { useChatSend } from "@/hooks/useChatSend";

export function ChatComposer() {
  const inputQuery = useChatStore((s) => s.inputQuery);
  const setInputQuery = useChatStore((s) => s.setInputQuery);
  const isGenerating = useChatStore((s) => s.isGenerating);
  const { send } = useChatSend();
  const [local, setLocal] = useState(inputQuery);

  const submit = async (text?: string) => {
    const q = (text ?? local).trim();
    if (!q || isGenerating) return;
    setLocal("");
    setInputQuery("");
    await send(q);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void submit();
    }
  };

  return (
    <form
      className="border-t border-cortex-border bg-cortex-surface/90 p-4 backdrop-blur-md"
      onSubmit={(e: FormEvent) => {
        e.preventDefault();
        void submit();
      }}
    >
      <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-xl border border-cortex-border bg-cortex-elevated p-2 shadow-sm">
        <textarea
          value={local}
          onChange={(e) => setLocal(e.target.value)}
          onKeyDown={onKeyDown}
          rows={1}
          placeholder="Ask Cortex about your machine, repos, or memory…"
          className="max-h-40 min-h-[44px] flex-1 resize-none bg-transparent px-2 py-2.5 text-sm text-cortex-text placeholder:text-cortex-muted focus:outline-none"
        />
        <Button type="submit" size="icon" disabled={isGenerating || !local.trim()} aria-label="Send">
          <Send className="h-4 w-4" />
        </Button>
      </div>
      <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-cortex-muted">
        Cortex reads your environment automatically. Modifications require approval.
      </p>
    </form>
  );
}
