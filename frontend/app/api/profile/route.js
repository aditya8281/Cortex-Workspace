import { NextResponse } from "next/server";

function getBackendBases() {
  const publicBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
  const normalized = publicBase.replace(/\/api\/v1\/?$/, "");
  return [
    process.env.CORTEX_BACKEND_URL,
    normalized,
    "http://backend:8000",
    "http://localhost:8000",
  ].filter(Boolean);
}

function buildHeaders(request) {
  const headers = {
    "Content-Type": "application/json",
  };
  const authorization = request.headers.get("authorization");
  if (authorization) headers.Authorization = authorization;
  return headers;
}

export async function GET(request) {
  let lastError = null;

  for (const base of getBackendBases()) {
    try {
      const response = await fetch(`${base.replace(/\/$/, "")}/api/v1/profile`, {
        cache: "no-store",
        headers: buildHeaders(request),
      });
      const data = await response.json();

      if (!response.ok) {
        lastError = data?.detail || "Profile request failed";
        continue;
      }

      return NextResponse.json(data);
    } catch (error) {
      lastError = error instanceof Error ? error.message : "Profile request failed";
    }
  }

  return NextResponse.json({ error: lastError || "Profile request failed" }, { status: 502 });
}

export async function PUT(request) {
  const payload = await request.json();
  let lastError = null;

  for (const base of getBackendBases()) {
    try {
      const response = await fetch(`${base.replace(/\/$/, "")}/api/v1/profile`, {
        method: "PUT",
        headers: buildHeaders(request),
        body: JSON.stringify(payload),
        cache: "no-store",
      });
      const data = await response.json();

      if (!response.ok) {
        lastError = data?.detail || "Profile update failed";
        continue;
      }

      return NextResponse.json(data);
    } catch (error) {
      lastError = error instanceof Error ? error.message : "Profile update failed";
    }
  }

  return NextResponse.json({ error: lastError || "Profile update failed" }, { status: 502 });
}
