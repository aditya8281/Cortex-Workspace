import { askQuestion } from "@/api/ai";
import type { ChatTurn } from "@/api/ai";
import { useAppStore } from "@/stores/appStore";
import { useChatStore } from "@/stores/chatStore";
import { useContextStore } from "@/stores/contextStore";

export function useChatSend() {
  const token = useAppStore((s) => s.token);
  const modelConfig = useAppStore((s) => s.modelConfig);
  const apiKey = useAppStore((s) => s.apiKey);
  const apiBaseUrl = useAppStore((s) => s.apiBaseUrl);
  const setToast = useAppStore((s) => s.setToast);

  const activeSession = useChatStore((s) => s.getActiveSession());
  const appendMessages = useChatStore((s) => s.appendMessages);
  const updateMessage = useChatStore((s) => s.updateMessage);
  const setIsGenerating = useChatStore((s) => s.setIsGenerating);
  const buildTitleFromQuery = useChatStore((s) => s.buildTitleFromQuery);
  const updateSession = useChatStore((s) => s.updateSession);

  const send = async (query: string) => {
    if (!activeSession || !query.trim()) return;

    // Snapshot context items at send time
    const contextItems = useContextStore.getState().toPayload();

    const userMessage = {
      id: `msg-${crypto.randomUUID()}`,
      sender: "user" as const,
      text: query.trim(),
      timestamp: new Date().toLocaleTimeString(),
    };

    const nextTitle =
      activeSession.title === "New chat" ? buildTitleFromQuery(query) : activeSession.title;

    const assistantId = `msg-${crypto.randomUUID()}`;
    const stageMessages = [
      "Searching memory",
      "Reading files",
      "Thinking",
      "Drafting response",
    ];
    let stageIndex = 0;
    let stageTimer: number | null = null;

    const history: ChatTurn[] = activeSession.messages
      .filter((m) => m.id !== "welcome")
      .map((m) => ({ role: m.sender, content: m.text }));

    appendMessages(activeSession.id, [userMessage], nextTitle);
    setIsGenerating(true);
    appendMessages(activeSession.id, [
      {
        id: assistantId,
        sender: "assistant",
        text: stageMessages[0],
        state: "streaming",
        liveStage: stageMessages[0],
        timestamp: new Date().toLocaleTimeString(),
      },
    ]);

    stageTimer = window.setInterval(() => {
      stageIndex = Math.min(stageIndex + 1, stageMessages.length - 1);
      updateMessage(activeSession.id, assistantId, {
        text: stageMessages[stageIndex],
        liveStage: stageMessages[stageIndex],
      });
    }, 900);

    try {
      const configPayload = { ...modelConfig };
      if (activeSession.selectedModel) {
        configPayload.llm_model = activeSession.selectedModel;
      }
      const response = await askQuestion(
        query,
        Boolean(token),
        history,
        { ...configPayload, api_key: apiKey, api_base_url: apiBaseUrl },
        contextItems.length > 0 ? contextItems : undefined
      );

      updateMessage(activeSession.id, assistantId, {
        text: response.response,
        executionId: response.execution_id,
        routingInfo: response.routing_info,
        state: "done",
        liveStage: null,
        timestamp: new Date().toLocaleTimeString(),
      });

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
      updateMessage(activeSession.id, assistantId, {
        text: "I hit a routing problem while processing that request.",
        state: "done",
        liveStage: null,
        timestamp: new Date().toLocaleTimeString(),
      });
    } finally {
      if (stageTimer) window.clearInterval(stageTimer);
      setIsGenerating(false);
      updateSession(activeSession.id, { title: nextTitle });
    }
  };

  return { send, activeSession };
}
