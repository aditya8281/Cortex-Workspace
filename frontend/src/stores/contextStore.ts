import { create } from "zustand";
import type { ContextItem } from "@/types/cortex";

interface ContextState {
  /** Map of context item ID → item */
  contextItems: Map<string, ContextItem>;

  /** Attach a new context item */
  attach: (item: ContextItem) => void;

  /** Partially update a context item */
  update: (id: string, patch: Partial<ContextItem>) => void;

  /** Remove a context item by ID */
  remove: (id: string) => void;

  /** Return all attached context items as an array */
  list: () => ContextItem[];

  /** Clear all context items */
  clear: () => void;

  /**
   * Serialize context items into a flat string suitable for prompt injection.
   * Used as a fallback; the primary path now sends raw items to the backend.
   */
  resolve: () => string;

  /**
   * Return items serialised as a plain array for the API payload.
   */
  toPayload: () => ContextItem[];
}

export const useContextStore = create<ContextState>((set, get) => ({
  contextItems: new Map(),

  attach: (item) => {
    set((state) => {
      const newMap = new Map(state.contextItems);
      newMap.set(item.id, item);
      return { contextItems: newMap };
    });
  },

  update: (id, patch) => {
    set((state) => {
      const existing = state.contextItems.get(id);
      if (!existing) return state;
      const newMap = new Map(state.contextItems);
      newMap.set(id, { ...existing, ...patch });
      return { contextItems: newMap };
    });
  },

  remove: (id) => {
    set((state) => {
      const newMap = new Map(state.contextItems);
      newMap.delete(id);
      return { contextItems: newMap };
    });
  },

  list: () => Array.from(get().contextItems.values()),

  clear: () => {
    set({ contextItems: new Map() });
  },

  resolve: () => {
    const items = get().list();
    if (items.length === 0) return "";

    let resolved = "Attached Context:\n";
    items.forEach((item) => {
      resolved += `- ${item.title} (${item.kind}): `;
      if (item.contentPreview) {
        resolved += `\n${item.contentPreview}\n`;
      } else if (item.detail) {
        resolved += `${item.detail}\n`;
      } else {
        resolved += "\n";
      }
    });
    return resolved;
  },

  toPayload: () => get().list(),
}));