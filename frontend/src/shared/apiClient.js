import { getSessionToken } from "./auth/session";

export const PUBLIC_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "/api/v1";

function normalizeBase(base) {
  // if base is absolute URL, keep; otherwise keep relative
  return base.replace(/\/$/, "");
}

function buildHeaders(headers = {}) {
  const token = getSessionToken();
  const h = {
    "Content-Type": "application/json",
    ...headers,
  };
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

async function request(method, path, { body, headers, query } = {}) {
  const base = normalizeBase(PUBLIC_BASE);
  const cleanPath = path.replace(/^\/*/, "");
  const url = `${base}/${cleanPath}${query ? `?${new URLSearchParams(query)}` : ""}`;

  const opts = {
    method,
    headers: buildHeaders(headers),
  };

  if (body !== undefined) opts.body = JSON.stringify(body);

  const res = await fetch(url, opts);
  let data;
  try {
    data = await res.json();
  } catch (e) {
    data = null;
  }

  if (!res.ok) {
    const err = new Error(data?.detail || data?.error || `Request failed: ${res.status}`);
    err.status = res.status;
    err.body = data;
    throw err;
  }

  return data;
}

export const apiClient = {
  get: (path, opts) => request("GET", path, opts),
  post: (path, opts) => request("POST", path, opts),
  put: (path, opts) => request("PUT", path, opts),
  del: (path, opts) => request("DELETE", path, opts),
};

export default apiClient;
