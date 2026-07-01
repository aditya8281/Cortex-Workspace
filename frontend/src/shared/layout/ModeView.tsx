"use client";

import { useCallback, useEffect, useState } from "react";
import { useModeStack } from "./ModeStack";
import { Dock } from "./Dock";
import { NeuralRibbon } from "./NeuralRibbon";
import HubPage from "@/features/hub/page";
import { cn } from "@/shared/lib/utils";

interface ModeEntry {
  icon: string;
  name: string;
  Component: React.ComponentType | null; // null = coming soon
}

const MODE_REGISTRY: Record<string, ModeEntry> = {
  chat:    { icon: "💬", name: "Chat",    Component: null },
  search:  { icon: "🔍", name: "Search",  Component: null },
  brain:   { icon: "🧠", name: "Brain",   Component: null },
  vault:   { icon: "🔐", name: "Vault",   Component: null },
  models:  { icon: "📚", name: "Models",  Component: null },
  code:    { icon: "📐", name: "Code",    Component: null },
  utility: { icon: "🛠️", name: "Utility", Component: null },
  settings: { icon: "⚙️", name: "Settings", Component: null },
  systems: { icon: "🖥️", name: "Systems", Component: null },
  profile: { icon: "👤", name: "Profile", Component: null },
};

// ── Hub entry point (replaced placeholder from P03+) ─────────────────

// ── Placeholder mode page ────────────────────────────────────────────
function PlaceholderMode({ icon, name }: { icon: string; name: string }) {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <span className="text-3xl">{icon}</span>
        <p className="mt-3 text-headline font-semibold text-text-primary">{name}</p>
        <p className="mt-1 text-sm text-text-muted">Coming soon</p>
      </div>
    </div>
  );
}

// ── Crossfade wrapper ────────────────────────────────────────────────
function CrossfadeView({ children, id }: { children: React.ReactNode; id: string }) {
  return (
    <div
      key={id}
      className={cn(
        "flex h-full flex-col",
        "animate-fade-in motion-safe:animate-fade-in",
      )}
    >
      {children}
    </div>
  );
}

// ── Component ─────────────────────────────────────────────────────────
export function ModeView() {
  const { currentMode, isHub, pushMode, popMode, goToHub } = useModeStack();
  const [dockVisible, setDockVisible] = useState(true);
  const [transitioning, setTransitioning] = useState(false);

  // Auto-hide dock after 3s in mode view
  useEffect(() => {
    if (isHub) {
      setDockVisible(true);
      return;
    }

    const t = setTimeout(() => setDockVisible(false), 3000);
    return () => clearTimeout(t);
  }, [isHub, currentMode]);

  // Show dock on mouse move near bottom edge
  useEffect(() => {
    function handleMouseMove(e: MouseEvent) {
      if (isHub) return;
      const bottomEdge = window.innerHeight - 60;
      if (e.clientY >= bottomEdge) {
        setDockVisible(true);
      }
    }

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [isHub]);

  // Listen for hub:navigate custom event (dispatched by HubPage widgets)
  useEffect(() => {
    function onHubNavigate(e: CustomEvent<{ modeId: string }>) {
      pushMode(e.detail.modeId);
    }
    window.addEventListener("hub:navigate", onHubNavigate as EventListener);
    return () => window.removeEventListener("hub:navigate", onHubNavigate as EventListener);
  }, [pushMode]);

  const handleModeChange = (modeId: string) => {
    if (modeId === currentMode) return;
    setTransitioning(true);
    // Small delay to let exit animation start, then navigate
    requestAnimationFrame(() => {
      pushMode(modeId);
      setTimeout(() => setTransitioning(false), 150);
    });
  };

  const handleBack = () => {
    setTransitioning(true);
    requestAnimationFrame(() => {
      const popped = popMode();
      if (popped) {
        setTimeout(() => setTransitioning(false), 150);
      }
    });
  };

  // ── Render hub ────────────────────────────────────────────────────
  if (isHub) {
    return (
      <div className="relative h-dvh overflow-hidden bg-bg-base">
        <NeuralRibbon />
        <div className="absolute inset-0 top-6 flex flex-col overflow-y-auto">
          <CrossfadeView id="hub">
            <HubPage />
          </CrossfadeView>
        </div>
        <Dock
          activeMode={currentMode}
          onModeChange={handleModeChange}
          visible={true}
        />
      </div>
    );
  }

  // ── Mode view ─────────────────────────────────────────────────────
  const entry = MODE_REGISTRY[currentMode];
  if (!entry) {
    return (
      <div className="relative h-dvh overflow-hidden bg-bg-base">
        <NeuralRibbon />
        <div className="absolute inset-0 top-6 flex items-center justify-center text-text-muted text-sm">
          Unknown mode: {currentMode}
        </div>
        <Dock
          activeMode={currentMode}
          onModeChange={handleModeChange}
          visible={true}
        />
      </div>
    );
  }

  return (
    <div className="relative h-dvh overflow-hidden bg-bg-base">
      <NeuralRibbon />
      <div className="absolute inset-0 top-6 flex flex-col">
        <CrossfadeView id={currentMode}>
          <header className="flex h-11 items-center gap-2.5 border-b border-border-subtle px-4 flex-shrink-0">
            <button
              onClick={handleBack}
              className="flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-text-primary transition-colors duration-150"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10 2L4 8l6 6" />
              </svg>
              Back
            </button>
            <span className="text-border-default text-sm">·</span>
            <span className="text-lg leading-none">{entry.icon}</span>
            <h1 className="text-sm font-semibold text-text-primary">{entry.name}</h1>
            <div className="flex-1" />
          </header>
          <main className="flex-1 overflow-y-auto">
            {entry.Component ? (
              <entry.Component />
            ) : (
              <PlaceholderMode icon={entry.icon} name={entry.name} />
            )}
          </main>
        </CrossfadeView>
      </div>
      <Dock
        activeMode={currentMode}
        onModeChange={handleModeChange}
        visible={dockVisible}
      />
    </div>
  );
}
