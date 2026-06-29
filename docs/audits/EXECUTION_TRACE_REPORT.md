# Execution Trace Report

## Trace 1: Frontend Login → Dashboard

```
1. User submits login form (auth/page.tsx)
2. apiFetch("/auth/login") → fetch("/api/v1/auth/login")
   │  POST, body: {username, password}
   │  includes CSRF token from cookie
   ▼
3. Backend POST /api/v1/auth/login
   │  auth.service.login_user_service()
   │  ├── rate_limit.is_blocked() check
   │  ├── authenticate_user() → verify_password()
   │  ├── create_access_token({sub: str(user.id)})
   │  ├── create_refresh_token(user.id) → DB INSERT
   │  ├── log_event("login_success")
   │  └── reset_login_failures()
   ▼
4. Response with Set-Cookie: cortex_access + cortex_refresh
   ▼
5. window.location.href = "/"
   ▼
6. Next.js server checks middleware.ts
   │  Checks token cookie presence
   │  → Protected path with token → allow
   ▼
7. Browser renders dashboard page
   ▼
8. AuthProvider useEffect fires
   │  fetch("/api/v1/auth/me", {credentials: "include"})
   │  GET with httpOnly cookie → backend validates JWT → returns UserResponse
   ▼
9. AuthProvider.setUser(data) → user is now non-null
   ▼
10. MetricsProvider sees user is non-null → enables useWebSocket
    │  fetch("/api/v1/auth/ws-token") → {"token": "jwt..."}
    │  new WebSocket("ws://localhost:8001/api/v1/ws/system", [token])
    │  ws.accept() → ws.onopen fires → connected: true
    │  Server pushes metrics every 500ms
    ▼
11. SystemOverview receives metrics data via MetricsContext
```

**Potential failure points:**
- Step 2: CSRF cookie missing → 403
- Step 5: Full page reload loses React state (by design)
- Step 8: `/me` returns different user than login? (token consumed?)
- Step 10: WS-token endpoint fails if JWT expired (refresh needed)
- Step 10: WebSocket connects to different backend than HTTP proxy

## Trace 2: WebSocket Message Flow (System Metrics)

```
SERVER PUSH (every 500ms):
  ws_system.py: collect_metrics() → ws.send_text(json.dumps(...))

CLIENT RECEIVE:
  useWebSocket ws.onmessage → JSON.parse
  → setLastMessage(data)
  → onMessageRef.current(data)  → MetricsProvider.handleMessage
    → data.type === "metrics" → setMetrics(data as unknown as LiveMetrics)

ERROR PATH:
  Network failure → ws.onerror fires
    → setStatus("error")
    → onErrorRef.current(event)  → user callback
    → (ws.onclose fires after onerror)
  ws.onclose fires
    → setStatus("disconnected")
    → if !intentionalClose → scheduleRetry() with exponential backoff
      → retryTimer fires → connect() again
```

**Maximum reconnect chain:**
```
t=0  disconnect → retry 1/10 → timer 1s
t=1  connect fails → retry 2/10 → timer 2s
t=3  connect fails → retry 3/10 → timer 4s
t=7  connect fails → retry 4/10 → timer 8s
t=15 connect fails → retry 5/10 → timer 16s
t=31 connect fails → retry 6/10 → timer 30s
t=61 connect fails → retry 7/10 → timer 30s
...every 30s until retry 10/10 → stop
```
Total max reconnect time: ~4 minutes before giving up.

## Trace 3: Auth Token Refresh Cycle

```
1. Client makes API call with expired access token
2. Backend returns 401
3. apiFetch catches 401 (not auth path)
4. apiFetch calls POST /api/v1/auth/refresh with refresh cookie
5. Backend validates refresh token:
   ├── verify_refresh_token(refresh_token)
   │   ├── decode JWT
   │   ├── check expires_at column
   │   └── check revoked_at column (revoked_at is not None → 401)
   └── rotate_refresh_token
       ├── create new access token
       ├── create new refresh token (DB INSERT)
       ├── revoke old refresh token (UPDATE revoked_at)
       └── Set-Cookie new tokens
6. apiFetch retries original request with new cookie
7. If refresh fails → window.location.href = "/auth" (full redirect)
```

**Potential issue:** Race condition if two API calls refresh simultaneously.
The first refresh revokes the old token. The second refresh uses the now-revoked
old token → 401 → both calls redirect to auth.

## Trace 4: Chat Typing WebSocket Flow

```
USER STARTS TYPING:
  1. ChatInput calls useChatTyping.sendTyping()
  2. sendTyping() sends via WS: {"action": "typing", "conversation_id": 123}
  3. ws_chat.py receives: await ws.receive_text()
     → JSON parse → action = "typing", conv_id = 123
     → broadcast to ALL other WS on channel "chat:123":
       {"type": "typing", "conversation_id": 123, "user_id": 456}
  4. Other clients receive via useChatTyping handleWSMessage
     → data.type === "typing" && data.user_id !== localUserId
     → add to typingUsers array
     → setTimeout 5s → remove from typingUsers (auto-expire)

JOIN CONVERSATION:
  1. Chat page mounts with conversationId
  2. useChatTyping sends: {"action": "join", "conversation_id": 123}
  3. ws_chat.py adds WS to "chat:123" channel set

RECONNECT:
  1. WS disconnects → useWebSocket reconnects after backoff
  2. useChatTyping detects status change to "connected"
  3. useEffect re-sends join for current conversationId
```

```
LOCAL USER STOPS TYPING:
  1. 3 seconds after last sendTyping call (timeout in useChatTyping)
  2. Sends: {"action": "stop_typing", "conversation_id": 123}
  3. Server broadcasts to others:
     {"type": "stop_typing", "conversation_id": 123, "user_id": 456}
```

## Trace 5: Unused WS Demo Endpoint

```
CONNECTION:
  Frontend never connects to /ws/demo
  No frontend code references this endpoint

SERVER:
  /ws/demo registered at root level (not under /api/v1)
  Uses raw jwt.decode (bypasses verify_ws_token)
  Has stream/echo actions — no real production use
```

This endpoint is effectively dead code. No frontend consumer exists.
It was likely used during WS development for manual testing.
