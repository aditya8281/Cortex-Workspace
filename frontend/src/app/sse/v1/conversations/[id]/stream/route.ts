import { NextRequest } from "next/server";

const BACKEND_URL =
  process.env.CORTEX_BACKEND_URL || "http://localhost:8000";

/**
 * Proxies SSE stream from backend without Next.js rewrite buffering.
 *
 * The Next.js rewrite at /api/:path* buffers entire responses, breaking SSE.
 * This route handler lives at /sse/... (doesn't match the rewrite pattern)
 * and pipes the backend's ReadableStream through without buffering.
 *
 * Same-origin requests → cookies work → auth succeeds.
 * Server-side fetch → SameSite policy doesn't apply.
 */
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const backendUrl = `${BACKEND_URL}/api/v1/conversations/${id}/stream`;

  // Forward auth cookie + CSRF token from the original request
  const headers: Record<string, string> = {};
  const cookie = req.headers.get("cookie");
  if (cookie) headers["cookie"] = cookie;
  const csrf = req.headers.get("x-csrf-token");
  if (csrf) headers["x-csrf-token"] = csrf;

  const abortController = new AbortController();

  const response = await fetch(backendUrl, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    signal: abortController.signal,
  });

  if (!response.ok) {
    return new Response(`Backend stream error: ${response.status}`, {
      status: response.status,
    });
  }

  const body = response.body;
  if (!body) {
    return new Response("No response body from backend", { status: 502 });
  }

  // When the client disconnects, cancel the backend fetch
  req.signal.addEventListener("abort", () => {
    abortController.abort();
  });

  return new Response(body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
