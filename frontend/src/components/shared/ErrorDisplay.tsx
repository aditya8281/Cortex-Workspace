import React from "react";
import { Card } from "@/components/ui/base";
import { AlertCircle } from "lucide-react";

interface ErrorMessageProps {
  title?: string;
  message: string;
  onDismiss?: () => void;
}

export function ErrorMessage({ title = "Error", message, onDismiss }: ErrorMessageProps) {
  return (
    <Card className="bg-red-900/20 border border-danger p-4 flex items-start gap-3">
      <AlertCircle className="text-danger flex-shrink-0 mt-1" size={20} />
      <div className="flex-1">
        <h3 className="font-bold text-danger">{title}</h3>
        <p className="text-sm text-gray-300">{message}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-gray-400 hover:text-white transition-colors"
        >
          ✕
        </button>
      )}
    </Card>
  );
}

interface EmptyStateProps {
  title: string;
  message: string;
  action?: React.ReactNode;
}

export function EmptyState({ title, message, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <h3 className="text-lg font-medium text-white mb-2">{title}</h3>
      <p className="text-gray-400 mb-4">{message}</p>
      {action}
    </div>
  );
}
