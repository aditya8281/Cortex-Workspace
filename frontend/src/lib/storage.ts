/** Clear corrupt persisted state that can crash the app on load. */
export function sanitizePersistedStorage() {
  for (const key of ["cortex-chats", "cortex-app", "cortex-profile"]) {
    try {
      const raw = localStorage.getItem(key);
      if (!raw) continue;
      JSON.parse(raw);
    } catch {
      localStorage.removeItem(key);
    }
  }
}
