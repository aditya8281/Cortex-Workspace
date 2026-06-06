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

export async function POST(request) {
  const payload = await request.json();
  let lastError = null;
  let lastStatus = null;
  let lastBody = null;

  for (const base of getBackendBases()) {
    try {
      const response = await fetch(`${base.replace(/\/$/, "")}/api/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
        cache: "no-store",
      });
      const data = await response.json();

      if (!response.ok) {
        lastStatus = response.status;
        lastBody = data;
        lastError = data?.detail || data?.error || "Login failed";
        continue;
      }

      return NextResponse.json(data);
    } catch (error) {
      lastError = error instanceof Error ? error.message : "Login failed";
    }
  }

  // If we received a non-OK response from the backend, forward its body and status
  if (lastStatus && lastBody) {
    return NextResponse.json(lastBody, { status: lastStatus });
  }

  return NextResponse.json({ error: lastError || "Login failed" }, { status: 502 });
}
