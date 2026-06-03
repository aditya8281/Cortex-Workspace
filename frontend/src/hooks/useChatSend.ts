import { askQuestion } from "@/api/ai";
import type { ChatTurn } from "@/api/ai";
import { useAppStore } from "@/stores/appStore";
import { useChatStore } from "@/stores/chatStore";

export function useChatSend() {
  const token = useAppStore((s) => s.token);
  const modelConfig = useAppStore((s) => s.modelConfig);
  const apiKey = useAppStore((s) => s.apiKey);
  const apiBaseUrl = useAppStore((s) => s.apiBaseUrl);
  const setToast = useAppStore((s) => s.setToast);

  const activeSession = useChatStore((s) => s.getActiveSession());
  const appendMessages = useChatStore((s) => s.appendMessages);
  const setIsGenerating = useChatStore((s) => s.setIsGenerating);
  const buildTitleFromQuery = useChatStore((s) => s.buildTitleFromQuery);
  const updateSession = useChatStore((s) => s.updateSession);

  const send = async (query: string) => {
    if (!activeSession || !query.trim()) return;

    const userMessage = {
      id: `msg-${crypto.randomUUID()}`,
      sender: "user" as const,
      text: query.trim(),
      timestamp: new Date().toLocaleTimeString(),
    };

    const nextTitle =
      activeSession.title === "New chat" ? buildTitleFromQuery(query) : activeSession.title;

    const history: ChatTurn[] = activeSession.messages
      .filter((m) => m.id !== "welcome")
      .map((m) => ({ role: m.sender, content: m.text }));

    appendMessages(activeSession.id, [userMessage], nextTitle);
    setIsGenerating(true);

    try {
      const response = await askQuestion(query, Boolean(token), history, {
        ...modelConfig,
        api_key: apiKey,
        api_base_url: apiBaseUrl,
      });

      appendMessages(activeSession.id, [
        {
          id: `msg-${crypto.randomUUID()}`,
          sender: "assistant",
          text: response.response,
          executionId: response.execution_id,
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);

      useChatStore.getState().setContextItems([
        {
          id: "exec",
          kind: "activity",
          title: "Last execution",
          detail: response.execution_id ?? "completed",
        },
      ]);
    } catch {
      setToast("Assistant unreachable — check backend or model provider.");
      appendMessages(activeSession.id, [
        {
          id: `msg-${crypto.randomUUID()}`,
          sender: "assistant",
          text: "I hit a routing problem while processing that request.",
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } finally {
      setIsGenerating(false);
      updateSession(activeSession.id, { title: nextTitle });
    }
  };

  return { send, activeSession };
}
