import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { getExecutionReplay, listExecutions } from "./api/execution";

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

function App() {
  const [executions, setExecutions] = useState<ExecutionListItem[]>([]);
  const [selectedExecution, setSelectedExecution] = useState<string | null>(null);
  const [executionData, setExecutionData] = useState<ReplayData | null>(null);
  const [loadingExecutions, setLoadingExecutions] = useState(true);
  const [loadingReplay, setLoadingReplay] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadExecutions() {
      setLoadingExecutions(true);
      setError(null);

      try {
        const data = await listExecutions();

        if (!mounted) return;

        setExecutions(data);
      } catch (err) {
        if (!mounted) return;

        setError("Failed to load executions.");
        setExecutions([]);
      } finally {
        if (mounted) {
          setLoadingExecutions(false);
        }
      }
    }

    loadExecutions();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (executions.length === 0) {
      setSelectedExecution(null);
      return;
    }

    if (!selectedExecution || !executions.some((item) => item.execution_id === selectedExecution)) {
      setSelectedExecution(executions[0].execution_id);
    }
  }, [executions, selectedExecution]);

  useEffect(() => {
    if (!selectedExecution) {
      setExecutionData(null);
      return;
    }

    const executionId = selectedExecution;
    let mounted = true;

    async function loadReplay() {
      setLoadingReplay(true);
      setError(null);

      try {
        const data = await getExecutionReplay(executionId);

        if (!mounted) return;

        setExecutionData(data);
      } catch (err) {
        if (!mounted) return;

        setError("Failed to load execution replay.");
        setExecutionData(null);
      } finally {
        if (mounted) {
          setLoadingReplay(false);
        }
      }
    }

    loadReplay();

    return () => {
      mounted = false;
    };
  }, [selectedExecution]);

  const activeExecution = useMemo(
    () => executions.find((item) => item.execution_id === selectedExecution) ?? null,
    [executions, selectedExecution]
  );

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Cortex Workspace</p>
          <h1>Execution Intelligence Console</h1>
          <p className="subtitle">
            Local-first AI operating system, execution replay, and repo intelligence in one workspace.
          </p>
        </div>

        <button
          className="refresh-button"
          onClick={() => window.location.reload()}
          type="button"
        >
          Refresh
        </button>
      </header>

      {error ? <div className="banner error">{error}</div> : null}

      <main className="workspace">
        <section className="panel list-panel">
          <div className="panel-heading">
            <h2>Executions</h2>
            <span>{loadingExecutions ? "Loading" : `${executions.length} items`}</span>
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
                    <span className="execution-id">{item.execution_id}</span>
                    <span className={`status-pill status-${item.status}`}>{item.status}</span>
                  </div>

                  <div className="execution-card__meta">
                    <span>{item.event_count ?? 0} events</span>
                    <span>{item.summary?.steps_executed ?? 0} steps</span>
                  </div>

                  <div className="execution-card__footer">
                    <span>{item.summary?.tools_used?.length ?? 0} tools</span>
                    <span>{item.last_timestamp ? new Date(item.last_timestamp).toLocaleString() : "No timestamp"}</span>
                  </div>
                </button>
              );
            })}

            {!loadingExecutions && executions.length === 0 ? (
              <div className="empty-state">No executions have been recorded yet.</div>
            ) : null}
          </div>
        </section>

        <section className="panel timeline-panel">
          <div className="panel-heading">
            <h2>Timeline</h2>
            <span>{loadingReplay ? "Loading" : activeExecution?.execution_id ?? "No execution selected"}</span>
          </div>

          {!executionData ? (
            <div className="empty-state">
              {loadingReplay ? "Loading replay..." : "Select an execution to inspect the replay."}
            </div>
          ) : (
            <div className="timeline">
              {executionData.replay.map((step) => (
                <article key={step.step} className="timeline-item">
                  <div className="timeline-item__head">
                    <strong>{step.action}</strong>
                    <span>{step.raw?.timestamp ?? "Unknown time"}</span>
                  </div>

                  <div className="timeline-item__body">
                    <span>{step.raw?.type ?? "event"}</span>
                    <span>{step.raw?.source ?? "system"}</span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="panel inspector-panel">
          <div className="panel-heading">
            <h2>Inspector</h2>
            <span>{executionData?.status ?? "Idle"}</span>
          </div>

          {!executionData ? (
            <div className="empty-state">No execution selected.</div>
          ) : (
            <div className="inspector">
              <div className="inspector-card">
                <label>Execution ID</label>
                <p>{executionData.execution_id}</p>
              </div>

              <div className="inspector-card">
                <label>Status</label>
                <p>{executionData.status}</p>
              </div>

              <div className="inspector-card">
                <label>Steps</label>
                <p>{executionData.summary?.steps_executed ?? 0}</p>
              </div>

              <div className="inspector-card">
                <label>Errors</label>
                <p>{executionData.summary?.error_count ?? 0}</p>
              </div>

              <div className="inspector-card">
                <label>Duration</label>
                <p>
                  {executionData.summary?.duration_ms != null
                    ? `${executionData.summary.duration_ms} ms`
                    : "Unknown"}
                </p>
              </div>

              <div className="inspector-card">
                <label>Tools Used</label>
                <div className="chips">
                  {(executionData.summary?.tools_used ?? []).length > 0 ? (
                    executionData.summary.tools_used?.map((tool) => (
                      <span key={tool} className="chip">
                        {tool}
                      </span>
                    ))
                  ) : (
                    <span className="muted">None</span>
                  )}
                </div>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
