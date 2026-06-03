import { useEffect, useState } from "react";
import "./App.css";
import { getExecutionReplay, listExecutions } from "./api/execution";
import { getMe, login, register, logout } from "./api/auth";
import { askQuestion, type AskResponse } from "./api/ai";

type User = {
  id: number;
  email: string;
  full_name: string;
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

  // AI Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      sender: "assistant",
      text: "Welcome to Cortex Workspace. I can help search files, scan system configurations, and run code analyses. Try asking a question below!",
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState<"chat" | "replay">("chat");

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
        clearAuthForm();
      } else if (authMode === "register") {
        await register(authEmail, authFullName, authPassword);
        // Automatically login after registration
        const data = await login(authEmail, authPassword);
        setToken(data.access_token);
        setAuthMode("none");
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
    loadExecutionsList(true);
  };

  const clearAuthForm = () => {
    setAuthEmail("");
    setAuthPassword("");
    setAuthFullName("");
    setAuthError(null);
  };

  // Handle Chat Queries
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || isGenerating) return;

    const userQuery = inputQuery;
    setInputQuery("");
    setIsGenerating(true);
    setError(null);

    // Add user message to log
    const userMsg: ChatMessage = {
      id: Math.random().toString(36).substring(7),
      sender: "user",
      text: userQuery,
      timestamp: new Date().toLocaleTimeString(),
    };
    setChatMessages((prev) => [...prev, userMsg]);

    try {
      const result: AskResponse = await askQuestion(userQuery, !!token);

      const assistantMsg: ChatMessage = {
        id: Math.random().toString(36).substring(7),
        sender: "assistant",
        text: result.response,
        executionId: result.execution_id,
        timestamp: new Date().toLocaleTimeString(),
      };
      setChatMessages((prev) => [...prev, assistantMsg]);

      // Automatically reload execution telemetry list and highlight the execution trace
      if (result.execution_id) {
        await loadExecutionsList();
        setSelectedExecution(result.execution_id);
      }
    } catch (err: any) {
      setError("AI Gateway did not respond. Verify local LLM / Ollama server is running.");
      const errorMsg: ChatMessage = {
        id: Math.random().toString(36).substring(7),
        sender: "assistant",
        text: "Error: Failed to process query. Please check server logs.",
        timestamp: new Date().toLocaleTimeString(),
      };
      setChatMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsGenerating(false);
    }
  };

  const inspectMsgExecution = (executionId: string) => {
    setSelectedExecution(executionId);
    setActiveTab("replay");
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-section">
          <p className="eyebrow">Cortex Workspace</p>
          <h1>Execution Intelligence Console</h1>
          <p className="subtitle">
            Local-first AI operating system, execution replay, and repo intelligence.
          </p>
        </div>

        <div className="user-controls">
          {currentUser ? (
            <div className="user-profile">
              <div className="user-avatar">{currentUser.full_name[0].toUpperCase()}</div>
              <div className="user-details">
                <span className="user-name">{currentUser.full_name}</span>
                <span className="user-email">{currentUser.email}</span>
              </div>
              <button className="btn logout-button" onClick={handleLogoutClick}>
                Sign Out
              </button>
            </div>
          ) : (
            <div className="auth-actions">
              <span className="anonymous-badge">Guest Mode (Ask-only)</span>
              <button className="btn login-trigger" onClick={() => setAuthMode("login")}>
                Sign In
              </button>
              <button className="btn register-trigger" onClick={() => setAuthMode("register")}>
                Create Account
              </button>
            </div>
          )}
        </div>
      </header>

      {error ? <div className="banner error">{error}</div> : null}

      <main className="workspace">
        {/* Left Column: Executions Telemetry Log */}
        <section className="panel list-panel">
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
                  onClick={() => setSelectedExecution(item.execution_id)}
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
        </section>

        {/* Center Column: Toggleable Chat Console vs Execution Replay */}
        <section className="panel center-panel">
          <div className="panel-tabs">
            <button
              className={`tab-button ${activeTab === "chat" ? "active" : ""}`}
              onClick={() => setActiveTab("chat")}
            >
              Chat Console
            </button>
            <button
              className={`tab-button ${activeTab === "replay" ? "active" : ""}`}
              onClick={() => setActiveTab("replay")}
              disabled={!selectedExecution}
            >
              Replay Timeline {!selectedExecution && "(None Selected)"}
            </button>
          </div>

          {activeTab === "chat" ? (
            <div className="chat-container">
              <div className="chat-messages">
                {chatMessages.map((msg) => (
                  <div key={msg.id} className={`chat-bubble-container ${msg.sender}`}>
                    <div className="chat-bubble">
                      <div className="chat-bubble-header">
                        <strong>{msg.sender === "user" ? "You" : "Cortex Assistant"}</strong>
                        <span className="chat-time">{msg.timestamp}</span>
                      </div>
                      <div className="chat-bubble-text">{msg.text}</div>
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

              <form onSubmit={handleSendMessage} className="chat-input-form">
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
          ) : (
            <div className="replay-container">
              <div className="panel-heading">
                <h2>Execution step-by-step replay</h2>
                <span className="execution-id-subtitle">ID: {selectedExecution}</span>
              </div>

              {!executionData ? (
                <div className="empty-state">
                  {loadingReplay ? "Loading trace timeline..." : "Select an execution telemetry run on the left."}
                </div>
              ) : (
                <div className="timeline">
                  {executionData.replay.map((step) => (
                    <article key={step.step} className="timeline-item">
                      <div className="timeline-item__head">
                        <div className="timeline-step-badge">Step {step.step}</div>
                        <strong>{step.action}</strong>
                        <span className="timeline-time">{step.raw?.timestamp ? new Date(step.raw.timestamp).toLocaleTimeString() : "Unknown"}</span>
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
              )}
            </div>
          )}
        </section>

        {/* Right Column: Telemetry Inspector */}
        <section className="panel inspector-panel">
          <div className="panel-heading">
            <h2>Inspector Dashboard</h2>
            <span className={`status-pill status-${executionData?.status ?? "idle"}`}>
              {executionData?.status ?? "Idle"}
            </span>
          </div>

          {!executionData ? (
            <div className="empty-state">No execution run selected for inspection.</div>
          ) : (
            <div className="inspector">
              <div className="inspector-card">
                <label>Execution Identity</label>
                <p className="font-mono selectable-id">{executionData.execution_id}</p>
              </div>

              <div className="inspector-card">
                <label>Execution Status</label>
                <p className="capitalize-text">{executionData.status}</p>
              </div>

              <div className="inspector-card-group">
                <div className="inspector-card half">
                  <label>Total Steps</label>
                  <p className="large-stat">{executionData.summary?.steps_executed ?? 0}</p>
                </div>

                <div className="inspector-card half">
                  <label>Errors</label>
                  <p className={`large-stat ${executionData.summary?.error_count ? "text-danger" : ""}`}>
                    {executionData.summary?.error_count ?? 0}
                  </p>
                </div>
              </div>

              <div className="inspector-card">
                <label>Tracer Duration</label>
                <p className="large-stat">
                  {executionData.summary?.duration_ms != null
                    ? `${(executionData.summary.duration_ms / 1000).toFixed(2)} s`
                    : "0.00 s"}
                </p>
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
                    <span className="muted">No tools invoked during execution.</span>
                  )}
                </div>
              </div>
            </div>
          )}
        </section>
      </main>

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
    </div>
  );
}

export default App;
