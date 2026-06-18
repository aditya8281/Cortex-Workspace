/**
 * Catch-all proxy — forwards any /api/* request to the FastAPI backend.
 * Supports binary uploads (FormData/images) and binary responses (images/files).
 */

import { NextResponse } from "next/server";

function getBackendBase() {
  const env = process.env.CORTEX_BACKEND_URL || process.env.NEXT_PUBLIC_API_BASE_URL;
  if (env && /^https?:\/\//.test(env)) return env.replace(/\/api\/v1\/?$/, "").replace(/\/$/, "");
  return "http://localhost:8000";
}

async function proxyRequest(request, path) {
  const bases = [getBackendBase(), "http://backend:8000", "http://localhost:8000"];

  // Read body as ArrayBuffer to preserve binary data (FormData, images, etc.)
  // Skip body for methods that never carry one (GET, HEAD, DELETE)
  const hasBody = request.method !== "GET" && request.method !== "HEAD" && request.method !== "DELETE";
  const body = hasBody ? await request.arrayBuffer() : undefined;

  const search = request.nextUrl.search || "";

  for (const base of bases) {
    try {
      const res = await fetch(`${base}${path}${search}`, {
        method: request.method,
        headers: {
          // Forward original Content-Type (includes multipart boundary for FormData)
          "Content-Type": request.headers.get("content-type") || "application/json",
          ...(request.headers.get("authorization")
            ? { Authorization: request.headers.get("authorization") }
            : {}),
        },
        body: body !== undefined ? body : undefined,
        cache: "no-store",
      });

      const contentType = res.headers.get("content-type") || "";

      // Binary response (images, files) — forward raw bytes
      if (!contentType.includes("application/json")) {
        const buffer = await res.arrayBuffer();
        return new NextResponse(buffer, {
          status: res.status,
          headers: {
            "Content-Type": contentType,
            ...(res.headers.get("content-length")
              ? { "Content-Length": res.headers.get("content-length") }
              : {}),
          },
        });
      }

      // JSON response
      const data = await res.json().catch(() => null);
      return NextResponse.json(data, { status: res.status });
    } catch {
      continue;
    }
  }
  return NextResponse.json({ error: "Backend unavailable" }, { status: 502 });
}

export async function GET(request, { params }) {
  const { path } = await params;
  return proxyRequest(request, `/api/${path.join("/")}`);
}

export async function POST(request, { params }) {
  const { path } = await params;
  return proxyRequest(request, `/api/${path.join("/")}`);
}

export async function PUT(request, { params }) {
  const { path } = await params;
  return proxyRequest(request, `/api/${path.join("/")}`);
}

export async function DELETE(request, { params }) {
  const { path } = await params;
  return proxyRequest(request, `/api/${path.join("/")}`);
}

export async function PATCH(request, { params }) {
  const { path } = await params;
  return proxyRequest(request, `/api/${path.join("/")}`);
}
