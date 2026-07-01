"use client";

import { useRef } from "react";
import { cn } from "@/shared/lib/utils";
import gsap from "gsap";
import { Flip } from "gsap/Flip";
import { useGSAP } from "@gsap/react";
import type { Conversation } from "../api";

gsap.registerPlugin(Flip);

interface ConversationListProps {
  conversations: Conversation[];
  activeId: number | null;
  onSelect: (id: number) => void;
}

export function ConversationList({
  conversations,
  activeId,
  onSelect,
}: ConversationListProps) {
  const listRef = useRef<HTMLDivElement>(null);

  // Flip animation when conversations reorder (sort/filter)
  useGSAP(() => {
    if (!listRef.current || !conversations.length) return;

    const state = Flip.getState(listRef.current.querySelectorAll("[data-conv-id]"));
    // DOM has already updated — Flip captures post positions and animates from old
    Flip.from(state, {
      duration: 0.4,
      ease: "power3.inOut",
      absolute: true,
      scale: false,
      target: listRef.current.querySelectorAll("[data-conv-id]"),
    });
  }, { scope: listRef, dependencies: [conversations] });

  if (!conversations || !conversations.length) {
    return (
      <div className="px-3 py-8 text-center">
        <p className="text-sm text-text-muted">No conversations yet</p>
      </div>
    );
  }

  return (
    <div ref={listRef} className="flex flex-col gap-0.5 px-2 py-2">
      {conversations.map((conv) => (
        <button
          key={conv.id}
          data-conv-id={conv.id}
          onClick={() => onSelect(conv.id)}
          className={cn(
            "w-full rounded-lg px-3 py-2.5 text-left motion-safe:transition-colors motion-safe:duration-200",
            conv.id === activeId
              ? "bg-accent/10 text-accent"
              : "text-text-secondary hover:text-text-primary hover:bg-bg-hover",
          )}
        >
          <p className="text-sm font-medium truncate">{conv.title || "Untitled"}</p>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-xs text-text-muted">
              {conv.message_count} messages
            </span>
            {conv.model_used && (
              <span className="text-xs text-text-muted font-mono">
                {conv.model_used}
              </span>
            )}
          </div>
        </button>
      ))}
    </div>
  );
}
