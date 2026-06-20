/**
 * Runtime env endpoint — exposes the backend URL to the browser so the
 * frontend can dynamically discover the backend port for WebSocket connections
 * (and any other direct-backend needs) without hardcoded ports.
 */

import { NextResponse } from "next/server";
import { getBackendBase } from "@/shared/backend-url";

export async function GET() {
  const backendUrl = getBackendBase();
  const wsProtocol = backendUrl.startsWith("https") ? "wss" : "ws";
  const wsUrl = backendUrl.replace(/^http/, wsProtocol);
  return NextResponse.json({ backendUrl, wsUrl });
}
