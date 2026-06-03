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

export async function getUsers() {
  const res = await api.get("/users");
  return res.data;
}

export async function updateUser(userId: number, email: string, fullName: string, role: string) {
  const res = await api.put(`/users/${userId}`, {
    email,
    full_name: fullName,
    role,
  });
  return res.data;
}

export async function deleteUser(userId: number) {
  const res = await api.delete(`/users/${userId}`);
  return res.data;
}
