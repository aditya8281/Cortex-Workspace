import { useEffect, useState } from "react";
import "./App.css";
import { getExecutionReplay } from "./api/execution";

type Execution = any;

function App() {
  const [selectedExecution, setSelectedExecution] = useState<string | null>(null);
  const [executionData, setExecutionData] = useState<Execution | null>(null);

  // TEMP MOCK LIST (we will replace with real backend later)
  const executions = [
    { id: "exec_1" },
    { id: "exec_2" },
    { id: "exec_3" },
  ];

  useEffect(() => {
    if (!selectedExecution) return;

    async function load() {
      try {
        const data = await getExecutionReplay(selectedExecution);
        setExecutionData(data);
      } catch (err) {
        console.error("Failed to load execution:", err);
        setExecutionData(null);
      }
    }

    load();
  }, [selectedExecution]);

  return (
    <div className="cortex-shell">

      {/* LEFT PANEL */}
      <div className="panel left">
        <h3>Executions</h3>

        {executions.map((ex) => (
          <div
            key={ex.id}
            className="exec-item"
            onClick={() => setSelectedExecution(ex.id)}
          >
            {ex.id}
          </div>
        ))}
      </div>

      {/* CENTER PANEL */}
      <div className="panel center">
        <h3>Execution Timeline</h3>

        {!executionData ? (
          <div className="placeholder">
            Select an execution to load timeline
          </div>
        ) : (
          <div>
            {executionData.replay.map((step: any, idx: number) => (
              <div key={idx} className="timeline-step">
                <b>{step.action}</b>
                <div className="meta">
                  {step.raw?.type} | {step.raw?.timestamp}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* RIGHT PANEL */}
      <div className="panel right">
        <h3>Inspector</h3>

        {!executionData ? (
          <div className="placeholder">
            No execution selected
          </div>
        ) : (
          <div>
            <p><b>Execution ID:</b> {executionData.execution_id}</p>
            <p><b>Status:</b> {executionData.status}</p>

            <hr />

            <p><b>Tools Used:</b></p>
            {executionData.summary?.tools_used?.map((t: string) => (
              <div key={t}>{t}</div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}

export default App;