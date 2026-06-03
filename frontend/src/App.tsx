import "./App.css";

function App() {
  return (
    <div className="cortex-shell">

      {/* LEFT PANEL */}
      <div className="panel left">
        <h3>Executions</h3>
        <div className="placeholder">
          No executions loaded
        </div>
      </div>

      {/* CENTER PANEL */}
      <div className="panel center">
        <h3>Execution Timeline</h3>
        <div className="placeholder">
          Select an execution to view graph + steps
        </div>
      </div>

      {/* RIGHT PANEL */}
      <div className="panel right">
        <h3>Inspector</h3>
        <div className="placeholder">
          Tool / Memory / LLM details
        </div>
      </div>

    </div>
  );
}

export default App;