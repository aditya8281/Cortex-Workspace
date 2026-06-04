"use client";

import React from "react";
import { Card, Button } from "@/components/ui/base";

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <Card className="max-w-md">
            <h2 className="text-xl font-bold text-danger mb-2">Something went wrong</h2>
            <p className="text-sm text-gray-400 mb-4">{this.state.error?.message}</p>
            <Button onClick={() => window.location.reload()}>Reload Page</Button>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}
