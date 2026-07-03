"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { useModeStack } from "./ModeStack";
import { Dock } from "./Dock";
import { NeuralRibbon } from "./NeuralRibbon";
import HubPage from "@/features/hub/page";
import ChatPage from "@/features/chat/page";
import SearchPage from "@/features/search/page";
import BrainPage from "@/features/brain/page";
import VaultPage from "@/features/vault/page";
import ModelsPage from "@/features/models/page";
import CodePage from "@/features/code/page";
import UtilityPage from "@/features/utility/page";
import SettingsPage from "@/features/settings/page";
import SystemsPage from "@/features/system/page";
import ProfilePage from "@/features/profile/page";
import {
  ChatIcon, SearchIcon, BrainIcon, VaultIcon, ModelsIcon,
  CodeIcon, UtilityIcon, SettingsIcon, SystemsIcon, ProfileIcon,
} from "@/shared/ui/icons";
import { cn } from "@/shared/lib/utils";

gsap.registerPlugin(useGSAP);

interface ModeEntry {
  icon: React.ReactNode;
  name: string;
  Component: React.ComponentType<any> | null;
  /** If true, ModeView skips its own header — the component renders its own */
  selfContained?: boolean;
}

const MODE_REGISTRY: Record<string, ModeEntry> = {
  chat:     { icon: <ChatIcon size={18} />, name: "Chat",     Component: ChatPage, selfContained: true },
  search:   { icon: <SearchIcon size={18} />, name: "Search",   Component: SearchPage },
  brain:    { icon: <BrainIcon size={18} />, name: "Brain",    Component: BrainPage },
  vault:    { icon: <VaultIcon size={18} />, name: "Vault",    Component: VaultPage },
  models:   { icon: <ModelsIcon size={18} />, name: "Models",   Component: ModelsPage },
  code:     { icon: <CodeIcon size={18} />, name: "Code",     Component: CodePage },
  utility:  { icon: <UtilityIcon size={18} />, name: "Utility",  Component: UtilityPage },
  settings: { icon: <SettingsIcon size={18} />, name: "Settings", Component: SettingsPage },
  systems:  { icon: <SystemsIcon size={18} />, name: "Systems",  Component: SystemsPage },
  profile:  { icon: <ProfileIcon size={18} />, name: "Profile",  Component: ProfilePage },
};

// ── Placeholder mode page ────────────────────────────────────────────
function PlaceholderMode({ icon, name }: { icon: React.ReactNode; name: string }) {
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

// ── Component ─────────────────────────────────────────────────────────
export function ModeView() {
  const { currentMode, isHub, pushMode, popMode, goToHub } = useModeStack();
  const [dockVisible, setDockVisible] = useState(true);
  const [transitioning, setTransitioning] = useState(false);
  const [exitingId, setExitingId] = useState<string | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const prevModeRef = useRef(currentMode);

  // ── GSAP crossfade on mode change ──────────────────────────────────
  useGSAP(() => {
    if (!contentRef.current) return;
    if (currentMode === prevModeRef.current) return;

    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: reduce)", () => {
      gsap.set(contentRef.current, { opacity: 1 });
      return () => {};
    });

    mm.add("(prefers-reduced-motion: no-preference)", () => {
      const tl = gsap.timeline();
      // Fade out briefly if we were already rendered
      tl.fromTo(contentRef.current, { opacity: 1 }, { opacity: 0, duration: 0.05, ease: "none" })
        .to(contentRef.current, { opacity: 1, duration: 0.12, ease: "power2.out" });
    });

    prevModeRef.current = currentMode;
    return () => mm.revert();
  }, { dependencies: [currentMode], scope: contentRef });

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
    setExitingId(currentMode);
    setTransitioning(true);
    requestAnimationFrame(() => {
      pushMode(modeId);
      setTimeout(() => { setTransitioning(false); setExitingId(null); }, 200);
    });
  };

  const handleBack = () => {
    setExitingId(currentMode);
    setTransitioning(true);
    requestAnimationFrame(() => {
      const popped = popMode();
      if (popped) {
        setTimeout(() => { setTransitioning(false); setExitingId(null); }, 200);
      }
    });
  };

  // ── Render hub ────────────────────────────────────────────────────
  if (isHub) {
    return (
      <div className="relative h-dvh overflow-hidden bg-bg-base">
        <NeuralRibbon />
        <div className="absolute inset-0 top-6 flex flex-col overflow-y-auto">
          <div ref={contentRef} className="flex h-full flex-col">
            <HubPage />
          </div>
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
      <div className="absolute inset-0 top-6 flex flex-col min-h-0">
        <div ref={contentRef} className="flex h-full flex-col min-h-0">
          {entry.selfContained ? (
            /* Self-contained mode (chat) renders its own header */
            <main className="flex-1 min-h-0 overflow-hidden">
              {entry.Component && <entry.Component />}
            </main>
          ) : (
            <>
              <header className="flex h-11 items-center gap-2.5 border-b border-border-subtle px-4 flex-shrink-0 min-h-0">
                <button
                  onClick={handleBack}
                  className="flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-text-primary motion-safe:transition-colors motion-safe:duration-150"
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
            </>
          )}
        </div>
      </div>
      <Dock
        activeMode={currentMode}
        onModeChange={handleModeChange}
        visible={dockVisible}
      />
    </div>
  );
}
