"use client";

import { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Button, Card, Spinner } from "@/components/ui/base";
import { aiService } from "@/services/api/ai";
import { modelsService } from "@/services/api/models";
import { addMessage, setLoading } from "@/state/slices/chat";
import type { RootState } from "@/state/store";
import type { ChatMessage } from "@/types/api";
import { Send, Loader } from "lucide-react";

export default function ChatPage() {
  const dispatch = useDispatch();
  const { messages, loading, currentModel } = useSelector((state: RootState) => state.chat);
  const [query, setQuery] = useState("");
  const [models, setModels] = useState<any[]>([]);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const data = await modelsService.listAllModels();
        setModels(data);
      } catch (error) {
        console.error("Failed to fetch models:", error);
      }
    };
    fetchModels();
  }, []);

  const handleSendQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMessage: ChatMessage = {
      role: "user",
      content: query,
      timestamp: new Date().toISOString(),
    };
    dispatch(addMessage(userMessage));
    dispatch(setLoading(true));
    setQuery("");

    try {
      const response = await aiService.ask({
        query,
        llm_model: currentModel,
      });

      // Validate response
      if (!response || !response.response) {
        throw new Error("Invalid response from AI service");
      }

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.response,
        timestamp: new Date().toISOString(),
        execution_id: response.execution_id,
      };
      dispatch(addMessage(assistantMessage));
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : "Failed to get response";
      const errorMessage: ChatMessage = {
        role: "assistant",
        content: `Error: ${errorMsg}`,
        timestamp: new Date().toISOString(),
      };
      dispatch(addMessage(errorMessage));
      console.error("Query failed:", error);
    } finally {
      dispatch(setLoading(false));
    }
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Chat</h1>
        <select
          value={currentModel}
          onChange={(e) => {}}
          className="bg-surface border border-border px-4 py-2 rounded text-white"
        >
          {models.map((m) => (
            <option key={m.id} value={m.name}>
              {m.name}
            </option>
          ))}
        </select>
      </div>

      <Card className="h-96 overflow-y-auto space-y-4 p-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            Start a conversation...
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className={`p-3 rounded ${
                msg.role === "user" ? "bg-primary text-white ml-auto w-3/4" : "bg-surface text-gray-200 mr-auto w-3/4"
              }`}
            >
              <p className="text-sm">{msg.content}</p>
              <p className="text-xs mt-1 opacity-70">{new Date(msg.timestamp || "").toLocaleTimeString()}</p>
            </div>
          ))
        )}
        {loading && (
          <div className="flex items-center gap-2">
            <Spinner />
            <p className="text-gray-400">Thinking...</p>
          </div>
        )}
      </Card>

      <form onSubmit={handleSendQuery} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask anything about your workspace..."
          className="flex-1 bg-surface border border-border px-4 py-2 rounded text-white placeholder-gray-500 focus:outline-none focus:border-primary"
          disabled={loading}
        />
        <Button type="submit" loading={loading} size="md">
          <Send size={20} />
        </Button>
      </form>
    </div>
  );
}
