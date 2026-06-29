# Dependency Graph — CORTEX Control Plane

```
┌─────────────────────────────────────────────────────────────────┐
│                        REQUEST FLOW                              │
│                                                                   │
│  Browser                                                          │
│    │                                                              │
│    ├── HTTP ──────────► Next.js (port 3000)                       │
│    │                      │                                       │
│    │                      ├── API Route ──────► FastAPI (port X)  │
│    │                      │    (proxy /api/:path*)                │
│    │                      │                                       │
│    │                      ├── Page (SSR/SSG)                      │
│    │                      │                                       │
│    │                      └── Static Assets                       │
│    │                                                              │
│    └── WebSocket ──► Direct ──► FastAPI (port X)                  │
│                           (bypasses Next.js proxy)                │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                     FASTAPI MIDDLEWARE CHAIN                       │
│                                                                     │
│  Request In                                                        │
│    │                                                                │
│    ▼                                                                │
│  CORSMiddlewareWithWS     ← handles HTTP + WebSocket CORS          │
│    │                                                                │
│    ▼                                                                │
│  RequestLoggingMiddleware ← request_id, timing                     │
│    │                                                                │
│    ▼                                                                │
│  GZipMiddleware          ← compress >= 500B                        │
│    │                                                                │
│    ▼                                                                │
│  RequestSizeLimitMiddleware ← 10MB default                         │
│    │                                                                │
│    ▼                                                                │
│  RateLimitMiddleware     ← per-route limits                        │
│    │                                                                │
│    ▼                                                                │
│  CSRFMiddleware          ← double-submit (GET → set cookie)        │
│    │                       (POST/PUT/DELETE → verify header)       │
│    ▼                        (exempts /auth, /health, /ws, /metrics)│
│  HTTPSRedirectMiddleware ← optional prod redirect                  │
│    │                                                                │
│    ▼                                                                │
│  FastAPI Router                                                    │
│    │                                                                │
│    ├── /api/v1/*  ──► api_router                                    │
│    │                  ├── /memory/*      (v1_memory_router)        │
│    │                  ├── /awareness/*   (awareness_router)        │
│    │                  ├── /agents/*      (cognition_router)        │
│    │                  ├── /execution/*   (execution_router)        │
│    │                  ├── /conversations (interaction_router)      │
│    │                  ├── /health/*      (system_router)           │
│    │                  ├── /ws/system     (ws_system_router)        │
│    │                  ├── /ws/chat       (ws_chat_router)          │
│    │                  ├── /ws/models     (ws_models_router)        │
│    │                  ├── /ws/agents     (ws_agents_router)        │
│    │                  ├── /ws/notifications (ws_notifications_router)│
│    │                  ├── /models/*      (intelligence_router)     │
│    │                  ├── /models/*      (integration_router)      │
│    │                  ├── /privacy/*     (privacy_router)          │
│    │                  └── /memory        (memory_router — LEGACY)  │
│    │                        └── DUPLICATE: also at /api/v1/api/v1/memory/*│
│    ├── /api/v1/auth/* ──► auth_router                              │
│    ├── /api/v1/memory/* ──► memory_router (DIRECT INCLUDE)         │
│    └── /ws/demo ──► ws_router (no /api/v1 prefix)                 │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FLOW                              │
│                                                                     │
│  Client                              Backend                        │
│    │                                    │                           │
│    ├── POST /api/v1/auth/login ────────►│                           │
│    │◄── Set-Cookie: cortex_access=JWT  │  ✓ verify_password        │
│    │    Set-Cookie: cortex_refresh=JWT  │  ✓ create_access_token    │
│    │                                     │  ✓ create_refresh_token  │
│    │                                     │  ✓ log_event (audit)     │
│    │                                     │                           │
│    ├── GET /api/v1/auth/me ────────────►│                           │
│    │    Cookie: cortex_access=JWT       │  ✓ verify_access_token    │
│    │◄── UserResponse                    │  ✓ is_access_token_revoked│
│    │                                     │  ✓ User.deleted_at check │
│    │                                     │                           │
│    ├── POST /api/v1/auth/ws-token ─────►│                           │
│    │    Cookie: cortex_access=JWT       │  ✓ read cookie            │
│    │◄── {"token": "jwt"}               │                           │
│    │                                     │                           │
│    ├── WebSocket(sec-websocket-protocol)►│                           │
│    │    uses token as subprotocol        │  ✓ _extract_ws_token     │
│    │                                      │  ✓ verify_ws_token       │
│    │                                      │                           │
│    └── POST /api/v1/auth/refresh ──────►│                           │
│         Cookie: cortex_refresh=JWT       │  ✓ verify_refresh_token   │
│                                          │  ✓ rotate_refresh_token   │
│                                          │  ✓ revoke old refresh JTI │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                    DATABASE SESSION FLOW                            │
│                                                                     │
│  HTTP Endpoint (request-scoped)        WebSocket Endpoint           │
│    │                                      │                        │
│    │ Depends(get_db)                      │ SessionLocal()          │
│    │   │                                  │   │                     │
│    │   ├── yield session                  │   ├── query(...)        │
│    │   │   ├── query(...)                 │   ├── send/receive loop │
│    │   │   ├── commit()                   │   ├── query(...)        │
│    │   │   └── return                     │   └── close()           │
│    │   └── finally: session.close()       │                        │
│    │                                      │ session may be STALE    │
│    │                                      │ during long WS life     │
│    │                                      │ (manual refresh needed)  │
│                                          
│  TEST OVERRIDE:                            X NOT OVERRIDABLE        │
│  app.dependency_overrides[get_db]          (SessionLocal() direct)  │
│  → tests inject in-memory SQLite           → tests use real PG     │
│                                           → WS untestable            │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                    WEB SOCKET CONNECTION LIFECYCLE                  │
│                                                                     │
│  useWebSocket (Frontend)               Backend Endpoint             │
│    │                                      │                        │
│    1. fetch(/auth/ws-token)               │                        │
│    │                                      │                        │
│    2. new WebSocket(url, [token]) ────────►│                        │
│    │                                      │  ws.accept() ← FIRST   │
│    │                                      │  _extract_ws_token()   │
│    │                                      │  verify_ws_token()     │
│    │                                      │  manager.register()    │
│    │                                      │                        │
│    3. onopen fires ◄─────── 101 ──────── ws.accept() returns      │
│    │                                      │                        │
│    4. heartbeat interval (30s)            │                        │
│    │  └── send({"type":"ping"}) ─────────►│                        │
│    │                                      │  (ignored by push-only)│
│    │                                      │  (ws_chat sends pong)  │
│    │                                      │                        │
│    ├── send(message) ────────────────────►│                        │
│    │◄── push data ───────────────────────│                        │
│    │                                      │                        │
│    5. onclose fires ◄──────── disconnect │                        │
│       scheduleRetry() (unless intentional)│                        │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                    FRONTEND COMPONENT TREE                          │
│                                                                     │
│  RootLayout                                                         │
│    ├── AuthProvider (context: user, loading, logout)                │
│    ├── MetricsProvider (context: metrics, processes, logs)          │
│    │   └── uses useWebSocket("/api/v1/ws/system")                   │
│    ├── ToastProvider                                                │
│    │                                                                │
│    └── Pages                                                        │
│        ├── / → DashboardPage                                        │
│        │   ├── SystemOverview (uses useMetrics)                     │
│        │   ├── QuickActions                                         │
│        │   ├── MetricsRow                                           │
│        │   └── RecentActivity                                       │
│        ├── /system → SystemPage                                     │
│        │   ├── MetricsGrid (uses useMetrics)                        │
│        │   └── LogViewer                                            │
│        ├── /agents → AgentsPage                                     │
│        │   └── uses useWebSocket("/api/v1/ws/agents")               │
│        ├── /chat → ChatPage                                         │
│        │   └── uses useChatTyping                                   │
│        │       └── uses useWebSocket("/api/v1/ws/chat")             │
│        └── /models → ModelsPage                                     │
│            └── DownloadProvider                                      │
│                └── uses useWebSocket("/api/v1/ws/models")            │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE DEPENDENCIES                      │
│                                                                     │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐                    │
│  │ Frontend │────►│ Backend  │────►│ PostgreSQL│                    │
│  │ :3000    │     │ :8000    │     │ :5435     │                    │
│  └──────────┘     │          │     └──────────┘                    │
│       │           │          │     ┌──────────┐                    │
│       │ (WS)      │          │────►│ Qdrant   │                    │
│       └──────────►│          │     │ :6333    │                    │
│                   │          │     └──────────┘                    │
│                   │          │     ┌──────────┐                    │
│                   │          │────►│ Redis    │                    │
│                   │          │     │ :6379    │                    │
│                   │          │     └──────────┘                    │
│                   │          │     ┌──────────┐                    │
│                   │          │────►│ Ollama   │                    │
│                   │          │     │ :11434   │                    │
│                   │          │     └──────────┘                    │
│                   └──────────┘                                     │
│                                                                     │
│  Optional: All infra services (Redis, Qdrant, Ollama)              │
│  fail open — backend degrades but doesn't crash.                   │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```
