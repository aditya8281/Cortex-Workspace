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

  for (const base of getBackendBases()) {
    try {
      const response = await fetch(`${base.replace(/\/$/, "")}/api/models/download`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
        cache: "no-store",
      });
      const data = await response.json();

      if (!response.ok) {
        lastError = data?.detail || "Download request failed";
        continue;
      }

      return NextResponse.json(data);
    } catch (error) {
      lastError = error instanceof Error ? error.message : "Download request failed";
    }
  }

  return NextResponse.json({ error: lastError || "Download request failed" }, { status: 502 });
}
