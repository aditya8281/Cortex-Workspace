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
  "/profile": "Profile",
  "/marketplace": "Marketplace",
  "/performance": "Performance",
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
  const hasHydrated = useChatStore((s) => s._hasHydrated);

  useEffect(() => {
    initSessions();
    if (!useChatStore.getState()._hasHydrated) {
      useChatStore.setState({ _hasHydrated: true });
    }
  }, [initSessions]);

  useEffect(() => {
    if (!toast) return;
    const t = window.setTimeout(() => setToast(null), 3000);
    return () => window.clearTimeout(t);
  }, [toast, setToast]);

  const title =
    TITLES[location.pathname] ??
    (location.pathname.startsWith("/repositories/") ? "Repository" : "Cortex");

  if (!hasHydrated) {
    return (
      <div className="flex h-screen items-center justify-center bg-cortex-bg text-cortex-text">
        <div className="text-center">
          <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-2 border-cortex-accent border-t-transparent" />
          <p className="text-sm text-cortex-muted">Starting Cortex…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex h-screen overflow-hidden bg-cortex-bg text-cortex-text">
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -left-28 top-[-8rem] h-96 w-96 rounded-full bg-cortex-accent/10 blur-3xl animate-float-soft" />
        <div className="absolute -bottom-28 right-[-6rem] h-[28rem] w-[28rem] rounded-full bg-cyan-400/8 blur-3xl animate-float-soft" />
        <div className="absolute inset-0 opacity-[0.12] [background-image:radial-gradient(circle_at_center,rgba(255,255,255,0.1)_1px,transparent_1px)] [background-size:24px_24px]" />
      </div>
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

      <div className="relative z-10 flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center gap-3 border-b border-cortex-border/70 bg-cortex-surface/75 px-4 backdrop-blur-2xl">
          <Button variant="ghost" size="icon" className="md:hidden" onClick={() => setMobileOpen(true)}>
            <Menu className="h-5 w-5" />
          </Button>
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-sm font-semibold tracking-wide">{title}</h1>
            <p className="text-xs text-cortex-muted">Personal intelligence layer</p>
          </div>
          <div className="hidden items-center gap-2 rounded-full border border-cortex-border/80 bg-cortex-elevated/70 px-3 py-1.5 text-[11px] font-medium text-cortex-muted lg:flex">
            <span className="relative h-2 w-2 rounded-full bg-cortex-success shadow-[0_0_0_4px_rgba(62,220,159,0.14)]">
              <span className="absolute inset-0 animate-ping rounded-full bg-cortex-success/60" />
            </span>
            Live
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
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                className="h-full"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2, ease: "easeOut" }}
              >
                <Outlet />
              </motion.div>
            </AnimatePresence>
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
            className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-full border border-cortex-border/80 bg-cortex-elevated/90 px-4 py-2 text-sm shadow-2xl backdrop-blur-xl"
          >
            {toast}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
