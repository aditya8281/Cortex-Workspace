import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AppUser, ModelConfig } from "@/types/cortex";

const MODEL_DEFAULTS: ModelConfig = {
  llm_model: "qwen3:8b",
  embedding_model: "BAAI/bge-small-en-v1.5",
  vector_db: "FAISS",
  inference_engine: "Ollama",
  code_parsing: "Tree-sitter",
};

type AppState = {
  token: string | null;
  currentUser: AppUser | null;
  modelConfig: ModelConfig;
  apiBaseUrl: string;
  apiKey: string;
  sidebarCollapsed: boolean;
  contextPanelOpen: boolean;
  mobileSidebarOpen: boolean;
  theme: "dark" | "light";
  toast: string | null;
  setToken: (token: string | null) => void;
  setCurrentUser: (user: AppUser | null) => void;
  setModelConfig: (config: Partial<ModelConfig>) => void;
  setApiBaseUrl: (url: string) => void;
  setApiKey: (key: string) => void;
  setSidebarCollapsed: (v: boolean) => void;
  setContextPanelOpen: (v: boolean) => void;
  setMobileSidebarOpen: (v: boolean) => void;
  setTheme: (theme: "dark" | "light") => void;
  setToast: (msg: string | null) => void;
};

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      token: localStorage.getItem("cortex_token"),
      currentUser: null,
      modelConfig: MODEL_DEFAULTS,
      apiBaseUrl: "",
      apiKey: "",
      sidebarCollapsed: false,
      contextPanelOpen: true,
      mobileSidebarOpen: false,
      theme: "dark",
      toast: null,
      setToken: (token) => {
        if (token) localStorage.setItem("cortex_token", token);
        else localStorage.removeItem("cortex_token");
        set({ token });
      },
      setCurrentUser: (currentUser) => set({ currentUser }),
      setModelConfig: (partial) =>
        set((s) => ({ modelConfig: { ...s.modelConfig, ...partial } })),
      setApiBaseUrl: (apiBaseUrl) => set({ apiBaseUrl }),
      setApiKey: (apiKey) => set({ apiKey }),
      setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
      setContextPanelOpen: (contextPanelOpen) => set({ contextPanelOpen }),
      setMobileSidebarOpen: (mobileSidebarOpen) => set({ mobileSidebarOpen }),
      setTheme: (theme) => set({ theme }),
      setToast: (toast) => set({ toast }),
    }),
    {
      name: "cortex-app",
      partialize: (s) => ({
        modelConfig: s.modelConfig,
        sidebarCollapsed: s.sidebarCollapsed,
        contextPanelOpen: s.contextPanelOpen,
        theme: s.theme,
      }),
    },
  ),
);
