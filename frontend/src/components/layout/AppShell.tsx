import { Outlet, useLocation } from "react-router-dom";
import { Menu, PanelRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Sidebar } from "./Sidebar";
import { ContextPanel } from "./ContextPanel";
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/stores/appStore";
import { useChatStore } from "@/stores/chatStore";
import { useEffect } from "react";

const TITLES: Record<string, string> = {
  "/": "Dashboard",
  "/chat": "Chat",
  "/sync": "Sync Center",
  "/repositories": "Repositories",
  "/memory": "Memory",
  "/graph": "Knowledge Graph",
  "/activity": "Activity",
  "/settings": "Settings",
  "/projects": "Projects",
};

export function AppShell() {
  const location = useLocation();
  const mobileOpen = useAppStore((s) => s.mobileSidebarOpen);
  const setMobileOpen = useAppStore((s) => s.setMobileSidebarOpen);
  const contextOpen = useAppStore((s) => s.contextPanelOpen);
  const setContextOpen = useAppStore((s) => s.setContextPanelOpen);
  const toast = useAppStore((s) => s.toast);
  const setToast = useAppStore((s) => s.setToast);
  const initSessions = useChatStore((s) => s.initSessions);

  useEffect(() => {
    initSessions();
  }, [initSessions]);

  useEffect(() => {
    if (!toast) return;
    const t = window.setTimeout(() => setToast(null), 3000);
    return () => window.clearTimeout(t);
  }, [toast, setToast]);

  const title =
    TITLES[location.pathname] ??
    (location.pathname.startsWith("/repositories/") ? "Repository" : "Cortex");

  return (
    <div className="flex h-screen overflow-hidden">
      <div className="hidden md:flex">
        <Sidebar />
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/60 md:hidden"
              onClick={() => setMobileOpen(false)}
            />
            <motion.div
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              className="fixed inset-y-0 left-0 z-50 md:hidden"
            >
              <Sidebar mobile />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center gap-3 border-b border-cortex-border bg-cortex-surface/80 px-4 backdrop-blur-md">
          <Button variant="ghost" size="icon" className="md:hidden" onClick={() => setMobileOpen(true)}>
            <Menu className="h-5 w-5" />
          </Button>
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-sm font-semibold">{title}</h1>
            <p className="text-xs text-cortex-muted">Personal intelligence layer</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="xl:hidden"
            onClick={() => setContextOpen(!contextOpen)}
            aria-label="Toggle context"
          >
            <PanelRight className="h-5 w-5" />
          </Button>
        </header>

        <main className="relative flex min-h-0 flex-1">
          <div className="min-w-0 flex-1 overflow-hidden">
            <Outlet />
          </div>
          {contextOpen && (
            <div className="absolute inset-y-0 right-0 z-30 shadow-2xl xl:hidden">
              <ContextPanel />
            </div>
          )}
          <div className="hidden xl:flex">
            <ContextPanel />
          </div>
        </main>
      </div>

      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 16 }}
            className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-lg border border-cortex-border bg-cortex-elevated px-4 py-2 text-sm shadow-lg"
          >
            {toast}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
