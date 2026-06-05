// Lightweight safety utilities to avoid common runtime crashes
export function safeGet<T = any>(obj: any, path: string | string[], fallback?: T): T | undefined {
  if (!obj) return fallback;
  const parts = Array.isArray(path) ? path : String(path).split(".");
  let cur: any = obj;
  for (const p of parts) {
    if (cur == null) return fallback;
    cur = cur[p];
  }
  return cur === undefined ? fallback : (cur as T);
}

export function tryParseJSON<T = any>(value: unknown, fallback?: T): T | undefined {
  if (value == null) return fallback;
  if (typeof value === "object") return value as T;
  try {
    return JSON.parse(String(value)) as T;
  } catch (e) {
    console.warn("Failed to parse JSON safely", e);
    return fallback;
  }
}

// Basic schema validator: shallow required keys check
export function validateResponseSchema(obj: any, requiredKeys: string[] = []): boolean {
  if (obj == null || typeof obj !== "object") return false;
  for (const k of requiredKeys) {
    if (!(k in obj)) return false;
  }
  return true;
}

export function createAbortController(): AbortController | undefined {
  try {
    return new AbortController();
  } catch (e) {
    return undefined;
  }
}
