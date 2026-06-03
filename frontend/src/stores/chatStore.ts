import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ChatMessage, ChatSession, ContextItem } from "@/types/cortex";

function buildSessionTitle(query: string) {
  const compact = query.replace(/\s+/g, " ").trim();
  if (compact.length <= 34) return compact;
  return `${compact.slice(0, 31).trim()}...`;
}

export function createFreshSession(title = "New chat") {
  return {
    id: `session-${crypto.randomUUID()}`,
    title,
    messages: [
      {
        id: "welcome",
        sender: "assistant" as const,
        text: "Cortex is online. I understand your machine, repositories, and memory. What should we work on?",
        timestamp: new Date().toLocaleTimeString(),
      },
    ],
    createdAt: new Date().toISOString(),
    pinned: false,
    archived: false,
  } satisfies ChatSession;
}

type ChatState = {
  sessions: ChatSession[];
  activeSessionId: string | null;
  inputQuery: string;
  isGenerating: boolean;
  contextItems: ContextItem[];
  renamingId: string | null;
  renameValue: string;
  initSessions: () => void;
  setActiveSession: (id: string) => void;
  newSession: () => void;
  setInputQuery: (q: string) => void;
  setIsGenerating: (v: boolean) => void;
  setContextItems: (items: ContextItem[]) => void;
  appendMessages: (sessionId: string, messages: ChatMessage[], title?: string) => void;
  updateSession: (sessionId: string, patch: Partial<ChatSession>) => void;
  deleteSession: (sessionId: string) => void;
  pinSession: (sessionId: string, pinned: boolean) => void;
  archiveSession: (sessionId: string, archived: boolean) => void;
  setRenaming: (id: string | null, value?: string) => void;
  commitRename: (sessionId: string) => void;
  getActiveSession: () => ChatSession | null;
  buildTitleFromQuery: (query: string) => string;
};

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      sessions: [],
      activeSessionId: null,
      inputQuery: "",
      isGenerating: false,
      contextItems: [],
      renamingId: null,
      renameValue: "",

      initSessions: () => {
        const { sessions } = get();
        if (sessions.length === 0) {
          const session = createFreshSession();
          set({ sessions: [session], activeSessionId: session.id });
        } else if (!get().activeSessionId) {
          set({ activeSessionId: sessions[0].id });
        }
      },

      setActiveSession: (id) => set({ activeSessionId: id }),
      newSession: () => {
        const session = createFreshSession();
        set((s) => ({
          sessions: [session, ...s.sessions],
          activeSessionId: session.id,
        }));
      },
      setInputQuery: (inputQuery) => set({ inputQuery }),
      setIsGenerating: (isGenerating) => set({ isGenerating }),
      setContextItems: (contextItems) => set({ contextItems }),

      appendMessages: (sessionId, messages, title) => {
        set((s) => ({
          sessions: s.sessions.map((session) =>
            session.id === sessionId
              ? {
                  ...session,
                  title: title ?? session.title,
                  messages: [...session.messages, ...messages],
                }
              : session,
          ),
        }));
      },

      updateSession: (sessionId, patch) =>
        set((s) => ({
          sessions: s.sessions.map((session) =>
            session.id === sessionId ? { ...session, ...patch } : session,
          ),
        })),

      deleteSession: (sessionId) => {
        set((s) => {
          const sessions = s.sessions.filter((x) => x.id !== sessionId);
          const activeSessionId =
            s.activeSessionId === sessionId ? sessions[0]?.id ?? null : s.activeSessionId;
          return { sessions: sessions.length ? sessions : [createFreshSession()], activeSessionId };
        });
      },

      pinSession: (sessionId, pinned) =>
        get().updateSession(sessionId, { pinned }),

      archiveSession: (sessionId, archived) =>
        get().updateSession(sessionId, { archived }),

      setRenaming: (renamingId, renameValue = "") => set({ renamingId, renameValue }),

      commitRename: (sessionId) => {
        const value = get().renameValue.trim();
        if (value) get().updateSession(sessionId, { title: value });
        set({ renamingId: null, renameValue: "" });
      },

      getActiveSession: () => {
        const { sessions, activeSessionId } = get();
        return sessions.find((s) => s.id === activeSessionId) ?? null;
      },

      buildTitleFromQuery: buildSessionTitle,
    }),
    {
      name: "cortex-chats",
      partialize: (s) => ({ sessions: s.sessions, activeSessionId: s.activeSessionId }),
    },
  ),
);
