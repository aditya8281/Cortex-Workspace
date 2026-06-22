"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { motion } from "framer-motion";
import type { ModelRecommendation } from "@/shared/types";
import PickCard from "./PickCard";

interface TopPicksCarouselProps {
  recommendations: ModelRecommendation[];
  onDownload: (modelId: string, variant?: string) => void;
}

export default function TopPicksCarousel({ recommendations, onDownload }: TopPicksCarouselProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const top10 = recommendations.slice(0, 10);

  const next = useCallback(() => {
    setActiveIndex((prev) => (prev + 1) % top10.length);
  }, [top10.length]);

  const prev = useCallback(() => {
    setActiveIndex((prev) => (prev - 1 + top10.length) % top10.length);
  }, [top10.length]);

  // Auto-rotation
  useEffect(() => {
    if (isPaused || top10.length <= 1) return;
    timerRef.current = setInterval(next, 5000);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [isPaused, next, top10.length]);

  // Pause on tab hidden
  useEffect(() => {
    const handleVisibility = () => { setIsPaused(document.hidden); };
    document.addEventListener("visibilitychange", handleVisibility);
    return () => document.removeEventListener("visibilitychange", handleVisibility);
  }, []);

  // Keyboard navigation (scoped to container)
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") prev();
      if (e.key === "ArrowRight") next();
    };
    el.addEventListener("keydown", handleKey);
    return () => el.removeEventListener("keydown", handleKey);
  }, [next, prev]);

  if (top10.length === 0) return null;

  return (
    <div className="mb-7">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted mb-3 flex items-center gap-2">
        Best for your machine
        <span className="flex-1 h-px bg-white/[0.06]" />
      </div>

      <div
        ref={containerRef}
        tabIndex={0}
        className="relative outline-none"
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
      >
        <div className="overflow-hidden rounded-xl">
          <motion.div
            className="flex gap-4"
            animate={{ x: `-${activeIndex * 336}px` }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          >
            {top10.map((rec, i) => (
              <PickCard
                key={rec.model_id}
                recommendation={rec}
                isActive={i === activeIndex}
                onDownload={onDownload}
              />
            ))}
          </motion.div>
        </div>

        {/* Arrows */}
        <button
          aria-label="Previous"
          onClick={prev}
          className="absolute left-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full glass-panel border border-white/[0.1] flex items-center justify-center text-secondary hover:text-primary hover:border-accent transition-colors z-10"
        >
          ←
        </button>
        <button
          aria-label="Next"
          onClick={next}
          className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full glass-panel border border-white/[0.1] flex items-center justify-center text-secondary hover:text-primary hover:border-accent transition-colors z-10"
        >
          →
        </button>

        {/* Dots */}
        <div className="flex justify-center gap-1.5 mt-4">
          {top10.map((_, i) => (
            <button
              key={i}
              aria-label={`Go to slide ${i + 1}`}
              onClick={() => setActiveIndex(i)}
              className={`w-2 h-2 rounded-full transition-all ${
                i === activeIndex ? "bg-accent w-4" : "bg-white/20 hover:bg-white/40"
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
