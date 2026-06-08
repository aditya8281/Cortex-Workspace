/**
 * Catch-all proxy — forwards any /api/* request to the FastAPI backend.
 * This replaces individual proxy routes and ensures all endpoints work.
 */

import { NextResponse } from "next/server";

function getBackendBase() {
  const env = process.env.CORTEX_BACKEND_URL || process.env.NEXT_PUBLIC_API_BASE_URL;
  if (env && /^https?:\/\//.test(env)) return env.replace(/\/api\/v1\/?$/, "").replace(/\/$/, "");
  return "http://localhost:8000";
}

async function proxyRequest(request, path) {
  const bases = [getBackendBase(), "http://backend:8000", "http://localhost:8000"];
  const body = request.method !== "GET" && request.method !== "HEAD"
    ? await request.text()
    : undefined;
  const search = request.nextUrl.search || "";

  for (const base of bases) {
    try {
      const res = await fetch(`${base}${path}${search}`, {
        method: request.method,
        headers: {
          "Content-Type": request.headers.get("content-type") || "application/json",
          ...(request.headers.get("authorization") ? { Authorization: request.headers.get("authorization") } : {}),
        },
        body,
        cache: "no-store",
      });
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
