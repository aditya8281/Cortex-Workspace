/**
 * Catch-all proxy — forwards any /api/* request to the FastAPI backend.
 * Supports binary uploads (FormData/images) and binary responses (images/files).
 */

import { NextResponse, type NextRequest } from "next/server";

function getBackendBase(): string {
  const env = process.env.CORTEX_BACKEND_URL || process.env.NEXT_PUBLIC_API_BASE_URL;
  if (env && /^https?:\/\//.test(env)) return env.replace(/\/api\/v1\/?$/, "").replace(/\/$/, "");
  return "http://localhost:8000";
}

async function proxyRequest(request: NextRequest, path: string): Promise<NextResponse> {
  const bases = [getBackendBase(), "http://backend:8000", "http://localhost:8000"];

  const hasBody = request.method !== "GET" && request.method !== "HEAD" && request.method !== "DELETE";
  const body = hasBody ? await request.arrayBuffer() : undefined;
  const search = request.nextUrl.search || "";

  for (const base of bases) {
    try {
      const res = await fetch(`${base}${path}${search}`, {
        method: request.method,
        headers: {
          "Content-Type": request.headers.get("content-type") || "application/json",
          ...(request.headers.get("authorization") ? { Authorization: request.headers.get("authorization")! } : {}),
        },
        body: body !== undefined ? body : undefined,
        cache: "no-store",
      });
      const contentType = res.headers.get("content-type") || "";
      if (!contentType.includes("application/json")) {
        const buffer = await res.arrayBuffer();
        return new NextResponse(buffer, {
          status: res.status,
          headers: { "Content-Type": contentType, ...(res.headers.get("content-length") ? { "Content-Length": res.headers.get("content-length")! } : {}) },
        });
      }
      const data = await res.json().catch(() => null);
      return NextResponse.json(data, { status: res.status });
    } catch { continue; }
  }
  return NextResponse.json({ error: "Backend unavailable" }, { status: 502 });
}

export async function GET(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }): Promise<NextResponse> {
  const { path } = await params;
  return proxyRequest(request, `/api/${path.join("/")}`);
}

export async function POST(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }): Promise<NextResponse> {
  const { path } = await params;
  return proxyRequest(request, `/api/${path.join("/")}`);
}

export async function PUT(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }): Promise<NextResponse> {
  const { path } = await params;
  return proxyRequest(request, `/api/${path.join("/")}`);
}

export async function DELETE(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }): Promise<NextResponse> {
  const { path } = await params;
  return proxyRequest(request, `/api/${path.join("/")}`);
}

export async function PATCH(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }): Promise<NextResponse> {
  const { path } = await params;
  return proxyRequest(request, `/api/${path.join("/")}`);
}
