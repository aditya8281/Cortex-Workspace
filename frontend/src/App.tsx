import { useEffect, useState } from "react";
import "./App.css";
import { getExecutionReplay, listExecutions } from "./api/execution";
import { getMe, login, register, logout, getUsers, updateUser, deleteUser } from "./api/auth";
import { askQuestion, getChatHistory, getInstalledModels, deleteModel, getUserSettings, updateUserSettings, pullModel, type AskResponse, type ChatTurn, type ModelConfig, type InstalledModel } from "./api/ai";

type User = {
  id: number;
  email: string;
  full_name: string;
  role: string;
};

type ChatSession = {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
};

const QUICK_CARDS = [
  {
    icon: "🔍",
    title: "Search Codebase",
    desc: "Find class definitions, functions, or variable usages in files.",
    prompt: "search for class AIExecutor in the codebase and show its location"
  },
  {
    icon: "📋",
    title: "System Scan",
    desc: "Inspect system configs, services, dependencies, and CPU/memory.",
    prompt: "scan the system configurations and summarize the active services"
  },
  {
    icon: "⚙️",
    title: "Explain Graph",
    desc: "Understand how the GraphRunner controls runtime execution steps.",
    prompt: "explain how GraphRunner works in backend/app/executor/graph_runner.py"
  },
  {
    icon: "⚡",
    title: "AI Capabilities",
    desc: "Ask general inquiries to see what tools the AI is capable of running.",
    prompt: "what are you capable of in this workspace? show me all your tools"
  }
];

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
    payload?: Record<string, any>;
    human_readable?: string;
  };
};

type ReplayData = {
  execution_id: string;
  status: string;
  summary: ExecutionSummary;
  replay: ReplayStep[];
};

type ChatMessage = {
  id: string;
  sender: "user" | "assistant";
  text: string;
  executionId?: string | null;
  timestamp: string;
};

function parseResponseText(text: string) {
  if (!text) return { finalResponse: "", memoryText: "", toolText: "" };

  const memoryRegex = /(?:^|\r?\n)Memory\s+Context:\s*\r?\n/i;
  const toolRegex = /(?:^|\r?\n)Tool\s+Results:\s*\r?\n/i;
  const finalRegex = /(?:^|\r?\n)Final\s+Response:\s*\r?\n/i;

  const memoryMatch = text.match(memoryRegex);
  const toolMatch = text.match(toolRegex);
  const finalMatch = text.match(finalRegex);

  const memoryIdx = memoryMatch && memoryMatch.index !== undefined ? memoryMatch.index : -1;
  const toolIdx = toolMatch && toolMatch.index !== undefined ? toolMatch.index : -1;
  const finalIdx = finalMatch && finalMatch.index !== undefined ? finalMatch.index : -1;

  const sections: { type: "memory" | "tool" | "final"; start: number; headerLength: number }[] = [];
  if (memoryIdx !== -1 && memoryMatch) sections.push({ type: "memory", start: memoryIdx, headerLength: memoryMatch[0].length });
  if (toolIdx !== -1 && toolMatch) sections.push({ type: "tool", start: toolIdx, headerLength: toolMatch[0].length });
  if (finalIdx !== -1 && finalMatch) sections.push({ type: "final", start: finalIdx, headerLength: finalMatch[0].length });

  sections.sort((a, b) => a.start - b.start);

  let memoryText = "";
  let toolText = "";
  let finalResponse = "";

  const preText = sections.length > 0 ? text.slice(0, sections[0].start).trim() : text.trim();

  for (let i = 0; i < sections.length; i++) {
    const current = sections[i];
    const nextStart = i + 1 < sections.length ? sections[i + 1].start : text.length;
    const content = text.slice(current.start + current.headerLength, nextStart).trim();

    if (current.type === "memory") {
      memoryText = content;
    } else if (current.type === "tool") {
      toolText = content;
    } else if (current.type === "final") {
      finalResponse = content;
    }
  }

  if (!finalResponse) {
    if (preText) {
      finalResponse = preText;
    } else if (memoryText || toolText) {
      finalResponse = "Diagnostics execution completed.";
    } else {
      finalResponse = text;
    }
  } else if (preText) {
    finalResponse = preText + "\n\n" + finalResponse;
  }

  return { memoryText, toolText, finalResponse };
}

function Markdown({ text }: { text: string }) {
  if (!text) return null;

  // Split by code blocks first to separate text and code
  const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g;
  const parts: any[] = [];
  let lastIndex = 0;
  let match;

  const renderInline = (inlineText: string) => {
    const inlineRegex = /(\*\*|`)(.*?)\1/g;
    const elements: any[] = [];
    let lastInlineIdx = 0;
    let inlineMatch;
    let keyIdx = 0;

    while ((inlineMatch = inlineRegex.exec(inlineText)) !== null) {
      if (inlineMatch.index > lastInlineIdx) {
        elements.push(inlineText.slice(lastInlineIdx, inlineMatch.index));
      }
      const type = inlineMatch[1];
      const matchText = inlineMatch[2];
      if (type === "**") {
        elements.push(<strong key={`bold-${keyIdx++}`} className="md-strong">{matchText}</strong>);
      } else if (type === "`") {
        elements.push(<code key={`code-${keyIdx++}`} className="md-code">{matchText}</code>);
      }
      lastInlineIdx = inlineRegex.lastIndex;
    }

    if (lastInlineIdx < inlineText.length) {
      elements.push(inlineText.slice(lastInlineIdx));
    }

    return elements.length > 0 ? elements : inlineText;
  };

  const renderTextAndInlineCode = (txt: string, blockKey: string) => {
    const lines = txt.split("\n");
    return lines.map((line, lineIdx) => {
      // Check if it's a heading
      const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
      if (headingMatch) {
        const level = headingMatch[1].length;
        const headingText = headingMatch[2];
        const headingKey = `${blockKey}-h-${lineIdx}`;
        switch (level) {
          case 1: return <h1 key={headingKey} className="md-h1">{renderInline(headingText)}</h1>;
          case 2: return <h2 key={headingKey} className="md-h2">{renderInline(headingText)}</h2>;
          case 3: return <h3 key={headingKey} className="md-h3">{renderInline(headingText)}</h3>;
          default: return <h4 key={headingKey} className="md-h4">{renderInline(headingText)}</h4>;
        }
      }

      // Check if it's a list item
      const listMatch = line.match(/^(\s*)([-*]|\d+\.)\s+(.*)$/);
      if (listMatch) {
        const listText = listMatch[3];
        const isNumbered = /^\d+/.test(listMatch[2]);
        const itemKey = `${blockKey}-li-${lineIdx}`;
        if (isNumbered) {
          return (
            <ol key={itemKey} className="md-ol">
              <li>{renderInline(listText)}</li>
            </ol>
          );
        } else {
          return (
            <ul key={itemKey} className="md-ul">
              <li>{renderInline(listText)}</li>
            </ul>
          );
        }
      }

      // Plain line
      if (line.trim() === "") {
        return <div key={`${blockKey}-br-${lineIdx}`} className="md-br" />;
      }

      return (
        <p key={`${blockKey}-p-${lineIdx}`} className="md-p">
          {renderInline(line)}
        </p>
      );
    });
  };

  let blockKeyIdx = 0;
  while ((match = codeBlockRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      const textPart = text.slice(lastIndex, match.index);
      parts.push(
        <div key={`text-block-${blockKeyIdx++}`}>
          {renderTextAndInlineCode(textPart, `text-${blockKeyIdx}`)}
        </div>
      );
    }

    const language = match[1] || "text";
    const code = match[2];
    parts.push(
      <div key={`code-block-${blockKeyIdx++}`} className="md-code-block-container">
        <div className="md-code-block-header">
          <span className="md-code-block-lang">{language}</span>
          <button 
            type="button" 
            className="md-code-copy-btn"
            onClick={(e) => {
              navigator.clipboard.writeText(code);
              const btn = e.currentTarget;
              btn.innerText = "Copied!";
              setTimeout(() => { btn.innerText = "Copy"; }, 2000);
            }}
          >
            Copy
          </button>
        </div>
        <pre className="md-code-block">
          <code>{code}</code>
        </pre>
      </div>
    );

    lastIndex = codeBlockRegex.lastIndex;
  }

  if (lastIndex < text.length) {
    const textPart = text.slice(lastIndex);
    parts.push(
      <div key={`text-block-${blockKeyIdx++}`}>
        {renderTextAndInlineCode(textPart, `text-${blockKeyIdx}`)}
      </div>
    );
  }

  return <div className="md-container">{parts}</div>;
}

function renderMessageText(text: string) {
  if (!text) return null;

  const { memoryText, toolText, finalResponse } = parseResponseText(text);

  return (
    <div className="chat-bubble-content">
      <div className="chat-bubble-text">
        <Markdown text={finalResponse} />
      </div>
      
      {(memoryText || toolText) && (
        <div className="chat-bubble-diagnostics">
          {toolText && (
            <details className="diagnostics-details">
              <summary className="diagnostics-summary">🔧 View Invoked Tool Outputs</summary>
              <pre className="diagnostics-pre">{toolText}</pre>
            </details>
          )}
          {memoryText && (
            <details className="diagnostics-details">
              <summary className="diagnostics-summary">🧠 View Memory Recall Details</summary>
              <pre className="diagnostics-pre">{memoryText}</pre>
            </details>
          )}
        </div>
      )}
    </div>
  );
}

function App() {
  // Authentication state
  const [token, setToken] = useState<string | null>(localStorage.getItem("cortex_token"));
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authMode, setAuthMode] = useState<"login" | "register" | "none">("none");

  // Auth form input state
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authFullName, setAuthFullName] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);

  // Chat sessions state
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>("");
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");

  // Input query and generating states
  const [inputQuery, setInputQuery] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  
  // Navigation states
  const [activeTab, setActiveTab] = useState<"chat" | "admin">("chat");
  const [showTelemetry, setShowTelemetry] = useState(false);
  const [telemetryTab, setTelemetryTab] = useState<"list" | "detail">("list");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Admin user management state
  const [usersList, setUsersList] = useState<User[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [adminError, setAdminError] = useState<string | null>(null);
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [editEmail, setEditEmail] = useState("");
  const [editFullName, setEditFullName] = useState("");
  const [editRole, setEditRole] = useState("");

  // Model configuration (persisted per-session in localStorage)
  const [modelConfig, setModelConfig] = useState<ModelConfig>(() => {
    try {
      const saved = localStorage.getItem("cortex_model_config");
      if (saved) return JSON.parse(saved);
    } catch {}
    return {
      llm_model: "qwen3:8b",
      embedding_model: "BAAI/bge-small-en-v1.5",
      vector_db: "FAISS",
      inference_engine: "Ollama",
      code_parsing: "Tree-sitter",
    };
  });
  const [showModelConfig, setShowModelConfig] = useState(false);

  // Persist model config whenever it changes
  useEffect(() => {
    localStorage.setItem("cortex_model_config", JSON.stringify(modelConfig));
  }, [modelConfig]);

  const updateModelConfig = (field: keyof ModelConfig, value: string) => {
    setModelConfig(prev => ({ ...prev, [field]: value }));
  };

  // Model library states
  const [installedModels, setInstalledModels] = useState<InstalledModel[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [pullProgress, setPullProgress] = useState<{ status: string; percent: number } | null>(null);
  const [pullingModelName, setPullingModelName] = useState<string | null>(null);
  const [missingModel, setMissingModel] = useState<string | null>(null);

  // API key states
  const [apiBaseUrl, setApiBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [settingsSavedMessage, setSettingsSavedMessage] = useState<string | null>(null);

  // Load API keys from sessionStorage (guests) or backend (users)
  useEffect(() => {
    if (token) {
      async function loadSettings() {
        try {
          const settings = await getUserSettings();
          if (settings.api_base_url) setApiBaseUrl(settings.api_base_url);
          if (settings.api_key_masked) setApiKey(settings.api_key_masked);
        } catch (e) {
          console.error("Failed to load user settings", e);
        }
      }
      loadSettings();
    } else {
      setApiBaseUrl(sessionStorage.getItem("cortex_api_base_url") || "");
      setApiKey(sessionStorage.getItem("cortex_api_key") || "");
    }
  }, [token]);

  const handleApiKeyChange = (val: string) => {
    setApiKey(val);
    if (!token) {
      sessionStorage.setItem("cortex_api_key", val);
    }
  };

  const handleApiBaseUrlChange = (val: string) => {
    setApiBaseUrl(val);
    if (!token) {
      sessionStorage.setItem("cortex_api_base_url", val);
    }
  };

  const handleSaveSettings = async () => {
    setSettingsLoading(true);
    setSettingsSavedMessage(null);
    try {
      const result = await updateUserSettings({
        api_base_url: apiBaseUrl,
        api_key: apiKey
      });
      if (result.api_key_masked) {
        setApiKey(result.api_key_masked);
      }
      setSettingsSavedMessage("Credentials encrypted and saved!");
      setTimeout(() => setSettingsSavedMessage(null), 3000);
    } catch (e) {
      console.error("Failed to save credentials", e);
      setError("Failed to encrypt and save credentials on server.");
    } finally {
      setSettingsLoading(false);
    }
  };

  const fetchInstalledModels = async () => {
    setLoadingModels(true);
    try {
      const list = await getInstalledModels();
      setInstalledModels(list);
    } catch (e) {
      console.error("Failed to get installed models", e);
    } finally {
      setLoadingModels(false);
    }
  };

  useEffect(() => {
    if (showModelConfig) {
      fetchInstalledModels();
    }
  }, [showModelConfig]);

  const handlePullModel = async (modelName: string) => {
    setPullingModelName(modelName);
    setPullProgress({ status: "Starting download...", percent: 0 });
    try {
      await pullModel(modelName, (prog) => {
        setPullProgress({
          status: prog.status,
          percent: prog.percent
        });
      });
      await fetchInstalledModels();
      if (missingModel === modelName || (modelName === "qwen3:8b" && missingModel === "Qwen3 8B (Q4_K_M quantization)")) {
        setMissingModel(null);
      }
    } catch (e: any) {
      console.error("Download failed", e);
      setPullProgress(prev => ({
        status: `Error: ${e.message || "Failed to download model"}`,
        percent: prev?.percent || 0
      }));
    }
  };

  const handleDeleteModel = async (modelName: string) => {
    if (!window.confirm(`Are you sure you want to delete ${modelName}?`)) {
      return;
    }
    try {
      await deleteModel(modelName);
      await fetchInstalledModels();
    } catch (e) {
      console.error("Failed to delete model", e);
      alert("Failed to delete model.");
    }
  };

  const curatedModels = [
    { id: "qwen3:8b", name: "Qwen3 8B (Q4_K_M)" },
    { id: "llama3", name: "Llama 3 8B" },
    { id: "mistral", name: "Mistral 7B" },
    { id: "codellama", name: "CodeLlama 7B" },
    { id: "gemma2", name: "Gemma 2 9B" },
    { id: "phi3", name: "Phi-3 Mini" }
  ];

  // Executions telemetry state
  const [executions, setExecutions] = useState<ExecutionListItem[]>([]);
  const [selectedExecution, setSelectedExecution] = useState<string | null>(null);
  const [executionData, setExecutionData] = useState<ReplayData | null>(null);
  const [loadingExecutions, setLoadingExecutions] = useState(true);
  const [loadingReplay, setLoadingReplay] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch current user details if token is available
  useEffect(() => {
    if (!token) {
      setCurrentUser(null);
      return;
    }

    async function fetchMe() {
      try {
        const user = await getMe();
        setCurrentUser(user);
      } catch (err) {
        // Token might be invalid or expired
        localStorage.removeItem("cortex_token");
        setToken(null);
        setCurrentUser(null);
      }
    }

    fetchMe();
  }, [token]);

  // Load sessions from localStorage or backend
  useEffect(() => {
    const key = currentUser ? `cortex_sessions_user_${currentUser.id}` : `cortex_sessions_guest`;
    const localSaved = localStorage.getItem(key);
    
    if (localSaved) {
      try {
        const parsed = JSON.parse(localSaved);
        if (parsed && parsed.length > 0) {
          setSessions(parsed);
          setActiveSessionId(parsed[0].id);
          return;
        }
      } catch (e) {
        console.error("Failed to parse local sessions", e);
      }
    }
    
    // If no local sessions and logged in, load backend history as an imported session
    if (currentUser) {
      async function importHistory() {
        try {
          const history = await getChatHistory();
          if (history && history.length > 0) {
            const importedMessages: ChatMessage[] = [];
            importedMessages.push({
              id: "welcome",
              sender: "assistant",
              text: "Welcome to Cortex Workspace. I loaded your previous session history from the database below.",
              timestamp: new Date().toLocaleTimeString(),
            });
            
            history.forEach((item, index) => {
              importedMessages.push({
                id: `imported-user-${index}`,
                sender: "user",
                text: item.query,
                timestamp: "",
              });
              importedMessages.push({
                id: `imported-assistant-${index}`,
                sender: "assistant",
                text: item.response,
                timestamp: "",
              });
            });
            
            const importedSession: ChatSession = {
              id: `imported-${Date.now()}`,
              title: "Imported History",
              messages: importedMessages,
              createdAt: new Date().toISOString()
            };
            
            setSessions([importedSession]);
            setActiveSessionId(importedSession.id);
          } else {
            createFreshSession();
          }
        } catch (err) {
          console.error("Failed to import backend history", err);
          createFreshSession();
        }
      }
      importHistory();
    } else {
      createFreshSession();
    }
  }, [currentUser, token]);

  const createFreshSession = () => {
    const freshSession: ChatSession = {
      id: `session-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
      title: "New Chat",
      messages: [
        {
          id: "welcome",
          sender: "assistant",
          text: "Welcome to Cortex Workspace. I can help search files, scan system configurations, and run code analyses. Try asking a question below!",
          timestamp: new Date().toLocaleTimeString(),
        }
      ],
      createdAt: new Date().toISOString()
    };
    setSessions([freshSession]);
    setActiveSessionId(freshSession.id);
  };

  // Save sessions to localStorage when they change
  useEffect(() => {
    if (sessions.length > 0) {
      const key = currentUser ? `cortex_sessions_user_${currentUser.id}` : `cortex_sessions_guest`;
      localStorage.setItem(key, JSON.stringify(sessions));
    }
  }, [sessions, currentUser]);

  const handleNewChat = () => {
    const freshSession: ChatSession = {
      id: `session-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
      title: "New Chat",
      messages: [
        {
          id: "welcome",
          sender: "assistant",
          text: "Welcome to Cortex Workspace. I can help search files, scan system configurations, and run code analyses. Try asking a question below!",
          timestamp: new Date().toLocaleTimeString(),
        }
      ],
      createdAt: new Date().toISOString()
    };
    setSessions(prev => [freshSession, ...prev]);
    setActiveSessionId(freshSession.id);
    setActiveTab("chat");
  };

  const deleteSession = (idToDelete: string) => {
    const updated = sessions.filter(s => s.id !== idToDelete);
    if (updated.length === 0) {
      createFreshSession();
    } else {
      setSessions(updated);
      if (activeSessionId === idToDelete) {
        setActiveSessionId(updated[0].id);
      }
    }
  };

  const renameSession = (idToRename: string, newTitle: string) => {
    if (!newTitle.trim()) return;
    setSessions(prev => prev.map(s => s.id === idToRename ? { ...s, title: newTitle.trim() } : s));
  };

  // Admin: load user accounts list
  const loadUsers = async () => {
    setLoadingUsers(true);
    setAdminError(null);
    try {
      const users = await getUsers();
      setUsersList(users);
    } catch (err: any) {
      setAdminError(err.response?.data?.detail || "Failed to load users list.");
    } finally {
      setLoadingUsers(false);
    }
  };

  useEffect(() => {
    if (activeTab === "admin" && currentUser?.role === "admin") {
      loadUsers();
    }
  }, [activeTab, currentUser]);

  const startEdit = (user: User) => {
    setEditingUserId(user.id);
    setEditEmail(user.email);
    setEditFullName(user.full_name);
    setEditRole(user.role);
  };

  const cancelEdit = () => {
    setEditingUserId(null);
  };

  const handleUpdateUser = async (userId: number) => {
    try {
      await updateUser(userId, editEmail, editFullName, editRole);
      setEditingUserId(null);
      await loadUsers();
      if (userId === currentUser?.id) {
        const updatedMe = await getMe();
        setCurrentUser(updatedMe);
      }
    } catch (err: any) {
      setAdminError(err.response?.data?.detail || "Failed to update user.");
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (userId === currentUser?.id) {
      setAdminError("Cannot delete yourself!");
      return;
    }
    if (!window.confirm("Are you sure you want to delete this user?")) {
      return;
    }
    try {
      await deleteUser(userId);
      await loadUsers();
    } catch (err: any) {
      setAdminError(err.response?.data?.detail || "Failed to delete user.");
    }
  };

  // Load executions list
  const loadExecutionsList = async (showLoading = false) => {
    if (showLoading) setLoadingExecutions(true);
    try {
      const data = await listExecutions();
      setExecutions(data);
    } catch (err) {
      setError("Failed to load execution telemetry.");
    } finally {
      if (showLoading) setLoadingExecutions(false);
    }
  };

  useEffect(() => {
    loadExecutionsList(true);
  }, [token]);

  // Fetch replay details when selected execution changes
  useEffect(() => {
    if (!selectedExecution) {
      setExecutionData(null);
      return;
    }

    const executionId = selectedExecution;
    let mounted = true;

    async function loadReplay() {
      setLoadingReplay(true);
      try {
        const data = await getExecutionReplay(executionId);
        if (!mounted) return;
        setExecutionData(data);
      } catch (err) {
        if (!mounted) return;
        setError("Failed to load execution replay.");
        setExecutionData(null);
      } finally {
        if (mounted) setLoadingReplay(false);
      }
    }

    loadReplay();
    return () => {
      mounted = false;
    };
  }, [selectedExecution]);

  // Handle Authentication actions
  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);

    try {
      if (authMode === "login") {
        const data = await login(authEmail, authPassword);
        setToken(data.access_token);
        setAuthMode("none");
        setActiveTab("chat");
        clearAuthForm();
      } else if (authMode === "register") {
        await register(authEmail, authFullName, authPassword);
        // Automatically login after registration
        const data = await login(authEmail, authPassword);
        setToken(data.access_token);
        setAuthMode("none");
        setActiveTab("chat");
        clearAuthForm();
      }
    } catch (err: any) {
      setAuthError(err.response?.data?.detail || "Authentication request failed.");
    }
  };

  const handleLogoutClick = () => {
    logout();
    setToken(null);
    setCurrentUser(null);
    setActiveTab("chat");
    loadExecutionsList(true);
  };

  const clearAuthForm = () => {
    setAuthEmail("");
    setAuthPassword("");
    setAuthFullName("");
    setAuthError(null);
  };

  // Handle Chat Queries
  const handleSendMessage = async (e?: React.FormEvent, customQuery?: string) => {
    if (e) e.preventDefault();
    const queryToSend = customQuery !== undefined ? customQuery : inputQuery;
    if (!queryToSend.trim() || isGenerating) return;

    setInputQuery("");
    setIsGenerating(true);
    setError(null);

    const activeSession = sessions.find(s => s.id === activeSessionId);
    if (!activeSession) return;

    const userMsg: ChatMessage = {
      id: Math.random().toString(36).substring(7),
      sender: "user",
      text: queryToSend,
      timestamp: new Date().toLocaleTimeString(),
    };

    const history: ChatTurn[] = activeSession.messages
      .filter((msg) => msg.id !== "welcome")
      .map((msg) => ({
        role: msg.sender,
        content: msg.text,
      }));

    const updatedMessages = [...activeSession.messages, userMsg];
    let newTitle = activeSession.title;
    
    // Auto-rename from "New Chat" on first query
    if (activeSession.title === "New Chat") {
      newTitle = queryToSend.length > 28 ? queryToSend.substring(0, 25).trim() + "..." : queryToSend;
    }

    setSessions(prev => prev.map(s => s.id === activeSessionId ? { ...s, title: newTitle, messages: updatedMessages } : s));

    try {
      const configWithKeys = {
        ...modelConfig,
        api_key: apiKey,
        api_base_url: apiBaseUrl
      };
      const result: AskResponse = await askQuestion(queryToSend, !!token, history, configWithKeys);

      const assistantMsg: ChatMessage = {
        id: Math.random().toString(36).substring(7),
        sender: "assistant",
        text: result.response,
        executionId: result.execution_id,
        timestamp: new Date().toLocaleTimeString(),
      };

      setSessions(prev => prev.map(s => s.id === activeSessionId ? { ...s, messages: [...updatedMessages, assistantMsg] } : s));

      // Automatically reload execution telemetry list and highlight the execution trace
      if (result.execution_id) {
        await loadExecutionsList();
        setSelectedExecution(result.execution_id);
        setShowTelemetry(true);
        setTelemetryTab("detail");
      }
    } catch (err: any) {
      if (err.response?.status === 422 && err.response?.data?.error === "model_not_installed") {
        setMissingModel(err.response.data.model);
        setIsGenerating(false);
        return;
      }
      setError("AI Gateway did not respond. Verify local LLM / Ollama server is running.");
      const errorMsg: ChatMessage = {
        id: Math.random().toString(36).substring(7),
        sender: "assistant",
        text: "Error: Failed to process query. Please check server logs.",
        timestamp: new Date().toLocaleTimeString(),
      };
      setSessions(prev => prev.map(s => s.id === activeSessionId ? { ...s, messages: [...updatedMessages, errorMsg] } : s));
    } finally {
      setIsGenerating(false);
    }
  };

  const inspectMsgExecution = (executionId: string) => {
    setSelectedExecution(executionId);
    setShowTelemetry(true);
    setTelemetryTab("detail");
  };

  const activeSession = sessions.find(s => s.id === activeSessionId);

  return (
    <div className={`app-shell ${isSidebarOpen ? "sidebar-open" : "sidebar-closed"}`}>
      {/* Collapsible Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-logo">C</div>
          <div className="brand-info">
            <h2>CORTEX</h2>
            <span className="brand-tagline">AI Operating System</span>
          </div>
        </div>

        <button className="btn new-chat-btn" onClick={handleNewChat}>
          <span className="plus-icon">+</span> New Chat
        </button>

        <div className="sidebar-sessions">
          <div className="sessions-header">Recent Chats</div>
          <div className="sessions-list">
            {sessions.map((session) => {
              const isActive = session.id === activeSessionId;
              const isRenaming = renamingId === session.id;

              return (
                <div
                  key={session.id}
                  className={`session-item ${isActive ? "active" : ""}`}
                >
                  {isRenaming ? (
                    <input
                      type="text"
                      className="session-rename-input"
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          renameSession(session.id, renameValue);
                          setRenamingId(null);
                        } else if (e.key === "Escape") {
                          setRenamingId(null);
                        }
                      }}
                      onBlur={() => {
                        renameSession(session.id, renameValue);
                        setRenamingId(null);
                      }}
                      autoFocus
                    />
                  ) : (
                    <>
                      <span className="chat-icon">💬</span>
                      <span
                        className="session-title"
                        onClick={() => {
                          setActiveSessionId(session.id);
                          setActiveTab("chat");
                        }}
                        onDoubleClick={() => {
                          setRenamingId(session.id);
                          setRenameValue(session.title);
                        }}
                      >
                        {session.title}
                      </span>
                      <div className="session-actions">
                        <button
                          className="session-action-btn edit-btn"
                          onClick={() => {
                            setRenamingId(session.id);
                            setRenameValue(session.title);
                          }}
                          title="Rename"
                        >
                          ✏️
                        </button>
                        <button
                          className="session-action-btn delete-btn"
                          onClick={() => deleteSession(session.id)}
                          title="Delete"
                        >
                          🗑️
                        </button>
                      </div>
                    </>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Model Configuration Panel */}
        <div className="model-config-section">
          <button
            className="model-config-toggle"
            onClick={() => setShowModelConfig(!showModelConfig)}
          >
            <span className="model-config-icon">⚙️</span>
            <span>Model Config</span>
            <span className="model-config-chevron">{showModelConfig ? "▲" : "▼"}</span>
          </button>

          {showModelConfig && (
            <div className="model-config-panel">
              <div className="config-group">
                <label className="config-label">🤖 Main LLM</label>
                <select
                  className="config-select"
                  value={modelConfig.llm_model}
                  onChange={e => updateModelConfig("llm_model", e.target.value)}
                >
                  <option value="qwen3:8b">Qwen3 8B (Q4_K_M)</option>
                  <option value="llama3">Llama 3 8B</option>
                  <option value="mistral">Mistral 7B</option>
                  <option value="codellama">CodeLlama 7B</option>
                  <option value="gemma2">Gemma 2 9B</option>
                  <option value="phi3">Phi-3 Mini</option>
                </select>
              </div>

              <div className="config-group">
                <label className="config-label">🧬 Embedding Model</label>
                <select
                  className="config-select"
                  value={modelConfig.embedding_model}
                  onChange={e => updateModelConfig("embedding_model", e.target.value)}
                >
                  <option value="BAAI/bge-small-en-v1.5">BGE Small EN v1.5</option>
                  <option value="all-MiniLM-L6-v2">MiniLM L6 v2</option>
                  <option value="all-mpnet-base-v2">MPNet Base v2</option>
                </select>
              </div>

              <div className="config-group">
                <label className="config-label">🗄️ Vector Database</label>
                <select
                  className="config-select"
                  value={modelConfig.vector_db}
                  onChange={e => updateModelConfig("vector_db", e.target.value)}
                >
                  <option value="FAISS">FAISS</option>
                </select>
              </div>

              <div className="config-group">
                <label className="config-label">⚡ Inference Engine</label>
                <select
                  className="config-select"
                  value={modelConfig.inference_engine}
                  onChange={e => updateModelConfig("inference_engine", e.target.value)}
                >
                  <option value="Ollama">Ollama (Local)</option>
                  <option value="API">External API</option>
                </select>
              </div>

              <div className="config-group">
                <label className="config-label">🌳 Code Parsing</label>
                <select
                  className="config-select"
                  value={modelConfig.code_parsing}
                  onChange={e => updateModelConfig("code_parsing", e.target.value)}
                >
                  <option value="Tree-sitter">Tree-sitter (AST)</option>
                  <option value="Plain">Plain (Overlap)</option>
                </select>
              </div>

              <div className="config-active-badge">
                <span className="badge-dot" />
                Active: <strong>{modelConfig.inference_engine}</strong> · <strong>{modelConfig.llm_model}</strong>
              </div>

              {modelConfig.inference_engine === "API" && (
                <div className="config-api-section">
                  <hr className="config-divider" />
                  <h4>🔑 External API Key</h4>
                  
                  <div className="config-group">
                    <label className="config-label">Base URL</label>
                    <input 
                      type="text"
                      className="config-input"
                      placeholder="https://api.openai.com/v1"
                      value={apiBaseUrl}
                      onChange={(e) => handleApiBaseUrlChange(e.target.value)}
                    />
                  </div>
                  
                  <div className="config-group">
                    <label className="config-label">API Key</label>
                    <div className="config-input-password-wrapper">
                      <input 
                        type={showApiKey ? "text" : "password"}
                        className="config-input"
                        placeholder="sk-..."
                        value={apiKey}
                        onChange={(e) => handleApiKeyChange(e.target.value)}
                      />
                      <button 
                        type="button"
                        className="toggle-password-btn"
                        onClick={() => setShowApiKey(!showApiKey)}
                      >
                        {showApiKey ? "👁️" : "👁️‍🗨️"}
                      </button>
                    </div>
                  </div>
                  
                  {token ? (
                    <button 
                      type="button" 
                      className="btn btn-save-keys" 
                      onClick={handleSaveSettings}
                      disabled={settingsLoading}
                    >
                      {settingsLoading ? "Saving..." : "Save Credentials"}
                    </button>
                  ) : (
                    <div className="guest-keys-notice">
                      ⚠️ Stored locally for this session. Sign in to save permanently.
                    </div>
                  )}
                  {settingsSavedMessage && (
                    <div className="settings-saved-msg">
                      {settingsSavedMessage}
                    </div>
                  )}
                </div>
              )}

              {modelConfig.inference_engine === "Ollama" && (
                <>
                  <hr className="config-divider" />
                  
                  {/* Installed Model Library */}
                  <div className="model-library-section">
                    <h4>🗃️ Installed Models</h4>
                    {loadingModels ? (
                      <div className="library-loading">Loading list...</div>
                    ) : installedModels.length === 0 ? (
                      <div className="library-empty">No local models found.</div>
                    ) : (
                      <div className="installed-models-list">
                        {installedModels.map((model) => (
                          <div key={model.name} className="model-library-row">
                            <div className="model-library-info">
                              <span className="model-lib-name" title={model.name}>{model.name}</span>
                              <span className="model-lib-size">{(model.size / (1024 * 1024 * 1024)).toFixed(2)} GB</span>
                            </div>
                            {currentUser?.role === "admin" && (
                              <button 
                                type="button"
                                className="delete-model-btn"
                                onClick={() => handleDeleteModel(model.name)}
                                title="Delete model"
                              >
                                🗑️
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Curated Download List */}
                  <div className="model-download-section">
                    <h4>📥 Download Popular Models</h4>
                    <div className="available-download-list">
                      {curatedModels
                        .filter(cur => !installedModels.some(inst => inst.name === cur.id || inst.name.startsWith(cur.id + ":")))
                        .map(cur => (
                          <div key={cur.id} className="model-download-row">
                            <span className="model-dl-name">{cur.name}</span>
                            <button 
                              type="button"
                              className="btn-download-model"
                              onClick={() => handlePullModel(cur.id)}
                              title="Download"
                            >
                              ⬇️
                            </button>
                          </div>
                        ))
                      }
                      {curatedModels.filter(cur => !installedModels.some(inst => inst.name === cur.id || inst.name.startsWith(cur.id + ":"))).length === 0 && (
                        <div className="library-empty">All popular models installed!</div>
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        <div className="sidebar-footer">
          {currentUser ? (
            <div className="user-profile-card">
              <div className="user-avatar">{currentUser.full_name[0].toUpperCase()}</div>
              <div className="user-details">
                <span className="user-name">{currentUser.full_name}</span>
                <span className="user-role-badge">{currentUser.role}</span>
              </div>
              <button className="logout-icon-btn" onClick={handleLogoutClick} title="Sign Out">
                🚪
              </button>
            </div>
          ) : (
            <div className="sidebar-auth-prompt">
              <div className="guest-badge">Guest Mode (Local)</div>
              <div className="auth-btn-row">
                <button className="btn btn-signin" onClick={() => setAuthMode("login")}>
                  Sign In
                </button>
                <button className="btn btn-signup" onClick={() => setAuthMode("register")}>
                  Sign Up
                </button>
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* Main Container */}
      <div className="main-layout">
        {/* Topbar */}
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="sidebar-toggle-btn"
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              title={isSidebarOpen ? "Hide Sidebar" : "Show Sidebar"}
            >
              {isSidebarOpen ? "◀" : "▶"}
            </button>
            
            {activeTab === "chat" && activeSession && (
              <div className="topbar-session-title">
                {renamingId === activeSession.id ? (
                  <input
                    type="text"
                    className="topbar-rename-input"
                    value={renameValue}
                    onChange={(e) => setRenameValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        renameSession(activeSession.id, renameValue);
                        setRenamingId(null);
                      } else if (e.key === "Escape") {
                        setRenamingId(null);
                      }
                    }}
                    onBlur={() => {
                      renameSession(activeSession.id, renameValue);
                      setRenamingId(null);
                    }}
                    autoFocus
                  />
                ) : (
                  <>
                    <h2>{activeSession.title}</h2>
                    <button
                      className="edit-session-title-btn"
                      onClick={() => {
                        setRenamingId(activeSession.id);
                        setRenameValue(activeSession.title);
                      }}
                    >
                      ✏️
                    </button>
                  </>
                )}
              </div>
            )}

            {activeTab === "admin" && <h2>Admin User Console</h2>}
          </div>

          <div className="topbar-actions">
            {currentUser?.role === "admin" && (
              <div className="admin-tab-toggle-container">
                <button
                  className={`tab-btn ${activeTab === "chat" ? "active" : ""}`}
                  onClick={() => setActiveTab("chat")}
                >
                  Chat Console
                </button>
                <button
                  className={`tab-btn ${activeTab === "admin" ? "active" : ""}`}
                  onClick={() => setActiveTab("admin")}
                >
                  Admin Console
                </button>
              </div>
            )}

            <button
              className={`telemetry-toggle-btn ${showTelemetry ? "active" : ""}`}
              onClick={() => setShowTelemetry(!showTelemetry)}
            >
              📊 {showTelemetry ? "Telemetry: Open" : "Telemetry: Closed"}
            </button>
          </div>
        </header>

        {error ? <div className="banner error">{error}</div> : null}

        <div className="workspace-container">
          <main className="workspace-main-panel">
            {activeTab === "chat" && (
              <div className="chat-container">
                <div className="chat-scroll-area">
                  {activeSession && activeSession.messages.length <= 1 ? (
                    <div className="chat-empty-state">
                      <div className="cortex-logo-container">
                        <div className="cortex-logo">C</div>
                        <h1>Cortex Workspace</h1>
                        <p>How can I help you manage, search, and audit your code today?</p>
                      </div>

                      <div className="quick-cards-grid">
                        {QUICK_CARDS.map((card, idx) => (
                          <button
                            key={idx}
                            type="button"
                            className="quick-card"
                            onClick={(e) => handleSendMessage(e, card.prompt)}
                          >
                            <span className="quick-card-icon">{card.icon}</span>
                            <div className="quick-card-info">
                              <h3>{card.title}</h3>
                              <p>{card.desc}</p>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="chat-messages">
                      {activeSession && activeSession.messages.map((msg) => (
                        <div key={msg.id} className={`chat-bubble-container ${msg.sender}`}>
                          <div className="chat-avatar">
                            {msg.sender === "user" ? "U" : "C"}
                          </div>
                          <div className="chat-bubble">
                            <div className="chat-bubble-header">
                              <strong>{msg.sender === "user" ? "You" : "Cortex Assistant"}</strong>
                              <span className="chat-time">{msg.timestamp}</span>
                            </div>
                            {renderMessageText(msg.text)}
                            {msg.executionId && (
                              <div className="chat-bubble-actions">
                                <button
                                  className="inspect-trace-btn"
                                  onClick={() => inspectMsgExecution(msg.executionId!)}
                                >
                                  🔍 Inspect Execution Trace
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                      {isGenerating && (
                        <div className="chat-bubble-container assistant">
                          <div className="chat-avatar">C</div>
                          <div className="chat-bubble typing">
                            <div className="typing-dots">
                              <span></span>
                              <span></span>
                              <span></span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <form onSubmit={(e) => handleSendMessage(e)} className="chat-input-form">
                  <input
                    type="text"
                    placeholder={
                      token
                        ? "Ask assistant to run tools, review logs or explain codes..."
                        : "Guest Mode: Ask anything..."
                    }
                    value={inputQuery}
                    onChange={(e) => setInputQuery(e.target.value)}
                    disabled={isGenerating}
                  />
                  <button type="submit" disabled={isGenerating || !inputQuery.trim()}>
                    {isGenerating ? "Routing..." : "Send"}
                  </button>
                </form>
              </div>
            )}

            {activeTab === "admin" && currentUser?.role === "admin" && (
              <div className="admin-container">
                <div className="panel-heading">
                  <h2>User Records Management</h2>
                  <button className="refresh-telemetry-btn" onClick={loadUsers}>
                    ↻
                  </button>
                </div>

                {adminError && <div className="banner error">{adminError}</div>}

                {loadingUsers ? (
                  <div className="empty-state">Loading user records...</div>
                ) : (
                  <div className="admin-table-container">
                    <table className="admin-table">
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Full Name</th>
                          <th>Email Address</th>
                          <th>Role</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {usersList.map((user) => {
                          const isEditing = editingUserId === user.id;

                          return (
                            <tr key={user.id} className={isEditing ? "editing-row" : ""}>
                              <td>{user.id}</td>
                              <td>
                                {isEditing ? (
                                  <input
                                    type="text"
                                    className="admin-edit-input"
                                    value={editFullName}
                                    onChange={(e) => setEditFullName(e.target.value)}
                                  />
                                ) : (
                                  user.full_name
                                )}
                              </td>
                              <td>
                                {isEditing ? (
                                  <input
                                    type="email"
                                    className="admin-edit-input"
                                    value={editEmail}
                                    onChange={(e) => setEditEmail(e.target.value)}
                                  />
                                ) : (
                                  user.email
                                )}
                              </td>
                              <td>
                                {isEditing ? (
                                  <select
                                    className="admin-edit-select"
                                    value={editRole}
                                    onChange={(e) => setEditRole(e.target.value)}
                                  >
                                    <option value="user">User</option>
                                    <option value="admin">Admin</option>
                                  </select>
                                ) : (
                                  <span className={`role-badge role-${user.role}`}>
                                    {user.role}
                                  </span>
                                )}
                              </td>
                              <td>
                                {isEditing ? (
                                  <div className="admin-action-buttons">
                                    <button
                                      className="btn btn-save"
                                      onClick={() => handleUpdateUser(user.id)}
                                    >
                                      Save
                                    </button>
                                    <button className="btn btn-cancel" onClick={cancelEdit}>
                                      Cancel
                                    </button>
                                  </div>
                                ) : (
                                  <div className="admin-action-buttons">
                                    <button className="btn btn-edit" onClick={() => startEdit(user)}>
                                      Edit
                                    </button>
                                    {user.id !== currentUser?.id && (
                                      <button
                                        className="btn btn-delete"
                                        onClick={() => handleDeleteUser(user.id)}
                                      >
                                        Delete
                                      </button>
                                    )}
                                  </div>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </main>

          {/* Telemetry drawer panel on the right */}
          {showTelemetry && (
            <aside className="panel telemetry-panel">
              <div className="telemetry-header">
                <div className="telemetry-tabs">
                  <button
                    className={`telemetry-tab-btn ${telemetryTab === "list" ? "active" : ""}`}
                    onClick={() => setTelemetryTab("list")}
                  >
                    Traces
                  </button>
                  <button
                    className={`telemetry-tab-btn ${telemetryTab === "detail" ? "active" : ""}`}
                    onClick={() => setTelemetryTab("detail")}
                    disabled={!selectedExecution}
                  >
                    Active Trace
                  </button>
                </div>
                <button className="close-telemetry-btn" onClick={() => setShowTelemetry(false)}>
                  ✕
                </button>
              </div>

              {telemetryTab === "list" ? (
                <div className="telemetry-list-container">
                  <div className="panel-heading">
                    <h2>Telemetry Runs</h2>
                    <button className="refresh-telemetry-btn" onClick={() => loadExecutionsList(true)}>
                      ↻
                    </button>
                  </div>

                  <div className="list">
                    {executions.map((item) => {
                      const isActive = item.execution_id === selectedExecution;

                      return (
                        <button
                          key={item.execution_id}
                          type="button"
                          className={`execution-card ${isActive ? "active" : ""}`}
                          onClick={() => {
                            setSelectedExecution(item.execution_id);
                            setTelemetryTab("detail");
                          }}
                        >
                          <div className="execution-card__top">
                            <span className="execution-id">{item.execution_id.slice(0, 13)}...</span>
                            <span className={`status-pill status-${item.status}`}>{item.status}</span>
                          </div>

                          <div className="execution-card__meta">
                            <span>{item.event_count ?? 0} events</span>
                            <span>{item.summary?.steps_executed ?? 0} steps</span>
                          </div>

                          <div className="execution-card__footer">
                            <span>{item.summary?.tools_used?.length ?? 0} tools</span>
                            <span>{item.last_timestamp ? new Date(item.last_timestamp).toLocaleTimeString() : "No time"}</span>
                          </div>
                        </button>
                      );
                    })}

                    {!loadingExecutions && executions.length === 0 ? (
                      <div className="empty-state">No telemetry traces found. Run a chat query to generate logs.</div>
                    ) : null}
                  </div>
                </div>
              ) : (
                <div className="telemetry-detail-container">
                  {!executionData ? (
                    <div className="empty-state">
                      {loadingReplay ? "Loading trace timeline..." : "Select a trace from the Traces tab."}
                    </div>
                  ) : (
                    <div className="inspector-and-replay">
                      <div className="inspector-summary">
                        <div className="inspector-row-group">
                          <div className="inspector-stat">
                            <label>Status</label>
                            <span className={`status-pill status-${executionData.status}`}>{executionData.status}</span>
                          </div>
                          <div className="inspector-stat">
                            <label>Duration</label>
                            <span className="stat-val">
                              {executionData.summary?.duration_ms != null
                                ? `${(executionData.summary.duration_ms / 1000).toFixed(2)}s`
                                : "0.00s"}
                            </span>
                          </div>
                        </div>

                        <div className="inspector-row-group">
                          <div className="inspector-stat">
                            <label>Steps</label>
                            <span className="stat-val">{executionData.summary?.steps_executed ?? 0}</span>
                          </div>
                          <div className="inspector-stat">
                            <label>Errors</label>
                            <span className={`stat-val ${executionData.summary?.error_count ? "text-danger" : ""}`}>
                              {executionData.summary?.error_count ?? 0}
                            </span>
                          </div>
                        </div>

                        <div className="inspector-card">
                          <label>Resolved Agent Tools</label>
                          <div className="chips">
                            {(executionData.summary?.tools_used ?? []).length > 0 ? (
                              executionData.summary.tools_used?.map((tool) => (
                                <span key={tool} className="chip">
                                  {tool}
                                </span>
                              ))
                            ) : (
                              <span className="muted">No tools invoked.</span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="timeline-section">
                        <h3>Step-by-Step Replay</h3>
                        <div className="timeline">
                          {executionData.replay.map((step) => (
                            <article key={step.step} className="timeline-item">
                              <div className="timeline-item__head">
                                <div className="timeline-step-badge">Step {step.step}</div>
                                <strong>{step.action}</strong>
                                <span className="timeline-time">
                                  {step.raw?.timestamp ? new Date(step.raw.timestamp).toLocaleTimeString() : "Unknown"}
                                </span>
                              </div>

                              <div className="timeline-item__body">
                                <div className="timeline-meta-row">
                                  <span className="meta-label">Type:</span>
                                  <span className="meta-value font-mono">{step.raw?.type ?? "event"}</span>
                                </div>
                                <div className="timeline-meta-row">
                                  <span className="meta-label">Source:</span>
                                  <span className="meta-value font-mono">{step.raw?.source ?? "system"}</span>
                                </div>
                                {step.raw?.human_readable && (
                                  <div className="timeline-explanation">
                                    <p>{step.raw.human_readable}</p>
                                  </div>
                                )}
                              </div>
                            </article>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </aside>
          )}
        </div>
      </div>

      {/* Premium Glassmorphism Auth Modals */}
      {authMode !== "none" && (
        <div className="auth-overlay">
          <div className="auth-modal">
            <div className="auth-modal-header">
              <h2>{authMode === "login" ? "Welcome Back to Cortex" : "Create Developer Profile"}</h2>
              <button className="auth-close-btn" onClick={() => { setAuthMode("none"); clearAuthForm(); }}>
                ✕
              </button>
            </div>

            {authError && <div className="banner error auth-error">{authError}</div>}

            <form onSubmit={handleAuthSubmit} className="auth-form">
              {authMode === "register" && (
                <div className="form-group">
                  <label htmlFor="fullName">Full Name</label>
                  <input
                    id="fullName"
                    type="text"
                    required
                    placeholder="Ada Lovelace"
                    value={authFullName}
                    onChange={(e) => setAuthFullName(e.target.value)}
                  />
                </div>
              )}

              <div className="form-group">
                <label htmlFor="email">Email Address</label>
                <input
                  id="email"
                  type="email"
                  required
                  placeholder="developer@cortex.local"
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="password">Password (min. 8 characters)</label>
                <input
                  id="password"
                  type="password"
                  required
                  minLength={8}
                  placeholder="••••••••"
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                />
              </div>

              <button type="submit" className="btn auth-submit-btn">
                {authMode === "login" ? "Authenticate Profile" : "Register Credentials"}
              </button>
            </form>

            <div className="auth-modal-footer">
              {authMode === "login" ? (
                <p>
                  New developer?{" "}
                  <button className="toggle-auth-link" onClick={() => { setAuthMode("register"); setAuthError(null); }}>
                    Create account credentials
                  </button>
                </p>
              ) : (
                <p>
                  Already registered?{" "}
                  <button className="toggle-auth-link" onClick={() => { setAuthMode("login"); setAuthError(null); }}>
                    Sign in with existing credentials
                  </button>
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Pull Progress Overlay Modal */}
      {pullingModelName && (
        <div className="pull-overlay">
          <div className="pull-modal">
            <div className="pull-modal-header">
              <h3>Downloading Model</h3>
            </div>
            <div className="pull-modal-body">
              <p className="pull-model-name">Model: <strong>{pullingModelName}</strong></p>
              {pullProgress && (
                <>
                  <div className="progress-bar-container">
                    <div 
                      className="progress-bar-fill" 
                      style={{ width: `${pullProgress.percent}%` }}
                    />
                  </div>
                  <div className="pull-status-row">
                    <span className="pull-status-text">{pullProgress.status}</span>
                    <span className="pull-percent">{pullProgress.percent}%</span>
                  </div>
                </>
              )}
            </div>
            <div className="pull-modal-actions">
              {pullProgress?.status.startsWith("Error:") || pullProgress?.status === "success" || pullProgress?.percent === 100 || !pullProgress ? (
                <button 
                  type="button"
                  className="btn btn-close-pull" 
                  onClick={() => {
                    setPullingModelName(null);
                    setPullProgress(null);
                  }}
                >
                  Close
                </button>
              ) : (
                <div className="pulling-spinner-row">
                  <span className="pulling-indicator">Downloading, please do not close this window...</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Missing Model Prompt Modal */}
      {missingModel && (
        <div className="missing-model-overlay">
          <div className="missing-model-modal">
            <div className="missing-model-header">
              <h3>Model Required</h3>
            </div>
            <div className="missing-model-body">
              <p>The selected model <strong>{missingModel}</strong> is not currently installed in your Ollama library.</p>
              <p>Would you like to download it now or switch to another model?</p>
            </div>
            <div className="missing-model-actions">
              <button 
                type="button" 
                className="btn btn-download-now" 
                onClick={() => {
                  const modelToPull = missingModel;
                  setMissingModel(null);
                  handlePullModel(modelToPull);
                }}
              >
                Download Now
              </button>
              <button 
                type="button" 
                className="btn btn-switch-model" 
                onClick={() => {
                  setMissingModel(null);
                  setShowModelConfig(true);
                }}
              >
                Switch Model
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
