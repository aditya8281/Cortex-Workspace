/**
 * Catch-all proxy — forwards any /api/* request to the FastAPI backend.
 * Supports binary uploads (FormData/images) and binary responses (images/files).
 * Forwards Set-Cookie headers so auth cookies persist in the browser.
 */

import { NextResponse, type NextRequest } from "next/server";
import { getBackendBase } from "@/shared/backend-url";

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
      const csrfHeader = request.headers.get("x-csrf-token");
      if (csrfHeader) proxyHeaders["x-csrf-token"] = csrfHeader;

      const res = await fetch(`${base}${path}${search}`, {
        method: request.method,
        headers: proxyHeaders,
        body: body !== undefined ? body : undefined,
        cache: "no-store",
      });

      const responseHeaders = new Headers();
      const contentType = res.headers.get("content-type") || "";
      responseHeaders.set("Content-Type", contentType);

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
