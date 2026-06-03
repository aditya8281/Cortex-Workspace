import { useEffect, useState } from "react";
import "./App.css";
import { getExecutionReplay, listExecutions } from "./api/execution";
import { getMe, login, register, logout } from "./api/auth";
import { askQuestion, type AskResponse, type ChatTurn } from "./api/ai";

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

    const history: ChatTurn[] = chatMessages
      .filter((msg) => msg.id !== "welcome")
      .map((msg) => ({
        role: msg.sender,
        content: msg.text,
      }));

    setChatMessages((prev) => [...prev, userMsg]);

    try {
      const result: AskResponse = await askQuestion(userQuery, !!token, history);

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
