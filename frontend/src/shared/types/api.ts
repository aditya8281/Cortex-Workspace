// Shared API Types
export interface ApiResponse<T> {
  data: T;
  status: number;
}

export interface ApiError {
  code: string;
  message: string;
  details?: unknown;
}
