"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

// ── Types ─────────────────────────────────────────────────────────────

interface ModeState {
  modeId: string;
  scrollPosition: number;
  inputDraft?: string;
}

interface ModeStackContextValue {
  /** Current mode stack (hub always at bottom) */
  stack: ModeState[];
  /** Currently active mode ID */
  currentMode: string;
  /** Whether the currently active mode is the hub */
  isHub: boolean;
  /** Navigate to a mode (pushes onto stack) */
  pushMode: (modeId: string) => void;
  /** Go back one step in the stack. Returns the mode we popped from. */
  popMode: () => string | null;
  /** Go directly back to the hub, clearing the stack */
  goToHub: () => void;
  /** Save state snapshot for a mode */
  saveState: (modeId: string, updates: Partial<ModeState>) => void;
}

const MAX_DEPTH = 5;
const ModeStackContext = createContext<ModeStackContextValue | null>(null);

// ── Hook ──────────────────────────────────────────────────────────────

export function useModeStack(): ModeStackContextValue {
  const ctx = useContext(ModeStackContext);
  if (!ctx) {
    throw new Error("useModeStack must be used within <ModeStackProvider>");
  }
  return ctx;
}

// ── Provider ──────────────────────────────────────────────────────────

export function ModeStackProvider({ children }: { children: ReactNode }) {
  // Restore last mode from sessionStorage — survives page refresh
  const [stack, setStack] = useState<ModeState[]>(() => {
    try {
      const saved = sessionStorage.getItem("cortex_last_mode");
      if (saved && saved !== "hub") {
        return [
          { modeId: "hub", scrollPosition: 0 },
          { modeId: saved, scrollPosition: 0 },
        ];
      }
    } catch { /* non-critical */ }
    return [{ modeId: "hub", scrollPosition: 0 }];
  });

  const currentMode = stack[stack.length - 1]?.modeId ?? "hub";
  const isHub = currentMode === "hub";

  // Persist current mode to sessionStorage — survives refresh
  useEffect(() => {
    try {
      sessionStorage.setItem("cortex_last_mode", currentMode);
    } catch { /* non-critical */ }
  }, [currentMode]);

  // Use ref to track the latest callbacks so the keyboard handler doesn't stale-capture
  const pushRef = useRef<(id: string) => void>(null!);
  const popRef = useRef<() => void>(null!);
  const hubRef = useRef<() => void>(null!);

  const pushMode = useCallback((modeId: string) => {
    if (modeId === "hub") {
      hubRef.current?.();
      return;
    }

    // If already at this mode, do nothing (prevent duplicate pushes)
    setStack((prev) => {
      if (prev[prev.length - 1]?.modeId === modeId) return prev;

      const next = [...prev, { modeId, scrollPosition: 0 }];
      // Enforce max depth — drop oldest non-hub entry
      if (next.length > MAX_DEPTH) {
        return [{ modeId: "hub", scrollPosition: 0 }, ...next.slice(next.length - MAX_DEPTH + 1)];
      }
      return next;
    });
  }, []);

  const popMode = useCallback(() => {
    let popped: string | null = null;
    setStack((prev) => {
      if (prev.length <= 1) return prev;
      popped = prev[prev.length - 1].modeId;
      return prev.slice(0, -1);
    });
    return popped;
  }, []);

  const goToHub = useCallback(() => {
    setStack([{ modeId: "hub", scrollPosition: 0 }]);
  }, []);

  const saveState = useCallback(
    (modeId: string, updates: Partial<ModeState>) => {
      setStack((prev) =>
        prev.map((s) => (s.modeId === modeId ? { ...s, ...updates } : s)),
      );
    },
    [],
  );

  // Keep refs in sync
  pushRef.current = pushMode;
  popRef.current = popMode;
  hubRef.current = goToHub;

  const value = useMemo<ModeStackContextValue>(
    () => ({
      stack,
      currentMode,
      isHub,
      pushMode,
      popMode,
      goToHub,
      saveState,
    }),
    [stack, currentMode, isHub, pushMode, popMode, goToHub, saveState],
  );

  return (
    <ModeStackContext.Provider value={value}>
      {children}
    </ModeStackContext.Provider>
  );
}
