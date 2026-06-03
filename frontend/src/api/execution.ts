import { api } from "./client";

export async function getExecution(executionId: string) {
  const res = await api.get(`/execution/${executionId}`);
  return res.data;
}

export async function getExecutionReplay(executionId: string) {
  const res = await api.get(`/execution/${executionId}/replay`);
  return res.data;
}

export async function getExecutionTools(executionId: string) {
  const res = await api.get(`/execution/${executionId}/tools`);
  return res.data;
}