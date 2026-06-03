import { api } from "./client";

export type AskResponse = {
  query: string;
  response: string;
  user_id: number | null;
  execution_id: string | null;
};

export async function askQuestion(query: string, useAuthenticatedChat = false): Promise<AskResponse> {
  const url = useAuthenticatedChat ? "/ai/chat" : "/ai/ask";
  const res = await api.post(url, { query });
  return res.data;
}
