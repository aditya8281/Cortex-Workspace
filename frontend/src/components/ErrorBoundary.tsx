import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button } from "@/components/ui/button";

type Props = { children: ReactNode };
type State = { error: Error | null };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Cortex UI error:", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 24,
            background: "#060a12",
            color: "#e8eef8",
            fontFamily: "system-ui, sans-serif",
          }}
        >
          <div style={{ maxWidth: 480, textAlign: "center" }}>
            <h1 style={{ fontSize: 20, marginBottom: 8 }}>Cortex hit a display error</h1>
            <p style={{ color: "#8b9cb8", fontSize: 14, marginBottom: 16 }}>
              {this.state.error.message}
            </p>
            <div style={{ display: "flex", gap: 8, justifyContent: "center", flexWrap: "wrap" }}>
              <Button
                onClick={() => {
                  localStorage.removeItem("cortex-chats");
                  localStorage.removeItem("cortex-app");
                  window.location.reload();
                }}
              >
                Reset local data
              </Button>
              <Button variant="secondary" onClick={() => this.setState({ error: null })}>
                Try again
              </Button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
