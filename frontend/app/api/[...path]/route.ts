/**
 * Catch-all proxy — forwards any /api/* request to the FastAPI backend.
 * Supports binary uploads (FormData/images) and binary responses (images/files).
 * Forwards Set-Cookie headers so auth cookies persist in the browser.
 */

import { NextResponse, type NextRequest } from "next/server";

function getBackendBase(): string {
  const env = process.env.CORTEX_BACKEND_URL || process.env.NEXT_PUBLIC_API_BASE_URL;
  if (env && /^https?:\/\//.test(env)) return env.replace(/\/api\/v1\/?$/, "").replace(/\/$/, "");
  return "http://localhost:8000";
}

async function proxyRequest(request: NextRequest, path: string): Promise<NextResponse> {
  const bases = [getBackendBase(), "http://backend:8000", "http://localhost:8000"];

  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  const body = hasBody ? await request.arrayBuffer() : undefined;
  const search = request.nextUrl.search || "";

  for (const base of bases) {
    try {
      const proxyHeaders: Record<string, string> = {
        "Content-Type": request.headers.get("content-type") || "application/json",
      };
      const authHeader = request.headers.get("authorization");
      if (authHeader) proxyHeaders["Authorization"] = authHeader;
      const cookieHeader = request.headers.get("cookie");
      if (cookieHeader) proxyHeaders["Cookie"] = cookieHeader;

      const res = await fetch(`${base}${path}${search}`, {
        method: request.method,
        headers: proxyHeaders,
        body: body !== undefined ? body : undefined,
        cache: "no-store",
      });

      const responseHeaders = new Headers();
      const contentType = res.headers.get("content-type") || "";
      responseHeaders.set("Content-Type", contentType);

      const contentLength = res.headers.get("content-length");
      if (contentLength) responseHeaders.set("Content-Length", contentLength);

      // Forward Set-Cookie headers from backend so auth cookies persist
      const setCookies = res.headers.getSetCookie?.() ?? [];
      for (const cookie of setCookies) {
        responseHeaders.append("Set-Cookie", cookie);
      }
      // Fallback: some runtimes don't have getSetCookie
      if (setCookies.length === 0) {
        const rawSetCookie = res.headers.get("set-cookie");
        if (rawSetCookie) responseHeaders.set("Set-Cookie", rawSetCookie);
      }

      if (!contentType.includes("application/json")) {
        const buffer = await res.arrayBuffer();
        return new NextResponse(buffer, { status: res.status, headers: responseHeaders });
      }
      const data = await res.json().catch(() => null);
      return NextResponse.json(data, { status: res.status, headers: responseHeaders });
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
