import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent, type KeyboardEvent, type ReactNode } from "react";
import "./App.css";
import {
  askQuestion,
  deleteModel,
  getChatHistory,
  getInstalledModels,
  getUserSettings,
  pullModel,
  updateUserSettings,
  type AskResponse,
  type ChatTurn,
  type InstalledModel,
  type ModelConfig,
} from "./api/ai";
import {
  deleteUser,
  getMe,
  getUsers,
  login,
  logout,
  register,
  updateUser,
} from "./api/auth";
import { getExecutionReplay, listExecutions } from "./api/execution";

type AppUser = {
  id: number;
  email: string;
  full_name: string;
  role: string;
};

type ChatMessage = {
  id: string;
  sender: "user" | "assistant";
  text: string;
  executionId?: string | null;
  timestamp: string;
};

type ChatSession = {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
};

type ExecutionSummary = {
  total_events?: number;
  steps_executed?: number;
  tools_used?: string[];
  error_count?: number;
  started_at?: string | null;
  completed_at?: string | null;
  duration_ms?: number | null;
};

type ExecutionListItem = {
  execution_id: string;
  status: string;
  summary: ExecutionSummary;
  last_timestamp?: string | null;
  event_count?: number;
};

type ReplayStep = {
  step: number;
  action: string;
  raw: {
    type?: string;
    timestamp?: string;
    source?: string;
    payload?: Record<string, unknown>;
    human_readable?: string;
  };
};

type ReplayData = {
  execution_id: string;
  status: string;
  summary: ExecutionSummary;
  replay: ReplayStep[];
};

type PanelTab = "traces" | "models" | "admin";
type AuthMode = "login" | "register" | "none";
type ProviderKey = "openai" | "nvidia" | "groq" | "openrouter" | "custom";

type ProviderConfig = {
  name: string;
  defaultUrl: string;
  models: string[];
};

const QUICK_ACTIONS = [
  {
    icon: "◫",
    title: "Find code paths",
    description: "Locate services, endpoints, and implementation details in the workspace.",
    prompt: "find the implementation for GraphRunner and explain the execution flow",
  },
  {
    icon: "◌",
    title: "Audit the system",
    description: "Inspect the current environment, running services, and obvious mismatches.",
    prompt: "scan the project for bugs, mismatches, and production risks",
  },
  {
    icon: "◈",
    title: "Trace execution",
    description: "Open the latest replay and see how the assistant routed the request.",
    prompt: "show me the latest execution trace and explain the important steps",
  },
  {
    icon: "◉",
    title: "Plan next build",
    description: "Use the assistant to outline the next product or architecture step.",
    prompt: "help me plan the next production-grade improvement for this workspace",
  },
];

const PROVIDERS: Record<ProviderKey, ProviderConfig> = {
  openai: {
    name: "OpenAI",
    defaultUrl: "https://api.openai.com/v1",
    models: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
  },
  nvidia: {
    name: "NVIDIA NIM",
    defaultUrl: "https://integrate.api.nvidia.com/v1",
    models: [
      "meta/llama3-70b-instruct",
      "meta/llama3-8b-instruct",
      "nvidia/nemotron-4-340b-instruct",
      "mistralai/mixtral-8x22b-instruct-v0.1",
    ],
  },
  groq: {
    name: "Groq",
    defaultUrl: "https://api.groq.com/openai/v1",
    models: ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768", "gemma-7b-it"],
  },
  openrouter: {
    name: "OpenRouter",
    defaultUrl: "https://openrouter.ai/api/v1",
    models: [
      "meta-llama/llama-3-70b-instruct",
      "mistralai/mixtral-8x22b-instruct",
      "anthropic/claude-3.5-sonnet",
      "google/gemini-flash-1.5",
    ],
  },
  custom: {
    name: "Custom",
    defaultUrl: "",
    models: [],
  },
};

const CURATED_MODELS = [
  { id: "qwen3:8b", name: "Qwen3 8B" },
  { id: "llama3", name: "Llama 3 8B" },
  { id: "mistral", name: "Mistral 7B" },
  { id: "codellama", name: "CodeLlama 7B" },
  { id: "gemma2", name: "Gemma 2 9B" },
  { id: "phi3", name: "Phi-3 Mini" },
];

const MODEL_DEFAULTS: ModelConfig = {
  llm_model: "qwen3:8b",
  embedding_model: "BAAI/bge-small-en-v1.5",
  vector_db: "FAISS",
  inference_engine: "Ollama",
  code_parsing: "Tree-sitter",
};

function pad(value: number) {
  return value.toString().padStart(2, "0");
}

function formatTimestamp(value?: string | null) {
  if (!value) return "unknown";
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

function formatDuration(value?: number | null) {
  if (value == null) return "0.00s";
  return `${(value / 1000).toFixed(2)}s`;
}

function buildSessionTitle(query: string) {
  const compact = query.replace(/\s+/g, " ").trim();
  if (compact.length <= 34) return compact;
  return `${compact.slice(0, 31).trim()}...`;
}

function createFreshSession(title = "New Session", welcome = "Ready when you are. Ask for code, docs, traces, or system checks.") {
  return {
    id: `session-${crypto.randomUUID()}`,
    title,
    messages: [
      {
        id: "welcome",
        sender: "assistant",
        text: welcome,
        timestamp: new Date().toLocaleTimeString(),
      },
    ],
    createdAt: new Date().toISOString(),
  } satisfies ChatSession;
}

function parseResponseText(text: string) {
  if (!text) return { finalResponse: "", memoryText: "", toolText: "" };

  const memoryRegex = /(?:^|\r?\n)Memory\s+Context:\s*\r?\n/i;
  const toolRegex = /(?:^|\r?\n)Tool\s+Results:\s*\r?\n/i;
  const finalRegex = /(?:^|\r?\n)Final\s+Response:\s*\r?\n/i;

  const memoryMatch = text.match(memoryRegex);
  const toolMatch = text.match(toolRegex);
  const finalMatch = text.match(finalRegex);

  const sections: { type: "memory" | "tool" | "final"; start: number; headerLength: number }[] = [];

  if (memoryMatch?.index != null) {
    sections.push({ type: "memory", start: memoryMatch.index, headerLength: memoryMatch[0].length });
  }
  if (toolMatch?.index != null) {
    sections.push({ type: "tool", start: toolMatch.index, headerLength: toolMatch[0].length });
  }
  if (finalMatch?.index != null) {
    sections.push({ type: "final", start: finalMatch.index, headerLength: finalMatch[0].length });
  }

  sections.sort((a, b) => a.start - b.start);

  let memoryText = "";
  let toolText = "";
  let finalResponse = "";
  const preText = sections.length > 0 ? text.slice(0, sections[0].start).trim() : text.trim();

  sections.forEach((section, index) => {
    const nextStart = index + 1 < sections.length ? sections[index + 1].start : text.length;
    const content = text.slice(section.start + section.headerLength, nextStart).trim();

    if (section.type === "memory") memoryText = content;
    if (section.type === "tool") toolText = content;
    if (section.type === "final") finalResponse = content;
  });

  if (!finalResponse) {
    finalResponse = preText || memoryText || toolText || text;
  } else if (preText) {
    finalResponse = `${preText}\n\n${finalResponse}`;
  }

  return { finalResponse, memoryText, toolText };
}

function Markdown({ text }: { text: string }) {
  const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g;
  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  const renderInline = (line: string) => {
    const chunks: ReactNode[] = [];
    const inlineRegex = /(\*\*|`)(.*?)\1/g;
    let cursor = 0;
    let inlineMatch: RegExpExecArray | null;
    let keyIndex = 0;

    while ((inlineMatch = inlineRegex.exec(line)) !== null) {
      if (inlineMatch.index > cursor) {
        chunks.push(line.slice(cursor, inlineMatch.index));
      }

      const [token, content] = inlineMatch;
      if (token.startsWith("**")) {
        chunks.push(
          <strong key={`bold-${keyIndex++}`} className="md-strong">
            {content}
          </strong>,
        );
      } else {
        chunks.push(
          <code key={`code-${keyIndex++}`} className="md-code">
            {content}
          </code>,
        );
      }

      cursor = inlineRegex.lastIndex;
    }

    if (cursor < line.length) {
      chunks.push(line.slice(cursor));
    }

    return chunks.length > 0 ? chunks : line;
  };

  const renderTextBlock = (block: string, blockKey: string) =>
    block.split("\n").map((line, lineIndex) => {
      const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
      if (headingMatch) {
        const headingText = renderInline(headingMatch[2]);
        switch (headingMatch[1].length) {
          case 1:
            return (
              <h1 key={`${blockKey}-h1-${lineIndex}`} className="md-h1">
                {headingText}
              </h1>
            );
          case 2:
            return (
              <h2 key={`${blockKey}-h2-${lineIndex}`} className="md-h2">
                {headingText}
              </h2>
            );
          case 3:
            return (
              <h3 key={`${blockKey}-h3-${lineIndex}`} className="md-h3">
                {headingText}
              </h3>
            );
          default:
            return (
              <h4 key={`${blockKey}-h4-${lineIndex}`} className="md-h4">
                {headingText}
              </h4>
            );
        }
      }

      const listMatch = line.match(/^(\s*)([-*]|\d+\.)\s+(.*)$/);
      if (listMatch) {
        const listText = renderInline(listMatch[3]);
        if (/^\d+\./.test(listMatch[2])) {
          return (
            <ol key={`${blockKey}-ol-${lineIndex}`} className="md-ol">
              <li>{listText}</li>
            </ol>
          );
        }
        return (
          <ul key={`${blockKey}-ul-${lineIndex}`} className="md-ul">
            <li>{listText}</li>
          </ul>
        );
      }

      if (line.trim() === "") {
        return <div key={`${blockKey}-br-${lineIndex}`} className="md-br" />;
      }

      return (
        <p key={`${blockKey}-p-${lineIndex}`} className="md-p">
          {renderInline(line)}
        </p>
      );
    });

  while ((match = codeBlockRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      const textPart = text.slice(lastIndex, match.index);
      parts.push(
        <div key={`text-${lastIndex}`} className="md-text-block">
          {renderTextBlock(textPart, `block-${lastIndex}`)}
        </div>,
      );
    }

    const language = match[1] || "text";
    const code = match[2];
    const copyCode = async () => {
      await navigator.clipboard.writeText(code);
    };

    parts.push(
      <div key={`code-${lastIndex}`} className="md-code-block-container">
        <div className="md-code-block-header">
          <span className="md-code-block-lang">{language}</span>
          <button type="button" className="md-code-copy-btn" onClick={copyCode}>
            Copy
          </button>
        </div>
        <pre className="md-code-block">
          <code>{code}</code>
        </pre>
      </div>,
    );

    lastIndex = codeBlockRegex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(
      <div key={`text-tail-${lastIndex}`} className="md-text-block">
        {renderTextBlock(text.slice(lastIndex), `tail-${lastIndex}`)}
      </div>,
    );
  }

  return <div className="md-container">{parts}</div>;
}

function MessageBody({ text }: { text: string }) {
  const { finalResponse, memoryText, toolText } = parseResponseText(text);

  return (
    <div className="message-body">
      <div className="message-copy">
        <Markdown text={finalResponse} />
      </div>

      {(toolText || memoryText) && (
        <div className="message-diagnostics">
          {toolText && (
            <details className="diagnostic-card">
              <summary>Tool outputs</summary>
              <pre>{toolText}</pre>
            </details>
          )}
          {memoryText && (
            <details className="diagnostic-card">
              <summary>Memory recall</summary>
              <pre>{memoryText}</pre>
            </details>
          )}
        </div>
      )}
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  return <span className={`status-pill status-${status.toLowerCase()}`}>{status}</span>;
}

function App() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("cortex_token"));
  const [currentUser, setCurrentUser] = useState<AppUser | null>(null);
  const [authMode, setAuthMode] = useState<AuthMode>("none");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authFullName, setAuthFullName] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [panelTab, setPanelTab] = useState<PanelTab>("traces");
  const [inputQuery, setInputQuery] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState("");
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");

  const [modelConfig, setModelConfig] = useState<ModelConfig>(() => {
    try {
      const saved = localStorage.getItem("cortex_model_config");
      if (saved) return { ...MODEL_DEFAULTS, ...JSON.parse(saved) };
    } catch {
      // fall through to defaults
    }
    return MODEL_DEFAULTS;
  });

  const [apiBaseUrl, setApiBaseUrl] = useState(() => sessionStorage.getItem("cortex_api_base_url") || "");
  const [apiKey, setApiKey] = useState(() => sessionStorage.getItem("cortex_api_key") || "");
  const [showApiKey, setShowApiKey] = useState(false);
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [settingsSavedMessage, setSettingsSavedMessage] = useState<string | null>(null);

  const [installedModels, setInstalledModels] = useState<InstalledModel[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [pullingModelName, setPullingModelName] = useState<string | null>(null);
  const [pullProgress, setPullProgress] = useState<{ status: string; percent: number } | null>(null);
  const [missingModel, setMissingModel] = useState<string | null>(null);

  const [executions, setExecutions] = useState<ExecutionListItem[]>([]);
  const [selectedExecution, setSelectedExecution] = useState<string | null>(null);
  const [executionData, setExecutionData] = useState<ReplayData | null>(null);
  const [loadingExecutions, setLoadingExecutions] = useState(false);
  const [loadingReplay, setLoadingReplay] = useState(false);

  const [usersList, setUsersList] = useState<AppUser[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [adminError, setAdminError] = useState<string | null>(null);
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [editEmail, setEditEmail] = useState("");
  const [editFullName, setEditFullName] = useState("");
  const [editRole, setEditRole] = useState("");

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const toastTimerRef = useRef<number | null>(null);

  const activeSession = useMemo(
    () => sessions.find((session) => session.id === activeSessionId) ?? null,
    [sessions, activeSessionId],
  );

  const activeProviderKey = useMemo<ProviderKey>(() => {
    const normalizedUrl = apiBaseUrl.trim().toLowerCase();
    if (normalizedUrl.includes("api.openai.com")) return "openai";
    if (normalizedUrl.includes("integrate.api.nvidia.com")) return "nvidia";
    if (normalizedUrl.includes("api.groq.com")) return "groq";
    if (normalizedUrl.includes("openrouter.ai")) return "openrouter";
    return "custom";
  }, [apiBaseUrl]);

  const isAuthenticated = Boolean(token);
  const activeModeLabel = modelConfig.inference_engine === "API" ? "External API" : "Local Ollama";
  const selectedModelOption =
    activeProviderKey !== "custom" && PROVIDERS[activeProviderKey].models.includes(modelConfig.llm_model)
      ? modelConfig.llm_model
      : "custom_model";

  useEffect(() => {
    localStorage.setItem("cortex_model_config", JSON.stringify(modelConfig));
  }, [modelConfig]);

  useEffect(() => {
    if (toastTimerRef.current) {
      window.clearTimeout(toastTimerRef.current);
    }

    if (!toast) return;

    toastTimerRef.current = window.setTimeout(() => {
      setToast(null);
    }, 3000);

    return () => {
      if (toastTimerRef.current) {
        window.clearTimeout(toastTimerRef.current);
      }
    };
  }, [toast]);

  useEffect(() => {
    if (!token) return;

    const fetchCurrentUser = async () => {
      try {
        const user = await getMe();
        setCurrentUser(user);
      } catch {
        logout();
        setToken(null);
        setCurrentUser(null);
      }
    };

    void fetchCurrentUser();
  }, [token]);

  useEffect(() => {
    if (!token) return;

    const loadSettings = async () => {
      try {
        const settings = await getUserSettings();
        setApiBaseUrl(settings.api_base_url || "");
        setApiKey(settings.api_key_masked || "");
      } catch {
        setApiBaseUrl("");
        setApiKey("");
      }
    };

    void loadSettings();
  }, [token]);

  useEffect(() => {
    const loadSessions = async () => {
      const storageKey = currentUser ? `cortex_sessions_user_${currentUser.id}` : "cortex_sessions_guest";
      const saved = localStorage.getItem(storageKey);

      if (saved) {
        try {
          const parsed = JSON.parse(saved) as ChatSession[];
          if (Array.isArray(parsed) && parsed.length > 0) {
            setSessions(parsed);
            setActiveSessionId(parsed[0].id);
            return;
          }
        } catch {
          // ignored, we will fall back to a new session
        }
      }

      if (currentUser) {
        try {
          const history = await getChatHistory();
          if (history.length > 0) {
            const messages: ChatMessage[] = [
              {
                id: "welcome",
                sender: "assistant",
                text: "Recovered your stored conversation history. This workspace can keep building from where you left off.",
                timestamp: new Date().toLocaleTimeString(),
              },
            ];

            history.forEach((item, index) => {
              messages.push({
                id: `history-user-${index}`,
                sender: "user",
                text: item.query,
                timestamp: "",
              });
              messages.push({
                id: `history-assistant-${index}`,
                sender: "assistant",
                text: item.response,
                timestamp: "",
              });
            });

            const importedSession = {
              id: `imported-${crypto.randomUUID()}`,
              title: "Recovered History",
              messages,
              createdAt: new Date().toISOString(),
            } satisfies ChatSession;

            setSessions([importedSession]);
            setActiveSessionId(importedSession.id);
            return;
          }
        } catch {
          // ignored, we will fall back to a new session
        }
      }

      const freshSession = createFreshSession();
      setSessions([freshSession]);
      setActiveSessionId(freshSession.id);
    };

    void loadSessions();
  }, [currentUser]);

  useEffect(() => {
    if (!sessions.length) return;

    const storageKey = currentUser ? `cortex_sessions_user_${currentUser.id}` : "cortex_sessions_guest";
    localStorage.setItem(storageKey, JSON.stringify(sessions));
  }, [sessions, currentUser]);

  useEffect(() => {
    const loadExecutions = async () => {
      setLoadingExecutions(true);
      try {
        const data = await listExecutions();
        setExecutions(data);
      } catch {
        setExecutions([]);
      } finally {
        setLoadingExecutions(false);
      }
    };

    void loadExecutions();
  }, []);

  useEffect(() => {
    if (!selectedExecution) {
      return;
    }

    let active = true;

    const loadReplay = async () => {
      setLoadingReplay(true);
      try {
        const data = await getExecutionReplay(selectedExecution);
        if (active) setExecutionData(data);
      } catch {
        if (active) setExecutionData(null);
      } finally {
        if (active) setLoadingReplay(false);
      }
    };

    void loadReplay();

    return () => {
      active = false;
    };
  }, [selectedExecution]);

  useEffect(() => {
    if (panelTab === "models" || modelConfig.inference_engine === "Ollama") {
      const loadModels = async () => {
        setLoadingModels(true);
        try {
          const models = await getInstalledModels();
          setInstalledModels(models);
        } catch {
          setInstalledModels([]);
        } finally {
          setLoadingModels(false);
        }
      };

      void loadModels();
    }
  }, [panelTab, modelConfig.inference_engine]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [activeSession?.messages.length, isGenerating]);

  const persistTemporarySettings = (nextBaseUrl: string, nextKey: string) => {
    if (token) return;
    sessionStorage.setItem("cortex_api_base_url", nextBaseUrl);
    sessionStorage.setItem("cortex_api_key", nextKey);
  };

  const updateModelField = (field: keyof ModelConfig, value: string) => {
    setModelConfig((previous) => ({ ...previous, [field]: value }));
  };

  const setProvider = (providerKey: ProviderKey) => {
    const provider = PROVIDERS[providerKey];
    setApiBaseUrl(provider.defaultUrl);
    persistTemporarySettings(provider.defaultUrl, apiKey);

    if (providerKey === "custom") {
      updateModelField("llm_model", "");
      return;
    }

    const nextModel = provider.models[0] ?? "";
    updateModelField("llm_model", nextModel);
  };

  const handleApiBaseUrlChange = (value: string) => {
    setApiBaseUrl(value);
    persistTemporarySettings(value, apiKey);
  };

  const handleApiKeyChange = (value: string) => {
    setApiKey(value);
    persistTemporarySettings(apiBaseUrl, value);
  };

  const announceToast = (message: string) => {
    setToast(message);
  };

  const clearAuthForm = () => {
    setAuthEmail("");
    setAuthPassword("");
    setAuthFullName("");
    setAuthError(null);
  };

  const handleNewChat = () => {
    const session = createFreshSession();
    setSessions((previous) => [session, ...previous]);
    setActiveSessionId(session.id);
    setRenamingId(null);
    setRenameValue("");
    announceToast("Started a fresh workspace session");
  };

  const deleteSession = (id: string) => {
    const remaining = sessions.filter((session) => session.id !== id);
    if (remaining.length === 0) {
      const session = createFreshSession();
      setSessions([session]);
      setActiveSessionId(session.id);
      return;
    }

    setSessions(remaining);
    if (activeSessionId === id) {
      setActiveSessionId(remaining[0].id);
    }
  };

  const renameSession = (id: string, title: string) => {
    const trimmed = title.trim();
    if (!trimmed) return;
    setSessions((previous) => previous.map((session) => (session.id === id ? { ...session, title: trimmed } : session)));
  };

  const handleAuthSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAuthError(null);

    try {
      if (authMode === "login") {
        const result = await login(authEmail, authPassword);
        setToken(result.access_token);
        setAuthMode("none");
        clearAuthForm();
        announceToast("Signed in successfully");
      } else if (authMode === "register") {
        await register(authEmail, authFullName, authPassword);
        const result = await login(authEmail, authPassword);
        setToken(result.access_token);
        setAuthMode("none");
        clearAuthForm();
        announceToast("Account created and signed in");
      }
    } catch (error: unknown) {
      const responseError = error as { response?: { data?: { detail?: string } } };
      setAuthError(responseError.response?.data?.detail || "Authentication failed.");
    }
  };

  const handleLogoutClick = () => {
    logout();
    setToken(null);
    setCurrentUser(null);
    setPanelTab("traces");
    announceToast("Signed out");
  };

  const loadUsers = useCallback(async () => {
    setLoadingUsers(true);
    setAdminError(null);
    try {
      const users = await getUsers();
      setUsersList(users);
    } catch (error: unknown) {
      const responseError = error as { response?: { data?: { detail?: string } } };
      setAdminError(responseError.response?.data?.detail || "Failed to load users.");
    } finally {
      setLoadingUsers(false);
    }
  }, []);

  useEffect(() => {
    if (panelTab === "admin" && currentUser?.role === "admin") {
      const loadAdminUsers = async () => {
        setLoadingUsers(true);
        setAdminError(null);
        try {
          const users = await getUsers();
          setUsersList(users);
        } catch (error: unknown) {
          const responseError = error as { response?: { data?: { detail?: string } } };
          setAdminError(responseError.response?.data?.detail || "Failed to load users.");
        } finally {
          setLoadingUsers(false);
        }
      };

      void loadAdminUsers();
    }
  }, [panelTab, currentUser]);

  const handleUserStartEdit = (user: AppUser) => {
    setEditingUserId(user.id);
    setEditEmail(user.email);
    setEditFullName(user.full_name);
    setEditRole(user.role);
  };

  const handleUserSave = async (userId: number) => {
    try {
      await updateUser(userId, editEmail, editFullName, editRole);
      setEditingUserId(null);
      await loadUsers();
      if (userId === currentUser?.id) {
        const updated = await getMe();
        setCurrentUser(updated);
      }
      announceToast("User updated");
    } catch (error: unknown) {
      const responseError = error as { response?: { data?: { detail?: string } } };
      setAdminError(responseError.response?.data?.detail || "Failed to update user.");
    }
  };

  const handleUserDelete = async (userId: number) => {
    if (userId === currentUser?.id) {
      setAdminError("You cannot delete your own account.");
      return;
    }

    if (!window.confirm("Delete this user?")) return;

    try {
      await deleteUser(userId);
      await loadUsers();
      announceToast("User deleted");
    } catch (error: unknown) {
      const responseError = error as { response?: { data?: { detail?: string } } };
      setAdminError(responseError.response?.data?.detail || "Failed to delete user.");
    }
  };

  const fetchInstalledModels = async () => {
    setLoadingModels(true);
    try {
      const models = await getInstalledModels();
      setInstalledModels(models);
    } catch {
      setInstalledModels([]);
    } finally {
      setLoadingModels(false);
    }
  };

  const handlePullModel = async (modelName: string) => {
    setPullingModelName(modelName);
    setPullProgress({ status: "Starting download", percent: 0 });

    try {
      await pullModel(modelName, (progress) => {
        setPullProgress({
          status: progress.status,
          percent: progress.percent,
        });
      });

      await fetchInstalledModels();
      setToast(`Model ${modelName} is available`);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Failed to download model";
      setPullProgress((previous) => ({
        status: `Error: ${message}`,
        percent: previous?.percent ?? 0,
      }));
    }
  };

  const handleDeleteModel = async (modelName: string) => {
    if (!window.confirm(`Delete ${modelName}?`)) return;

    try {
      await deleteModel(modelName);
      await fetchInstalledModels();
      announceToast("Model deleted");
    } catch {
      announceToast("Failed to delete model");
    }
  };

  const handleSaveSettings = async () => {
    setSettingsLoading(true);
    setSettingsSavedMessage(null);

    try {
      const result = await updateUserSettings({
        api_base_url: apiBaseUrl,
        api_key: apiKey,
      });

      if (result.api_key_masked) {
        setApiKey(result.api_key_masked);
      }

      setSettingsSavedMessage("Credentials saved securely.");
      announceToast("Settings saved");
    } catch {
      setErrorMessage("Failed to save API settings.");
    } finally {
      setSettingsLoading(false);
    }
  };

  const handleSendMessage = async (event?: FormEvent<HTMLFormElement>, customQuery?: string) => {
    event?.preventDefault();

    if (isGenerating) return;

    const query = (customQuery ?? inputQuery).trim();
    if (!query || !activeSession) return;

    const userMessage: ChatMessage = {
      id: `msg-${crypto.randomUUID()}`,
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString(),
    };

    const nextTitle = activeSession.title === "New Session" ? buildSessionTitle(query) : activeSession.title;
    const updatedMessages = [...activeSession.messages, userMessage];
    const history: ChatTurn[] = activeSession.messages
      .filter((message) => message.id !== "welcome")
      .map((message) => ({
        role: message.sender,
        content: message.text,
      }));

    setSessions((previous) =>
      previous.map((session) =>
        session.id === activeSession.id
          ? { ...session, title: nextTitle, messages: updatedMessages }
          : session,
      ),
    );

    setInputQuery("");
    setIsGenerating(true);
    setErrorMessage(null);

    try {
      const config: ModelConfig = {
        ...modelConfig,
        api_key: apiKey,
        api_base_url: apiBaseUrl,
      };

      const response: AskResponse = await askQuestion(query, Boolean(token), history, config);

      const assistantMessage: ChatMessage = {
        id: `msg-${crypto.randomUUID()}`,
        sender: "assistant",
        text: response.response,
        executionId: response.execution_id,
        timestamp: new Date().toLocaleTimeString(),
      };

      setSessions((previous) =>
        previous.map((session) =>
          session.id === activeSession.id
            ? { ...session, title: nextTitle, messages: [...updatedMessages, assistantMessage] }
            : session,
        ),
      );

      if (response.execution_id) {
        const refreshed = await listExecutions();
        setExecutions(refreshed);
        setSelectedExecution(response.execution_id);
        setPanelTab("traces");
      }
    } catch (error: unknown) {
      const responseError = error as { response?: { status?: number; data?: { error?: string; model?: string } } };
      if (responseError.response?.status === 422 && responseError.response?.data?.error === "model_not_installed") {
        setMissingModel(responseError.response.data.model || null);
        return;
      }

      setErrorMessage("The assistant could not be reached. Check the backend or local model provider.");
      const failureMessage: ChatMessage = {
        id: `msg-${crypto.randomUUID()}`,
        sender: "assistant",
        text: "I hit a routing problem while processing that request.",
        timestamp: new Date().toLocaleTimeString(),
      };

      setSessions((previous) =>
        previous.map((session) =>
          session.id === activeSession.id ? { ...session, messages: [...updatedMessages, failureMessage] } : session,
        ),
      );
    } finally {
      setIsGenerating(false);
    }
  };

  const inspectExecution = (executionId: string) => {
    setSelectedExecution(executionId);
    setPanelTab("traces");
  };

  const handleSessionRenameCommit = (sessionId: string) => {
    renameSession(sessionId, renameValue);
    setRenamingId(null);
    setRenameValue("");
  };

  const sessionCount = sessions.length;
  const activeExecutionCount = executions.length;
  const latestExecution = executions[0];
  const readyChip = isAuthenticated ? "Authenticated" : "Local guest";

  const handleComposerKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      const form = event.currentTarget.form;
      if (form) {
        form.requestSubmit();
      }
    }
  };

  return (
    <div className="shell">
      <div className="background-grid" />
      <div className="background-orb background-orb--one" />
      <div className="background-orb background-orb--two" />

      {toast && <div className="toast">{toast}</div>}

      <aside className={`sidebar ${sidebarOpen ? "is-open" : "is-closed"}`}>
        <div className="sidebar__brand">
          <button type="button" className="brand-mark" onClick={() => setSidebarOpen((value) => !value)}>
            CX
          </button>
          <div>
            <p className="eyebrow">Cortex Workspace</p>
            <h1>Local AI Control Room</h1>
          </div>
        </div>

        <div className="sidebar__status card">
          <div className="card__header">
            <span>Runtime</span>
            <StatusPill status={modelConfig.inference_engine} />
          </div>

          <div className="status-stack">
            <div className="status-row">
              <span>Mode</span>
              <strong>{activeModeLabel}</strong>
            </div>
            <div className="status-row">
              <span>Identity</span>
              <strong>{readyChip}</strong>
            </div>
            <div className="status-row">
              <span>Model</span>
              <strong>{modelConfig.llm_model || "unset"}</strong>
            </div>
          </div>

          <button type="button" className="primary-btn" onClick={handleNewChat}>
            New Chat
          </button>

          <div className="inline-actions">
            <button type="button" className="ghost-btn" onClick={() => setPanelTab("traces")}>
              Traces
            </button>
            <button type="button" className="ghost-btn" onClick={() => setPanelTab("models")}>
              Models
            </button>
          </div>
        </div>

        <div className="sidebar__sessions card">
          <div className="card__header">
            <span>Sessions</span>
            <strong>{sessionCount}</strong>
          </div>

          <div className="session-list">
            {sessions.map((session, index) => {
              const active = session.id === activeSessionId;
              const isRenaming = renamingId === session.id;

              return (
                <button
                  key={session.id}
                  type="button"
                  className={`session-item ${active ? "is-active" : ""}`}
                  style={{ animationDelay: `${Math.min(index, 6) * 55}ms` }}
                  onClick={() => {
                    setActiveSessionId(session.id);
                    setPanelTab("traces");
                  }}
                >
                  <div className="session-item__main">
                    <span className="session-dot" />

                    {isRenaming ? (
                      <input
                        autoFocus
                        value={renameValue}
                        onClick={(event) => event.stopPropagation()}
                        onChange={(event) => setRenameValue(event.target.value)}
                        onKeyDown={(event) => {
                          if (event.key === "Enter") {
                            handleSessionRenameCommit(session.id);
                          }
                          if (event.key === "Escape") {
                            setRenamingId(null);
                            setRenameValue("");
                          }
                        }}
                        onBlur={() => handleSessionRenameCommit(session.id)}
                        className="session-rename"
                      />
                    ) : (
                      <div className="session-copy">
                        <strong>{session.title}</strong>
                        <span>{formatTimestamp(session.createdAt)}</span>
                      </div>
                    )}
                  </div>

                  <div className="session-actions">
                    <button
                      type="button"
                      className="icon-btn"
                      onClick={(event) => {
                        event.stopPropagation();
                        setRenamingId(session.id);
                        setRenameValue(session.title);
                      }}
                      aria-label="Rename session"
                    >
                      ✎
                    </button>
                    <button
                      type="button"
                      className="icon-btn icon-btn--danger"
                      onClick={(event) => {
                        event.stopPropagation();
                        deleteSession(session.id);
                      }}
                      aria-label="Delete session"
                    >
                      ×
                    </button>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        <div className="sidebar__profile card">
          {currentUser ? (
            <>
              <div className="profile-head">
                <div className="avatar">{currentUser.full_name.slice(0, 1).toUpperCase()}</div>
                <div>
                  <strong>{currentUser.full_name}</strong>
                  <span>{currentUser.email}</span>
                </div>
              </div>
              <div className="profile-meta">
                <span className="meta-chip">{currentUser.role}</span>
                <span className="meta-chip">{activeExecutionCount} traces</span>
              </div>
              <button type="button" className="ghost-btn ghost-btn--full" onClick={handleLogoutClick}>
                Sign out
              </button>
            </>
          ) : (
            <>
              <strong>Guest mode</strong>
              <p className="muted">
                Local chat is available right now. Sign in to sync memory, settings, and admin tools.
              </p>
              <div className="inline-actions">
                <button type="button" className="primary-btn primary-btn--ghost" onClick={() => setAuthMode("login")}>
                  Sign in
                </button>
                <button type="button" className="ghost-btn" onClick={() => setAuthMode("register")}>
                  Create account
                </button>
              </div>
            </>
          )}
        </div>
      </aside>

      <main className="workspace">
        <header className="hero card">
          <div className="hero__title">
            <button type="button" className="icon-btn icon-btn--wide" onClick={() => setSidebarOpen((value) => !value)}>
              {sidebarOpen ? "Collapse" : "Expand"}
            </button>
            <div>
              <p className="eyebrow">Operational cockpit</p>
              <h2>{activeSession?.title ?? "New Session"}</h2>
            </div>
          </div>

          <div className="hero__stats">
            <div className="stat-card">
              <span>Sessions</span>
              <strong>{pad(sessionCount)}</strong>
            </div>
            <div className="stat-card">
              <span>Executions</span>
              <strong>{pad(activeExecutionCount)}</strong>
            </div>
            <div className="stat-card">
              <span>Latest</span>
              <strong>{latestExecution?.status ?? "idle"}</strong>
            </div>
            <div className="stat-card">
              <span>Panel</span>
              <strong>{panelTab}</strong>
            </div>
          </div>
        </header>

        {errorMessage ? <div className="alert alert--error">{errorMessage}</div> : null}
        {adminError ? <div className="alert alert--error">{adminError}</div> : null}

        <section className="content-grid">
          <section className="chat-panel card">
            <div className="chat-panel__top">
              <div>
                <p className="eyebrow">Chat stream</p>
                <h3>Build, inspect, and iterate in one place</h3>
              </div>
              <div className="chat-panel__chips">
                <span className="meta-chip">{isAuthenticated ? "private chat" : "public chat"}</span>
                <span className="meta-chip">{modelConfig.llm_model || "no model"}</span>
              </div>
            </div>

            <div className="chat-stream">
              {!activeSession || activeSession.messages.length <= 1 ? (
                <div className="empty-state">
                  <div className="empty-state__hero">
                    <div className="empty-state__glyph">C</div>
                    <h3>Techy, fast, and focused.</h3>
                    <p>
                      Ask for code analysis, repository context, execution traces, or a full product review.
                    </p>
                  </div>

                  <div className="quick-grid">
                    {QUICK_ACTIONS.map((item, index) => (
                      <button
                        key={item.title}
                        type="button"
                        className="quick-card"
                        style={{ animationDelay: `${index * 80}ms` }}
                        onClick={() => void handleSendMessage(undefined, item.prompt)}
                      >
                        <span className="quick-card__icon">{item.icon}</span>
                        <strong>{item.title}</strong>
                        <p>{item.description}</p>
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="message-list">
                  {activeSession.messages.map((message, index) => (
                    <article
                      key={message.id}
                      className={`message-row message-row--${message.sender}`}
                      style={{ animationDelay: `${Math.min(index, 10) * 35}ms` }}
                    >
                      <div className="message-avatar">{message.sender === "user" ? "U" : "C"}</div>
                      <div className="message-card">
                        <div className="message-meta">
                          <strong>{message.sender === "user" ? "You" : "Cortex"}</strong>
                          <span>{message.timestamp}</span>
                        </div>
                        <MessageBody text={message.text} />
                        {message.executionId && (
                          <div className="message-actions">
                            <button type="button" className="ghost-btn" onClick={() => inspectExecution(message.executionId!)}>
                              Inspect execution
                            </button>
                          </div>
                        )}
                      </div>
                    </article>
                  ))}

                  {isGenerating && (
                    <article className="message-row message-row--assistant">
                      <div className="message-avatar">C</div>
                      <div className="message-card message-card--typing">
                        <div className="typing-dots">
                          <span />
                          <span />
                          <span />
                        </div>
                      </div>
                    </article>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>

            <form className="composer" onSubmit={(event) => void handleSendMessage(event)}>
              <textarea
                value={inputQuery}
                onChange={(event) => setInputQuery(event.target.value)}
                onKeyDown={handleComposerKeyDown}
                placeholder={
                  isAuthenticated
                    ? "Ask Cortex to inspect code, search memories, or trace the current system..."
                    : "Guest mode: ask anything and the assistant will reply locally..."
                }
                rows={4}
                disabled={isGenerating}
              />
              <div className="composer__bar">
                <span className="muted">Cmd/Ctrl + Enter to send</span>
                <button type="submit" className="primary-btn" disabled={isGenerating || !inputQuery.trim()}>
                  {isGenerating ? "Routing..." : "Send"}
                </button>
              </div>
            </form>
          </section>

          <aside className="inspector card">
            <div className="inspector__tabs">
              <button type="button" className={panelTab === "traces" ? "tab-btn is-active" : "tab-btn"} onClick={() => setPanelTab("traces")}>
                Traces
              </button>
              <button type="button" className={panelTab === "models" ? "tab-btn is-active" : "tab-btn"} onClick={() => setPanelTab("models")}>
                Models
              </button>
              {currentUser?.role === "admin" && (
                <button type="button" className={panelTab === "admin" ? "tab-btn is-active" : "tab-btn"} onClick={() => setPanelTab("admin")}>
                  Admin
                </button>
              )}
            </div>

            {panelTab === "traces" && (
              <div className="inspector-panel">
                <div className="panel-head">
                  <div>
                    <p className="eyebrow">Execution trace</p>
                    <h3>Replay the system</h3>
                  </div>
                  <button type="button" className="icon-btn" onClick={() => void listExecutions().then(setExecutions)}>
                    ↻
                  </button>
                </div>

                <div className="scroll-stack">
                  {executions.map((execution) => {
                    const active = execution.execution_id === selectedExecution;

                    return (
                      <button
                        key={execution.execution_id}
                        type="button"
                        className={`trace-card ${active ? "is-active" : ""}`}
                        onClick={() => setSelectedExecution(execution.execution_id)}
                      >
                        <div className="trace-card__top">
                          <span className="trace-id">{execution.execution_id.slice(0, 12)}…</span>
                          <StatusPill status={execution.status} />
                        </div>
                        <div className="trace-card__meta">
                          <span>{execution.event_count ?? 0} events</span>
                          <span>{execution.summary?.steps_executed ?? 0} steps</span>
                        </div>
                        <div className="trace-card__meta">
                          <span>{execution.summary?.tools_used?.length ?? 0} tools</span>
                          <span>{formatTimestamp(execution.last_timestamp)}</span>
                        </div>
                      </button>
                    );
                  })}

                  {!loadingExecutions && executions.length === 0 && (
                    <div className="mini-empty">Run a chat query to populate execution traces.</div>
                  )}
                </div>

                <div className="trace-detail">
                  {!executionData ? (
                    <div className="mini-empty">{loadingReplay ? "Loading replay..." : "Pick a trace to inspect."}</div>
                  ) : (
                    <>
                      <div className="trace-summary-grid">
                        <div className="mini-stat">
                          <span>Status</span>
                          <StatusPill status={executionData.status} />
                        </div>
                        <div className="mini-stat">
                          <span>Duration</span>
                          <strong>{formatDuration(executionData.summary?.duration_ms)}</strong>
                        </div>
                        <div className="mini-stat">
                          <span>Steps</span>
                          <strong>{executionData.summary?.steps_executed ?? 0}</strong>
                        </div>
                        <div className="mini-stat">
                          <span>Errors</span>
                          <strong>{executionData.summary?.error_count ?? 0}</strong>
                        </div>
                      </div>

                      <div className="chip-wrap">
                        {(executionData.summary?.tools_used ?? []).length > 0 ? (
                          executionData.summary.tools_used?.map((tool) => (
                            <span key={tool} className="meta-chip">
                              {tool}
                            </span>
                          ))
                        ) : (
                          <span className="muted">No tools were recorded.</span>
                        )}
                      </div>

                      <div className="timeline">
                        {executionData.replay.map((step) => (
                          <article key={step.step} className="timeline-item">
                            <div className="timeline-item__head">
                              <span className="timeline-step">Step {step.step}</span>
                              <strong>{step.action}</strong>
                              <span className="timeline-time">{formatTimestamp(step.raw?.timestamp)}</span>
                            </div>
                            <div className="timeline-item__body">
                              <div className="timeline-row">
                                <span>Type</span>
                                <code>{step.raw?.type || "event"}</code>
                              </div>
                              <div className="timeline-row">
                                <span>Source</span>
                                <code>{step.raw?.source || "system"}</code>
                              </div>
                              {step.raw?.human_readable && <p>{step.raw.human_readable}</p>}
                            </div>
                          </article>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            {panelTab === "models" && (
              <div className="inspector-panel">
                <div className="panel-head">
                  <div>
                    <p className="eyebrow">Model stack</p>
                    <h3>Runtime configuration</h3>
                  </div>
                </div>

                <div className="settings-block">
                  <label>Inference engine</label>
                  <select
                    value={modelConfig.inference_engine}
                    onChange={(event) => updateModelField("inference_engine", event.target.value)}
                  >
                    <option value="Ollama">Ollama</option>
                    <option value="API">External API</option>
                  </select>
                </div>

                {modelConfig.inference_engine === "Ollama" ? (
                  <div className="settings-stack">
                    <div className="settings-block">
                      <label>Main model</label>
                      <select value={modelConfig.llm_model} onChange={(event) => updateModelField("llm_model", event.target.value)}>
                        {CURATED_MODELS.map((model) => (
                          <option key={model.id} value={model.id}>
                            {model.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                ) : (
                  <div className="settings-stack">
                    <div className="settings-block">
                      <label>Provider</label>
                      <select value={activeProviderKey} onChange={(event) => setProvider(event.target.value as ProviderKey)}>
                        {Object.entries(PROVIDERS).map(([key, provider]) => (
                          <option key={key} value={key}>
                            {provider.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="settings-block">
                      <label>Model</label>
                      {activeProviderKey === "custom" ? (
                        <input
                          value={modelConfig.llm_model}
                          onChange={(event) => updateModelField("llm_model", event.target.value)}
                          placeholder="gpt-4o"
                        />
                      ) : (
                        <select
                          value={selectedModelOption}
                          onChange={(event) => {
                            const value = event.target.value;
                            updateModelField("llm_model", value === "custom_model" ? "" : value);
                          }}
                        >
                          {PROVIDERS[activeProviderKey].models.map((model) => (
                            <option key={model} value={model}>
                              {model}
                            </option>
                          ))}
                          <option value="custom_model">Custom model name</option>
                        </select>
                      )}
                    </div>

                    <div className="settings-block">
                      <label>API base URL</label>
                      <input
                        value={apiBaseUrl}
                        onChange={(event) => handleApiBaseUrlChange(event.target.value)}
                        placeholder="https://api.openai.com/v1"
                      />
                    </div>

                    <div className="settings-block">
                      <label>API key</label>
                      <div className="input-split">
                        <input
                          type={showApiKey ? "text" : "password"}
                          value={apiKey}
                          onChange={(event) => handleApiKeyChange(event.target.value)}
                          placeholder="sk-..."
                        />
                        <button type="button" className="ghost-btn" onClick={() => setShowApiKey((value) => !value)}>
                          {showApiKey ? "Hide" : "Show"}
                        </button>
                      </div>
                    </div>

                    {token ? (
                      <button type="button" className="primary-btn" onClick={handleSaveSettings} disabled={settingsLoading}>
                        {settingsLoading ? "Saving..." : "Save credentials"}
                      </button>
                    ) : (
                      <div className="mini-empty">Sign in to persist API credentials securely.</div>
                    )}
                    {settingsSavedMessage && <div className="success-note">{settingsSavedMessage}</div>}
                  </div>
                )}

                <div className="settings-block">
                  <label>Embedding model</label>
                  <select value={modelConfig.embedding_model} onChange={(event) => updateModelField("embedding_model", event.target.value)}>
                    <option value="BAAI/bge-small-en-v1.5">BGE Small EN v1.5</option>
                    <option value="all-MiniLM-L6-v2">MiniLM L6 v2</option>
                    <option value="all-mpnet-base-v2">MPNet Base v2</option>
                  </select>
                </div>

                <div className="settings-block">
                  <label>Code parsing</label>
                  <select value={modelConfig.code_parsing} onChange={(event) => updateModelField("code_parsing", event.target.value)}>
                    <option value="Tree-sitter">Tree-sitter</option>
                    <option value="Plain">Plain overlap</option>
                  </select>
                </div>

                <div className="settings-block">
                  <label>Active runtime</label>
                  <div className="runtime-pill">
                    <span className="pulse" />
                    <strong>{modelConfig.inference_engine}</strong>
                    <span>{modelConfig.llm_model || "unset"}</span>
                  </div>
                </div>

                {modelConfig.inference_engine === "Ollama" && (
                  <>
                    <div className="panel-divider" />
                    <div className="panel-head">
                      <div>
                        <p className="eyebrow">Local models</p>
                        <h3>Installed and downloadable</h3>
                      </div>
                      <button type="button" className="icon-btn" onClick={fetchInstalledModels}>
                        ↻
                      </button>
                    </div>

                    <div className="scroll-stack">
                      {loadingModels ? (
                        <div className="mini-empty">Loading local model inventory...</div>
                      ) : installedModels.length === 0 ? (
                        <div className="mini-empty">No Ollama models were found.</div>
                      ) : (
                        installedModels.map((model) => (
                          <div key={model.name} className="model-row">
                            <div>
                              <strong>{model.name}</strong>
                              <span>{(model.size / (1024 * 1024 * 1024)).toFixed(2)} GB</span>
                            </div>
                            {currentUser?.role === "admin" && (
                              <button type="button" className="icon-btn icon-btn--danger" onClick={() => handleDeleteModel(model.name)}>
                                ×
                              </button>
                            )}
                          </div>
                        ))
                      )}
                    </div>

                    <div className="download-list">
                      {CURATED_MODELS.filter(
                        (model) =>
                          !installedModels.some(
                            (installed) => installed.name === model.id || installed.name.startsWith(`${model.id}:`),
                          ),
                      ).map((model) => (
                        <div key={model.id} className="download-row">
                          <span>{model.name}</span>
                          <button type="button" className="ghost-btn" onClick={() => void handlePullModel(model.id)}>
                            Download
                          </button>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}

            {panelTab === "admin" && currentUser?.role === "admin" && (
              <div className="inspector-panel">
                <div className="panel-head">
                  <div>
                    <p className="eyebrow">Admin console</p>
                    <h3>User management</h3>
                  </div>
                  <button type="button" className="icon-btn" onClick={loadUsers}>
                    ↻
                  </button>
                </div>

                {loadingUsers ? (
                  <div className="mini-empty">Loading user records...</div>
                ) : (
                  <div className="scroll-stack">
                    {usersList.map((user) => {
                      const isEditing = editingUserId === user.id;
                      return (
                        <div key={user.id} className="user-row">
                          <div className="user-row__details">
                            <strong>{isEditing ? "Editing user" : user.full_name}</strong>
                            {isEditing ? (
                              <div className="settings-stack">
                                <input value={editFullName} onChange={(event) => setEditFullName(event.target.value)} />
                                <input value={editEmail} onChange={(event) => setEditEmail(event.target.value)} />
                                <select value={editRole} onChange={(event) => setEditRole(event.target.value)}>
                                  <option value="user">user</option>
                                  <option value="admin">admin</option>
                                </select>
                              </div>
                            ) : (
                              <>
                                <span>{user.email}</span>
                                <span className="meta-chip">{user.role}</span>
                              </>
                            )}
                          </div>

                          <div className="user-row__actions">
                            {isEditing ? (
                              <>
                                <button type="button" className="ghost-btn" onClick={() => void handleUserSave(user.id)}>
                                  Save
                                </button>
                                <button type="button" className="ghost-btn" onClick={() => setEditingUserId(null)}>
                                  Cancel
                                </button>
                              </>
                            ) : (
                              <>
                                <button type="button" className="ghost-btn" onClick={() => handleUserStartEdit(user)}>
                                  Edit
                                </button>
                                {user.id !== currentUser?.id && (
                                  <button type="button" className="icon-btn icon-btn--danger" onClick={() => void handleUserDelete(user.id)}>
                                    ×
                                  </button>
                                )}
                              </>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </aside>
        </section>
      </main>

      {authMode !== "none" && (
        <div className="overlay">
          <div className="modal card">
            <div className="modal__header">
              <div>
                <p className="eyebrow">Secure access</p>
                <h3>{authMode === "login" ? "Sign in to Cortex" : "Create your workspace account"}</h3>
              </div>
              <button type="button" className="icon-btn" onClick={() => { setAuthMode("none"); clearAuthForm(); }}>
                ×
              </button>
            </div>

            {authError && <div className="alert alert--error">{authError}</div>}

            <form onSubmit={handleAuthSubmit} className="auth-form">
              {authMode === "register" && (
                <label className="settings-block">
                  <span>Full name</span>
                  <input value={authFullName} onChange={(event) => setAuthFullName(event.target.value)} placeholder="Ada Lovelace" required />
                </label>
              )}

              <label className="settings-block">
                <span>Email</span>
                <input value={authEmail} onChange={(event) => setAuthEmail(event.target.value)} placeholder="developer@cortex.local" required type="email" />
              </label>

              <label className="settings-block">
                <span>Password</span>
                <input
                  value={authPassword}
                  onChange={(event) => setAuthPassword(event.target.value)}
                  placeholder="••••••••"
                  required
                  minLength={8}
                  type="password"
                />
              </label>

              <button type="submit" className="primary-btn primary-btn--full">
                {authMode === "login" ? "Authenticate" : "Register"}
              </button>
            </form>

            <div className="modal__footer">
              {authMode === "login" ? (
                <button type="button" className="ghost-link" onClick={() => { setAuthMode("register"); setAuthError(null); }}>
                  Need an account? Create one now.
                </button>
              ) : (
                <button type="button" className="ghost-link" onClick={() => { setAuthMode("login"); setAuthError(null); }}>
                  Already registered? Sign in instead.
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {pullingModelName && (
        <div className="overlay">
          <div className="modal card">
            <div className="modal__header">
              <div>
                <p className="eyebrow">Model download</p>
                <h3>{pullingModelName}</h3>
              </div>
            </div>

            <div className="progress-shell">
              <div className="progress-bar">
                <div className="progress-bar__fill" style={{ width: `${pullProgress?.percent ?? 0}%` }} />
              </div>
              <div className="progress-row">
                <span>{pullProgress?.status ?? "Preparing..."}</span>
                <strong>{pullProgress?.percent ?? 0}%</strong>
              </div>
            </div>

            <div className="modal__footer">
              {pullProgress?.status.startsWith("Error:") || pullProgress?.percent === 100 ? (
                <button type="button" className="primary-btn" onClick={() => { setPullingModelName(null); setPullProgress(null); }}>
                  Close
                </button>
              ) : (
                <span className="muted">This can take a while. Keep the window open.</span>
              )}
            </div>
          </div>
        </div>
      )}

      {missingModel && (
        <div className="overlay">
          <div className="modal card">
            <div className="modal__header">
              <div>
                <p className="eyebrow">Model required</p>
                <h3>{missingModel}</h3>
              </div>
            </div>
            <p className="modal__body">
              The selected model is not installed in Ollama yet. Download it now or switch the runtime model.
            </p>
            <div className="modal-actions">
              <button
                type="button"
                className="primary-btn"
                onClick={() => {
                  const model = missingModel;
                  setMissingModel(null);
                  void handlePullModel(model);
                }}
              >
                Download now
              </button>
              <button type="button" className="ghost-btn" onClick={() => setPanelTab("models")}>
                Switch model
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
