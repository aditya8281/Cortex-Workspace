import { api } from "./client";

export async function login(email: string, password: string) {
  const res = await api.post("/login", { email, password });
  const data = res.data;
  if (data.access_token) {
    localStorage.setItem("cortex_token", data.access_token);
  }
  return data;
}

export async function register(email: string, fullName: string, password: string) {
  const res = await api.post("/users", {
    email,
    full_name: fullName,
    password,
  });
  return res.data;
}

export async function getMe() {
  const res = await api.get("/me");
  return res.data;
}

export function logout() {
  localStorage.removeItem("cortex_token");
}
