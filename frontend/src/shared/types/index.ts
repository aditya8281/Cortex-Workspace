export interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

export type LoadingState = "idle" | "loading" | "success" | "error";
