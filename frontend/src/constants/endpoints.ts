export const API_ENDPOINTS = {
  // Auth
  AUTH_LOGIN: "/login",
  AUTH_REGISTER: "/users",
  AUTH_ME: "/me",

  // AI
  AI_ASK: "/ai/ask",
  AI_CHAT: "/ai/chat",
  AI_HISTORY: "/ai/history",

  // Models
  MODELS_LIST: "/models",
  MODELS_BY_TYPE: "/models/by-type",
  MODELS_SELECT: "/models/select",
  MODELS_INSTALLED: "/models/installed",
  MODELS_CUSTOM: "/models/custom",
  MODELS_CUSTOM_ITEM: "/models/custom/{name}",
  MODELS_PROVIDERS: "/models/providers",
  MODELS_PROVIDERS_VALIDATE: "/models/providers/validate",
  MODELS_MARKETPLACE: "/models/marketplace",
  MODELS_HARDWARE: "/models/hardware",
  MODELS_DOWNLOADS: "/models/downloads",
  MODELS_DOWNLOAD_JOB: "/models/downloads/{job_id}",
  MODELS_PULL: "/models/pull",

  // Routing
  ROUTING_PROFILES: "/models/routing/profiles",
  ROUTING_PROFILES_SELECT: "/models/routing/profiles/select",
  ROUTING_ROUTES: "/models/routing/routes",
  ROUTING_METRICS: "/models/metrics",
  ROUTING_ANALYTICS: "/models/metrics/analytics",

  // Sync
  SYNC_TRIGGER: "/workspace/sync",
  SYNC_STATUS: "/sync/status",
  SYNC_RUN_LATEST: "/sync/runs/latest",
  SYNC_RUN: "/sync/runs/{id}",
  SYNC_NOW: "/sync/now",
  SYNC_FORCE: "/sync/force",
  SYNC_CANCEL: "/sync/cancel",
  SYNC_CONFIG: "/sync/config",
  SYNC_CONFIG_INCLUDE: "/sync/config/include",
  SYNC_CONFIG_EXCLUDE: "/sync/config/exclude",

  // Memory
  MEMORY_SEARCH: "/intelligence/memory/search",
  MEMORY_KNOWLEDGE: "/intelligence/knowledge",
  VAULT_SETTINGS: "/vault/settings",
  VAULT_CHANGE_PATH: "/vault/change-path",
  VAULT_EXPORT: "/vault/export",
  VAULT_IMPORT: "/vault/import",
  VAULT_RESET: "/vault/reset",

  // Hierarchical
  HIERARCHICAL_SEARCH: "/sync/hierarchical/search",
  HIERARCHICAL_EXPAND: "/sync/hierarchical/expand_graph",

  // Intelligence
  INTELLIGENCE_SETTINGS: "/intelligence/settings/automation",
  INTELLIGENCE_ACTIONS_PLAN: "/intelligence/actions/plan",
  INTELLIGENCE_ACTIONS_PENDING: "/intelligence/actions/pending",
  INTELLIGENCE_ACTIONS_APPROVE: "/intelligence/actions/{id}/approve",
  INTELLIGENCE_PROACTIVE: "/intelligence/proactive",
  // Workspace
  WORKSPACE_INTELLIGENCE: "/workspace/intelligence",

  // Execution
  EXECUTION_LIST: "/execution",
  EXECUTION_DETAIL: "/execution/{id}",
  EXECUTION_REPLAY: "/execution/{id}/replay",

  // Context
  CONTEXT_ATTACH: "/context/attach",
  CONTEXT_LIST: "/context",

  // Health
  HEALTH_LIVE: "/health/live",
  HEALTH_READY: "/health/ready",
  HEALTH_DEEP: "/health/deep",

  // User Settings
  USER_SETTINGS: "/users/me/settings",
  USER_PROFILE: "/me/profile",

  // Admin
  ADMIN_USERS: "/users",
  ADMIN_USER_DETAIL: "/users/{id}",
  ADMIN_LOGS: "/execution",
};

export const ROLES = {
  USER: "user",
  ADMIN: "admin",
} as const;

export const FEATURE_FLAGS = {
  COMMAND_PALETTE: true,
  REAL_TIME_SYNC: false,
  EXPORT_MEMORY: true,
  BATCH_OPERATIONS: false,
} as const;
