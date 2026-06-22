# Models Page Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 927-line monolithic ModelsPage.tsx with a focused, component-based layout featuring a Netflix-style carousel, workload columns, catalog table, and installed bar.

**Architecture:** Decompose into 6 focused components. Each component owns its own data fetching and state. The orchestrator (ModelsPage) handles top-level data fetching and passes data down. Carousel auto-rotates with framer-motion animations. Catalog table filters client-side.

**Tech Stack:** React 19, Next.js 15 App Router, TypeScript, Tailwind CSS, framer-motion, vitest, @testing-library/react

## Global Constraints

- Next.js 15 App Router with `"use client"` directive on interactive components
- Tailwind CSS with design tokens from `DESIGN.md` (Warm Neural Dark)
- framer-motion for animations (spring physics, carousel transitions)
- vitest + @testing-library/react for tests
- All components in `frontend/app/models/` directory
- Follow existing code conventions (no comments, cn() utility, Card/Button from shared/ui)

---

## File Structure

| File | Responsibility |
|---|---|
| `frontend/app/models/ModelsPage.tsx` | Orchestrator: data fetching, state management, layout composition |
| `frontend/app/models/components/HardwareBar.tsx` | Compact hardware display + download indicator |
| `frontend/app/models/components/TopPicksCarousel.tsx` | Netflix-style carousel with auto-rotation |
| `frontend/app/models/components/PickCard.tsx` | Individual carousel card (fit score, variants, actions) |
| `frontend/app/models/components/WorkloadColumns.tsx` | 3-column workload recommendations |
| `frontend/app/models/components/CatalogTable.tsx` | Search, filter, table, pagination |
| `frontend/app/models/components/InstalledBar.tsx` | Collapsible installed models list |
| `frontend/app/models/components/ModelsPage.test.tsx` | Tests for all new components |

**Files to delete** (dead code from current design):
- `frontend/app/models/components/CompareModal.tsx`
- `frontend/app/models/components/CompareTray.tsx`
- `frontend/app/models/components/CategorySection.tsx`
- `frontend/app/models/components/RecommendedRow.tsx`
- `frontend/app/models/components/SearchBar.tsx`
- `frontend/app/models/components/ModelCard.tsx`
- `frontend/app/models/InstalledModelsPanel.tsx`
- `frontend/app/models/ModelBrowser.tsx`
- `frontend/app/models/HardwareOverview.tsx`
- `frontend/app/models/DownloadQueuePanel.tsx`

---

### Task 1: HardwareBar Component

**Files:**
- Create: `frontend/app/models/components/HardwareBar.tsx`
- Test: `frontend/app/models/components/ModelsPage.test.tsx`

**Interfaces:**
- Consumes: `HardwareProfile` from `@/shared/types`
- Produces: `<HardwareBar hardware={hardware} activeDownloads={number} />`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/app/models/components/ModelsPage.test.tsx
import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import HardwareBar from "./HardwareBar";

const mockHardware = {
  gpu: { available: true, name: "RTX 4090", type: "cuda", vram_gb: 24, vram_available_gb: 24, memory_bandwidth_gbps: 1008, compute_capability: "8.9", arch: "ada" },
  ram_gb: 64, ram_available_gb: 32, ram_percent: 50,
  cpu_count: 16, cpu_threads: 32, cpu_freq_mhz: 3500, cpu_arch: "x86_64",
  disk_free_gb: 200, supports_cuda: true, supports_metal: false,
};

describe("HardwareBar", () => {
  it("renders GPU name and VRAM", () => {
    render(<HardwareBar hardware={mockHardware} activeDownloads={0} />);
    expect(screen.getByText(/RTX 4090/)).toBeDefined();
    expect(screen.getByText(/24/)).toBeDefined();
  });

  it("shows CUDA badge when supports_cuda is true", () => {
    render(<HardwareBar hardware={mockHardware} activeDownloads={0} />);
    expect(screen.getByText(/CUDA/)).toBeDefined();
  });

  it("shows active download count when > 0", () => {
    render(<HardwareBar hardware={mockHardware} activeDownloads={3} />);
    expect(screen.getByText("3")).toBeDefined();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run app/models/components/ModelsPage.test.tsx`
Expected: FAIL — `HardwareBar` not found

- [ ] **Step 3: Implement HardwareBar**

```tsx
// frontend/app/models/components/HardwareBar.tsx
"use client";

import type { HardwareProfile } from "@/shared/types";

interface HardwareBarProps {
  hardware: HardwareProfile;
  activeDownloads: number;
}

export default function HardwareBar({ hardware, activeDownloads }: HardwareBarProps) {
  const gpu = hardware.gpu;
  const ramUsed = hardware.ram_gb - hardware.ram_available_gb;
  const ramPercent = Math.round((ramUsed / hardware.ram_gb) * 100);

  return (
    <div className="glass-panel rounded-xl px-5 py-3 flex items-center gap-8 mb-6">
      <div className="flex items-center gap-2">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-wider text-muted">GPU</div>
          <div className="text-[13px] font-medium">{gpu.available ? gpu.name : "No GPU"} · {gpu.vram_gb} GB</div>
        </div>
      </div>

      <div className="w-px h-6 bg-white/[0.06]" />

      <div className="flex items-center gap-2">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-wider text-muted">RAM</div>
          <div className="text-[13px] font-medium">{ramUsed}/{hardware.ram_gb} GB</div>
        </div>
        <div className="w-[60px] h-1 bg-surface rounded-full overflow-hidden">
          <div className="h-full bg-accent rounded-full" style={{ width: `${ramPercent}%` }} />
        </div>
      </div>

      <div className="w-px h-6 bg-white/[0.06]" />

      <div>
        <div className="font-mono text-[10px] uppercase tracking-wider text-muted">Disk</div>
        <div className="text-[13px] font-medium">{hardware.disk_free_gb} GB free</div>
      </div>

      <div className="w-px h-6 bg-white/[0.06]" />

      {hardware.supports_cuda && (
        <span className="font-mono text-[10px] px-2 py-0.5 rounded-md bg-success/10 text-success border border-success/20">
          CUDA
        </span>
      )}
      {hardware.supports_metal && (
        <span className="font-mono text-[10px] px-2 py-0.5 rounded-md bg-success/10 text-success border border-success/20">
          Metal
        </span>
      )}

      {activeDownloads > 0 && (
        <div className="ml-auto flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />
          <span className="font-mono text-[11px] text-accent">{activeDownloads} downloading</span>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run app/models/components/ModelsPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/app/models/components/HardwareBar.tsx frontend/app/models/components/ModelsPage.test.tsx
git commit -m "feat(models): add HardwareBar component"
```

---

### Task 2: PickCard Component

**Files:**
- Create: `frontend/app/models/components/PickCard.tsx`
- Test: `frontend/app/models/components/ModelsPage.test.tsx` (add tests)

**Interfaces:**
- Consumes: `ModelRecommendation` from `@/shared/types`, `isActive: boolean`, `onDownload: (modelId: string, variant?: string) => void`
- Produces: `<PickCard recommendation={rec} isActive={false} onDownload={fn} />`

- [ ] **Step 1: Write the failing test**

```tsx
// Add to frontend/app/models/components/ModelsPage.test.tsx
import PickCard from "./PickCard";

const mockRec = {
  model_id: "llama-3.1-8b",
  display_name: "Llama 3.1 8B",
  family: "llama",
  parameter_count: "8B",
  capabilities: ["chat", "reasoning"],
  description: "Best balance of speed and quality",
  score: 0.82,
  variant: { quantization: "Q5_K_M", size_gb: 4.2, vram_required_gb: 5.1, quality_score: 0.85 },
  performance: { tokens_per_second: 45, prompt_eval_tps: 52, memory_usage_gb: 4.2, vram_usage_gb: 5.1, quantization_quality: "high", quality_notes: "", speed_rating: "fast", fit_rating: "excellent", context_length_max: 128000 },
  explanation: { why: "Best balance for your hardware", tradeoff: "Slightly slower than Q4", suitability: "Excellent fit" },
};

describe("PickCard", () => {
  it("renders model name and fit score", () => {
    render(<PickCard recommendation={mockRec} isActive={true} onDownload={vi.fn()} />);
    expect(screen.getByText(/Llama 3.1 8B/)).toBeDefined();
    expect(screen.getByText(/82%/)).toBeDefined();
  });

  it("shows variant chips when active", () => {
    render(<PickCard recommendation={mockRec} isActive={true} onDownload={vi.fn()} />);
    expect(screen.getByText(/Q5_K_M/)).toBeDefined();
  });

  it("hides variant chips when not active", () => {
    render(<PickCard recommendation={mockRec} isActive={false} onDownload={vi.fn()} />);
    expect(screen.queryByText(/Q5_K_M/)).toBeNull();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run app/models/components/ModelsPage.test.tsx`
Expected: FAIL — `PickCard` not found

- [ ] **Step 3: Implement PickCard**

```tsx
// frontend/app/models/components/PickCard.tsx
"use client";

import type { ModelRecommendation } from "@/shared/types";

interface PickCardProps {
  recommendation: ModelRecommendation;
  isActive: boolean;
  onDownload: (modelId: string, variant?: string) => void;
}

export default function PickCard({ recommendation: rec, isActive, onDownload }: PickCardProps) {
  const fitPercent = Math.round(rec.score * 100);
  const variant = rec.variant;
  const perf = rec.performance;

  return (
    <div
      className={`min-w-[320px] max-w-[320px] rounded-xl border p-5 transition-all duration-300 ${
        isActive
          ? "border-accent bg-elevated shadow-[0_0_20px_rgba(14,165,201,0.15)] scale-[1.02]"
          : "border-white/[0.06] bg-elevated opacity-70"
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="font-mono text-[10px] text-muted uppercase">#{rec.score > 0.8 ? "Best" : "Top pick"}</div>
          <div className="text-[17px] font-semibold mt-1">{rec.display_name}</div>
          <div className="text-[12px] text-secondary mt-0.5">
            {rec.family} · {rec.parameter_count}
          </div>
        </div>
        <div className="font-mono text-[20px] font-bold text-accent-bright">{fitPercent}%</div>
      </div>

      {perf && (
        <div className="flex gap-4 text-[12px] text-secondary mb-3">
          <span><span className="text-primary font-medium">{perf.tokens_per_second}</span> t/s</span>
          <span><span className="text-primary font-medium">{variant?.size_gb}</span> GB</span>
          <span><span className="text-primary font-medium">{variant?.vram_required_gb}</span> GB VRAM</span>
        </div>
      )}

      <div className="w-full h-1.5 bg-surface rounded-full overflow-hidden mb-3">
        <div
          className="h-full rounded-full bg-gradient-to-r from-accent to-accent-bright"
          style={{ width: `${fitPercent}%` }}
        />
      </div>

      {rec.explanation?.why && (
        <p className="text-[12px] text-muted italic mb-4 line-clamp-2">&ldquo;{rec.explanation.why}&rdquo;</p>
      )}

      {isActive && variant && (
        <div className="flex gap-1.5 mb-4">
          {["Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0"].map((q) => (
            <button
              key={q}
              className={`font-mono text-[10px] px-2.5 py-1.5 rounded-md border transition-colors ${
                q === variant.quantization
                  ? "border-accent text-accent bg-accent/5"
                  : "border-white/[0.06] text-muted bg-surface hover:border-white/[0.1] hover:text-primary"
              }`}
            >
              {q}
            </button>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={() => onDownload(rec.model_id, variant?.quantization)}
          className="text-[12px] font-medium px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent-bright transition-colors"
        >
          Download
        </button>
        <button className="text-[12px] font-medium px-4 py-2 rounded-lg border border-white/[0.1] text-secondary hover:border-accent hover:text-primary transition-colors">
          Details →
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run app/models/components/ModelsPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/app/models/components/PickCard.tsx frontend/app/models/components/ModelsPage.test.tsx
git commit -m "feat(models): add PickCard component"
```

---

### Task 3: TopPicksCarousel Component

**Files:**
- Create: `frontend/app/models/components/TopPicksCarousel.tsx`
- Test: `frontend/app/models/components/ModelsPage.test.tsx` (add tests)

**Interfaces:**
- Consumes: `ModelRecommendation[]` (top 10), `onDownload: (modelId: string, variant?: string) => void`
- Produces: `<TopPicksCarousel recommendations={recs} onDownload={fn} />`

- [ ] **Step 1: Write the failing test**

```tsx
// Add to frontend/app/models/components/ModelsPage.test.tsx
import TopPicksCarousel from "./TopPicksCarousel";

const mockRecs = Array.from({ length: 10 }, (_, i) => ({
  ...mockRec,
  model_id: `model-${i}`,
  display_name: `Model ${i}`,
  score: 0.9 - i * 0.05,
}));

describe("TopPicksCarousel", () => {
  it("renders all recommendation cards", () => {
    render(<TopPicksCarousel recommendations={mockRecs} onDownload={vi.fn()} />);
    expect(screen.getByText(/Model 0/)).toBeDefined();
    expect(screen.getByText(/Model 9/)).toBeDefined();
  });

  it("shows navigation arrows", () => {
    render(<TopPicksCarousel recommendations={mockRecs} onDownload={vi.fn()} />);
    expect(screen.getByRole("button", { name: /previous/i })).toBeDefined();
    expect(screen.getByRole("button", { name: /next/i })).toBeDefined();
  });

  it("shows dot indicators", () => {
    render(<TopPicksCarousel recommendations={mockRecs} onDownload={vi.fn()} />);
    const dots = screen.getAllByRole("button", { name: /go to slide/i });
    expect(dots.length).toBe(10);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run app/models/components/ModelsPage.test.tsx`
Expected: FAIL — `TopPicksCarousel` not found

- [ ] **Step 3: Implement TopPicksCarousel**

```tsx
// frontend/app/models/components/TopPicksCarousel.tsx
"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
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

  // Keyboard navigation
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") prev();
      if (e.key === "ArrowRight") next();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
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
        className="relative"
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run app/models/components/ModelsPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/app/models/components/TopPicksCarousel.tsx frontend/app/models/components/ModelsPage.test.tsx
git commit -m "feat(models): add TopPicksCarousel with auto-rotation"
```

---

### Task 4: WorkloadColumns Component

**Files:**
- Create: `frontend/app/models/components/WorkloadColumns.tsx`
- Test: `frontend/app/models/components/ModelsPage.test.tsx` (add tests)

**Interfaces:**
- Consumes: `Record<string, WorkloadRecommendations>`, `onDownload: (modelId: string, variant?: string) => void`
- Produces: `<WorkloadColumns workloads={workloads} onDownload={fn} />`

- [ ] **Step 1: Write the failing test**

```tsx
// Add to frontend/app/models/components/ModelsPage.test.tsx
import WorkloadColumns from "./WorkloadColumns";

const mockWorkloads = {
  chat: { label: "Chat", description: "Conversational AI", recommendations: [mockRec, { ...mockRec, model_id: "phi-3", display_name: "Phi-3 14B", score: 0.75 }] },
  code: { label: "Code", description: "Code generation", recommendations: [{ ...mockRec, model_id: "codestral", display_name: "Codestral 7B", score: 0.78 }] },
};

describe("WorkloadColumns", () => {
  it("renders workload headers", () => {
    render(<WorkloadColumns workloads={mockWorkloads} onDownload={vi.fn()} />);
    expect(screen.getByText("Chat")).toBeDefined();
    expect(screen.getByText("Code")).toBeDefined();
  });

  it("renders top 3 models per workload", () => {
    render(<WorkloadColumns workloads={mockWorkloads} onDownload={vi.fn()} />);
    expect(screen.getByText(/Llama 3.1 8B/)).toBeDefined();
    expect(screen.getByText(/Phi-3 14B/)).toBeDefined();
    expect(screen.getByText(/Codestral 7B/)).toBeDefined();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run app/models/components/ModelsPage.test.tsx`
Expected: FAIL — `WorkloadColumns` not found

- [ ] **Step 3: Implement WorkloadColumns**

```tsx
// frontend/app/models/components/WorkloadColumns.tsx
"use client";

import type { WorkloadRecommendations } from "@/shared/types";

interface WorkloadColumnsProps {
  workloads: Record<string, WorkloadRecommendations>;
  onDownload: (modelId: string, variant?: string) => void;
}

const WORKLOAD_ICONS: Record<string, string> = {
  chat: "💬",
  code: "💻",
  vision: "👁",
};

export default function WorkloadColumns({ workloads, onDownload }: WorkloadColumnsProps) {
  const entries = Object.entries(workloads);
  if (entries.length === 0) return null;

  return (
    <div className="mb-7">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted mb-3 flex items-center gap-2">
        By workload
        <span className="flex-1 h-px bg-white/[0.06]" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {entries.map(([key, wl]) => (
          <div key={key} className="glass-panel rounded-xl overflow-hidden">
            <div className="px-4 py-3 border-b border-white/[0.06] flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-accent/10 flex items-center justify-center text-sm">
                {WORKLOAD_ICONS[key] || "🤖"}
              </div>
              <div className="text-[13px] font-semibold">{wl.label}</div>
            </div>
            {wl.recommendations.slice(0, 3).map((rec) => {
              const fit = Math.round(rec.score * 100);
              const fitColor = fit >= 75 ? "text-success" : fit >= 60 ? "text-accent" : "text-muted";
              return (
                <div key={rec.model_id} className="px-4 py-3 border-b border-white/[0.06] last:border-b-0 flex justify-between items-center hover:bg-white/[0.02] transition-colors">
                  <div>
                    <div className="text-[13px] font-medium">{rec.display_name}</div>
                    <div className="font-mono text-[10px] text-muted">
                      {rec.variant?.quantization} · {rec.variant?.size_gb} GB
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`font-mono text-[12px] font-medium ${fitColor}`}>{fit}%</div>
                    <div className="font-mono text-[10px] text-muted">{rec.performance?.tokens_per_second} t/s</div>
                    <button
                      onClick={() => onDownload(rec.model_id, rec.variant?.quantization)}
                      className="text-[10px] px-2.5 py-1 mt-1 rounded-md border border-accent/30 text-accent hover:bg-accent/5 transition-colors"
                    >
                      Download
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run app/models/components/ModelsPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/app/models/components/WorkloadColumns.tsx frontend/app/models/components/ModelsPage.test.tsx
git commit -m "feat(models): add WorkloadColumns component"
```

---

### Task 5: CatalogTable Component

**Files:**
- Create: `frontend/app/models/components/CatalogTable.tsx`
- Test: `frontend/app/models/components/ModelsPage.test.tsx` (add tests)

**Interfaces:**
- Consumes: `ModelInfo[]`, `onDownload: (modelName: string) => void`
- Produces: `<CatalogTable models={allModels} onDownload={fn} />`

- [ ] **Step 1: Write the failing test**

```tsx
// Add to frontend/app/models/components/ModelsPage.test.tsx
import CatalogTable from "./CatalogTable";

const mockModels = [
  { model_id: "llama-3.1-8b", name: "llama-3.1-8b", display_name: "Llama 3.1 8B", description: "", provider: "Meta", model_type: "chat" as const, parameter_count: "8B", context_length: 128000, capabilities: [], hardware_requirements: null, recommended: false, downloaded: false, size_bytes: 4500000000, variants: ["Q4_K_M", "Q5_K_M"], family: "llama", architecture: "transformer", license: "llama" },
  { model_id: "codestral-7b", name: "codestral-7b", display_name: "Codestral 7B", description: "", provider: "Mistral", model_type: "code" as const, parameter_count: "7B", context_length: 32000, capabilities: [], hardware_requirements: null, recommended: false, downloaded: false, size_bytes: 5100000000, variants: ["Q6_K"], family: "codestral", architecture: "transformer", license: "apache" },
];

describe("CatalogTable", () => {
  it("renders model names", () => {
    render(<CatalogTable models={mockModels} onDownload={vi.fn()} />);
    expect(screen.getByText("Llama 3.1 8B")).toBeDefined();
    expect(screen.getByText("Codestral 7B")).toBeDefined();
  });

  it("renders filter pills", () => {
    render(<CatalogTable models={mockModels} onDownload={vi.fn()} />);
    expect(screen.getByText("All")).toBeDefined();
    expect(screen.getByText("Chat")).toBeDefined();
    expect(screen.getByText("Code")).toBeDefined();
  });

  it("filters by type when pill is clicked", async () => {
    render(<CatalogTable models={mockModels} onDownload={vi.fn()} />);
    fireEvent.click(screen.getByText("Code"));
    await waitFor(() => {
      expect(screen.getByText("Codestral 7B")).toBeDefined();
      expect(screen.queryByText("Llama 3.1 8B")).toBeNull();
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run app/models/components/ModelsPage.test.tsx`
Expected: FAIL — `CatalogTable` not found

- [ ] **Step 3: Implement CatalogTable**

```tsx
// frontend/app/models/components/CatalogTable.tsx
"use client";

import { useState, useMemo } from "react";
import type { ModelInfo } from "@/shared/types";

interface CatalogTableProps {
  models: ModelInfo[];
  onDownload: (modelName: string) => void;
}

const TYPE_FILTERS = ["All", "Chat", "Code", "Vision", "Embed"] as const;
const SIZE_FILTERS = ["All", "≤3B", "3-8B", "8-14B", "14B+"] as const;

function matchesSizeFilter(paramCount: string, filter: string): boolean {
  if (filter === "All") return true;
  const match = paramCount.match(/([\d.]+)B/);
  if (!match) return false;
  const num = parseFloat(match[1]);
  switch (filter) {
    case "≤3B": return num <= 3;
    case "3-8B": return num > 3 && num <= 8;
    case "8-14B": return num > 8 && num <= 14;
    case "14B+": return num > 14;
    default: return true;
  }
}

export default function CatalogTable({ models, onDownload }: CatalogTableProps) {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("All");
  const [sizeFilter, setSizeFilter] = useState<string>("All");
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 20;

  const filtered = useMemo(() => {
    return models.filter((m) => {
      if (search && !m.display_name.toLowerCase().includes(search.toLowerCase())) return false;
      if (typeFilter !== "All" && m.model_type.toLowerCase() !== typeFilter.toLowerCase()) return false;
      if (!matchesSizeFilter(m.parameter_count, sizeFilter)) return false;
      return true;
    });
  }, [models, search, typeFilter, sizeFilter]);

  const pageCount = Math.ceil(filtered.length / PAGE_SIZE);
  const paged = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div className="mb-7">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted mb-3 flex items-center gap-2">
        Browse all models
        <span className="flex-1 h-px bg-white/[0.06]" />
      </div>

      <div className="glass-panel rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-white/[0.06] flex gap-2 items-center flex-wrap">
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0); }}
            placeholder="Search models..."
            className="flex-1 min-w-[200px] font-inter text-[13px] px-3 py-2 rounded-lg border border-white/[0.06] bg-surface text-primary outline-none focus:border-accent placeholder:text-muted"
          />
          {TYPE_FILTERS.map((t) => (
            <button
              key={t}
              onClick={() => { setTypeFilter(t); setPage(0); }}
              className={`font-mono text-[10px] px-2.5 py-1.5 rounded-md border transition-colors ${
                typeFilter === t
                  ? "border-accent text-accent bg-accent/5"
                  : "border-white/[0.06] text-muted hover:border-white/[0.1] hover:text-primary"
              }`}
            >
              {t}
            </button>
          ))}
          <div className="w-px h-4 bg-white/[0.06] mx-1" />
          {SIZE_FILTERS.map((s) => (
            <button
              key={s}
              onClick={() => { setSizeFilter(s); setPage(0); }}
              className={`font-mono text-[10px] px-2.5 py-1.5 rounded-md border transition-colors ${
                sizeFilter === s
                  ? "border-accent text-accent bg-accent/5"
                  : "border-white/[0.06] text-muted hover:border-white/[0.1] hover:text-primary"
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/[0.06]">
                <th className="font-mono text-[9px] uppercase tracking-wider text-muted px-4 py-2.5 text-left">Model</th>
                <th className="font-mono text-[9px] uppercase tracking-wider text-muted px-4 py-2.5 text-left">Type</th>
                <th className="font-mono text-[9px] uppercase tracking-wider text-muted px-4 py-2.5 text-left">Params</th>
                <th className="font-mono text-[9px] uppercase tracking-wider text-muted px-4 py-2.5 text-left">Size</th>
                <th className="font-mono text-[9px] uppercase tracking-wider text-muted px-4 py-2.5 text-left">Fit</th>
                <th className="font-mono text-[9px] uppercase tracking-wider text-muted px-4 py-2.5 text-left"></th>
              </tr>
            </thead>
            <tbody>
              {paged.map((m) => (
                <tr key={m.model_id} className="border-b border-white/[0.06] last:border-b-0 hover:bg-white/[0.02] transition-colors">
                  <td className="px-4 py-2.5 text-[12px] font-medium">{m.display_name}</td>
                  <td className="px-4 py-2.5">
                    <span className={`font-mono text-[9px] px-2 py-0.5 rounded ${
                      m.model_type === "chat" ? "bg-accent/8 text-accent" :
                      m.model_type === "code" ? "bg-purple-500/8 text-purple-400" :
                      "bg-warning/8 text-warning"
                    }`}>
                      {m.model_type}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 font-mono text-[11px]">{m.parameter_count}</td>
                  <td className="px-4 py-2.5 font-mono text-[11px]">{m.size_bytes ? `${(m.size_bytes / 1e9).toFixed(1)} GB` : "—"}</td>
                  <td className="px-4 py-2.5 font-mono text-[11px] text-accent">—</td>
                  <td className="px-4 py-2.5">
                    <button
                      onClick={() => onDownload(m.name)}
                      className="text-[10px] px-2.5 py-1 rounded-md border border-accent/30 text-accent hover:bg-accent/5 transition-colors"
                    >
                      ↓
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="px-4 py-3 border-t border-white/[0.06] flex justify-between items-center text-[12px] text-muted">
          <span>Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, filtered.length)} of {filtered.length} models</span>
          <div className="flex gap-1">
            {Array.from({ length: Math.min(pageCount, 5) }, (_, i) => (
              <button
                key={i}
                onClick={() => setPage(i)}
                className={`font-mono text-[11px] px-2.5 py-1 rounded-md border transition-colors ${
                  page === i
                    ? "border-accent text-accent"
                    : "border-white/[0.06] text-secondary hover:border-white/[0.1]"
                }`}
              >
                {i + 1}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run app/models/components/ModelsPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/app/models/components/CatalogTable.tsx frontend/app/models/components/ModelsPage.test.tsx
git commit -m "feat(models): add CatalogTable with search, filter, pagination"
```

---

### Task 6: InstalledBar Component

**Files:**
- Create: `frontend/app/models/components/InstalledBar.tsx`
- Test: `frontend/app/models/components/ModelsPage.test.tsx` (add tests)

**Interfaces:**
- Consumes: installed models data, `onManage: () => void`, `onChat: (modelId: string) => void`, `onDelete: (modelId: string) => void`
- Produces: `<InstalledBar models={installed} onManage={fn} onChat={fn} onDelete={fn} />`

- [ ] **Step 1: Write the failing test**

```tsx
// Add to frontend/app/models/components/ModelsPage.test.tsx
import InstalledBar from "./InstalledBar";

const mockInstalled = [
  { model_id: "llama-3.1-8b", display_name: "Llama 3.1 8B", variant: "Q5_K_M", size_gb: 4.2, last_used: "2h ago", usage_count: 1247 },
  { model_id: "codestral-7b", display_name: "Codestral 7B", variant: "Q6_K", size_gb: 5.1, last_used: "1d ago", usage_count: 89 },
];

describe("InstalledBar", () => {
  it("renders model count and storage", () => {
    render(<InstalledBar models={mockInstalled} onManage={vi.fn()} onChat={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.getByText(/2 models/)).toBeDefined();
    expect(screen.getByText(/9.3 GB/)).toBeDefined();
  });

  it("expands to show model list on click", async () => {
    render(<InstalledBar models={mockInstalled} onManage={vi.fn()} onChat={vi.fn()} onDelete={vi.fn()} />);
    fireEvent.click(screen.getByText(/2 models/));
    await waitFor(() => {
      expect(screen.getByText(/Llama 3.1 8B/)).toBeDefined();
      expect(screen.getByText(/Codestral 7B/)).toBeDefined();
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run app/models/components/ModelsPage.test.tsx`
Expected: FAIL — `InstalledBar` not found

- [ ] **Step 3: Implement InstalledBar**

```tsx
// frontend/app/models/components/InstalledBar.tsx
"use client";

import { useState } from "react";

interface InstalledModel {
  model_id: string;
  display_name: string;
  variant: string;
  size_gb: number;
  last_used: string;
  usage_count: number;
}

interface InstalledBarProps {
  models: InstalledModel[];
  onManage: () => void;
  onChat: (modelId: string) => void;
  onDelete: (modelId: string) => void;
}

export default function InstalledBar({ models, onManage, onChat, onDelete }: InstalledBarProps) {
  const [expanded, setExpanded] = useState(false);
  const totalSize = models.reduce((sum, m) => sum + m.size_gb, 0);

  return (
    <div className="glass-panel rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/[0.02] transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <span className="font-mono text-[11px] px-2.5 py-0.5 rounded bg-accent/10 text-accent">
            {models.length} models
          </span>
          <span className="font-mono text-[11px] text-muted">{totalSize.toFixed(1)} GB used</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={(e) => { e.stopPropagation(); onManage(); }}
            className="text-[11px] text-accent hover:text-accent-bright transition-colors"
          >
            Manage →
          </button>
          <span className="text-muted text-sm">{expanded ? "▴" : "▾"}</span>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-white/[0.06]">
          {models.map((m) => (
            <div key={m.model_id} className="px-4 py-2.5 flex justify-between items-center border-b border-white/[0.06] last:border-b-0 hover:bg-white/[0.02]">
              <div>
                <div className="text-[12px] font-medium">{m.display_name} · {m.variant}</div>
                <div className="font-mono text-[10px] text-muted">{m.size_gb} GB · Last used {m.last_used} · {m.usage_count.toLocaleString()} requests</div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => onChat(m.model_id)}
                  className="text-[10px] px-2.5 py-1 rounded-md border border-white/[0.1] text-secondary hover:border-accent hover:text-primary transition-colors"
                >
                  Chat
                </button>
                <button
                  onClick={() => onDelete(m.model_id)}
                  className="text-[10px] px-2 py-1 rounded-md border border-danger/20 text-danger hover:bg-danger/5 transition-colors"
                >
                  🗑
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run app/models/components/ModelsPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/app/models/components/InstalledBar.tsx frontend/app/models/components/ModelsPage.test.tsx
git commit -m "feat(models): add InstalledBar component"
```

---

### Task 7: ModelsPage Orchestrator

**Files:**
- Modify: `frontend/app/models/ModelsPage.tsx` (rewrite)
- Test: `frontend/app/models/page.test.tsx` (update existing tests)

**Interfaces:**
- Consumes: All components from Tasks 1-6
- Produces: Complete page layout

- [ ] **Step 1: Update existing page test**

The existing `page.test.tsx` tests the old ModelsPage. Update it to test the new structure:

```tsx
// Update frontend/app/models/page.test.tsx
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ModelsPage from "./ModelsPage";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
}));

vi.mock("@/shared/auth/AuthProvider", () => ({
  useAuth: () => ({
    user: { id: 1, username: "testuser", full_name: "Test User", role: "user", nickname: "tester", bio: null, description: null, profile_photo: null, handles: null, storage_root: null, github_username: null, preferences: null, created_at: null, updated_at: null },
    loading: false,
    login: vi.fn(),
  }),
}));

const mockRecommendedEnhanced = vi.fn();
const mockList = vi.fn();
const mockInstalled = vi.fn();

vi.mock("@/shared/api", () => ({
  modelsApi: {
    recommendedEnhanced: (...args: unknown[]) => mockRecommendedEnhanced(...args),
    list: (...args: unknown[]) => mockList(...args),
    installed: (...args: unknown[]) => mockInstalled(...args),
    download: vi.fn().mockResolvedValue({ status: "started" }),
    autocomplete: vi.fn().mockResolvedValue({ suggestions: [] }),
    hardware: vi.fn().mockResolvedValue({}),
    health: vi.fn().mockResolvedValue({}),
    metrics: vi.fn().mockResolvedValue({}),
    progress: vi.fn().mockResolvedValue({ model: "", progress: 0 }),
    cancel: vi.fn().mockResolvedValue({ cancelled: true }),
    storage: vi.fn().mockResolvedValue({ total_disk_gb: 0, used_disk_gb: 0, free_disk_gb: 0, models_total_gb: 0, models: [], cache_gb: 0 }),
    refreshCatalogue: vi.fn().mockResolvedValue({ status: "ok", models_added: 0 }),
  },
}));

vi.mock("@/shared/hooks/useSystemWebSocket", () => ({
  useSystemWebSocket: () => ({ messages: [] }),
}));

describe("ModelsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRecommendedEnhanced.mockResolvedValue({
      hardware: {
        gpu: { available: true, name: "RTX 4090", type: "cuda", vram_gb: 24, vram_available_gb: 24, memory_bandwidth_gbps: 1008, compute_capability: "8.9", arch: "ada" },
        ram_gb: 64, ram_available_gb: 32, ram_percent: 50,
        cpu_count: 16, cpu_threads: 32, cpu_freq_mhz: 3500, cpu_arch: "x86_64",
        disk_free_gb: 200, supports_cuda: true, supports_metal: false,
      },
      workloads: {
        chat: { label: "Chat", description: "Conversational AI", recommendations: [] },
      },
    });
    mockList.mockResolvedValue({ models: [], total_count: 0, downloaded_count: 0, available_from_providers: [], type_counts: {}, size_counts: {} });
    mockInstalled.mockResolvedValue({ models: [], installed_count: 0 });
  });

  it("renders the page title", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByText("Models")).toBeDefined();
    });
  });

  it("renders hardware bar with GPU info", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByText(/RTX 4090/)).toBeDefined();
    });
  });

  it("renders catalog section", async () => {
    render(<ModelsPage />);
    await waitFor(() => {
      expect(screen.getByText(/Browse all models/)).toBeDefined();
    });
  });
});
```

- [ ] **Step 2: Rewrite ModelsPage.tsx**

```tsx
// frontend/app/models/ModelsPage.tsx
"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Brain } from "lucide-react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { modelsApi } from "@/shared/api";
import { useSystemWebSocket } from "@/shared/hooks/useSystemWebSocket";
import type { HardwareProfile, ModelInfo, ModelRecommendation } from "@/shared/types";
import HardwareBar from "./components/HardwareBar";
import TopPicksCarousel from "./components/TopPicksCarousel";
import WorkloadColumns from "./components/WorkloadColumns";
import CatalogTable from "./components/CatalogTable";
import InstalledBar from "./components/InstalledBar";

export default function ModelsPage() {
  const router = useRouter();
  const { user } = useAuth();

  const [hardware, setHardware] = useState<HardwareProfile | null>(null);
  const [workloads, setWorkloads] = useState<Record<string, { label: string; description: string; recommendations: ModelRecommendation[] }>>({});
  const [allModels, setAllModels] = useState<ModelInfo[]>([]);
  const [installedModels, setInstalledModels] = useState<Array<{ model_id: string; display_name: string; variant: string; size_gb: number; last_used: string; usage_count: number }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadingModels, setDownloadingModels] = useState<Set<string>>(new Set());

  const { messages } = useSystemWebSocket({ path: "/ws/models", enabled: downloadingModels.size > 0 });

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [recs, list, inst] = await Promise.all([
        modelsApi.recommendedEnhanced(),
        modelsApi.list(),
        modelsApi.installed(),
      ]);
      setHardware(recs.hardware);
      setWorkloads(recs.workloads);
      setAllModels(list.models);
      setInstalledModels(inst.models || []);
    } catch (e) {
      setError("Failed to load models. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Handle download progress via WebSocket
  useEffect(() => {
    if (!messages.length) return;
    const last = messages[messages.length - 1];
    if (last.type === "model_progress") {
      const progress = last.data as Array<{ name: string; progress: number }>;
      progress.forEach((p) => {
        if (p.progress >= 1.0) {
          setDownloadingModels((prev) => {
            const next = new Set(prev);
            next.delete(p.name);
            return next;
          });
          fetchData();
        }
      });
    }
  }, [messages, fetchData]);

  const topRecs = useMemo(() => {
    const all: ModelRecommendation[] = [];
    Object.values(workloads).forEach((wl) => all.push(...wl.recommendations));
    return all.sort((a, b) => b.score - a.score).slice(0, 10);
  }, [workloads]);

  const handleDownload = useCallback(async (modelId: string, variant?: string) => {
    try {
      setDownloadingModels((prev) => new Set(prev).add(modelId));
      await modelsApi.download(modelId, variant);
    } catch {
      setDownloadingModels((prev) => {
        const next = new Set(prev);
        next.delete(modelId);
        return next;
      });
    }
  }, []);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="space-y-4">
          <div className="h-12 bg-elevated rounded-xl shimmer-bg" />
          <div className="h-48 bg-elevated rounded-xl shimmer-bg" />
          <div className="h-64 bg-elevated rounded-xl shimmer-bg" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="text-center py-20">
          <p className="text-secondary mb-4">{error}</p>
          <button onClick={fetchData} className="text-accent hover:text-accent-bright transition-colors">
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-6 relative z-10">
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        {/* Page Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center">
            <Brain className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h1 className="text-xl font-semibold">Models</h1>
            <p className="text-[13px] text-secondary">Browse, download, and manage LLM models</p>
          </div>
        </div>

        {/* Hardware Bar */}
        {hardware && <HardwareBar hardware={hardware} activeDownloads={downloadingModels.size} />}

        {/* Top Picks Carousel */}
        {topRecs.length > 0 && <TopPicksCarousel recommendations={topRecs} onDownload={handleDownload} />}

        {/* Workload Columns */}
        {Object.keys(workloads).length > 0 && <WorkloadColumns workloads={workloads} onDownload={handleDownload} />}

        {/* Catalog Table */}
        <CatalogTable models={allModels} onDownload={handleDownload} />

        {/* Installed Bar */}
        <InstalledBar
          models={installedModels}
          onManage={() => router.push("/settings")}
          onChat={(modelId) => router.push(`/chat?model=${modelId}`)}
          onDelete={(modelId) => { modelsApi.delete(modelId).then(fetchData); }}
        />
      </motion.div>
    </div>
  );
}
```

- [ ] **Step 3: Run all tests**

Run: `cd frontend && npx vitest run`
Expected: ALL PASS

- [ ] **Step 4: Run TypeScript check**

Run: `cd frontend && npx --no-install tsc --noEmit`
Expected: No errors in models/ files

- [ ] **Step 5: Commit**

```bash
git add frontend/app/models/ModelsPage.tsx frontend/app/models/page.test.tsx
git commit -m "feat(models): rewrite ModelsPage as focused layout orchestrator"
```

---

### Task 8: Clean Up Dead Components

**Files:**
- Delete: `frontend/app/models/components/CompareModal.tsx`
- Delete: `frontend/app/models/components/CompareTray.tsx`
- Delete: `frontend/app/models/components/CategorySection.tsx`
- Delete: `frontend/app/models/components/RecommendedRow.tsx`
- Delete: `frontend/app/models/components/SearchBar.tsx`
- Delete: `frontend/app/models/components/ModelCard.tsx`
- Delete: `frontend/app/models/InstalledModelsPanel.tsx`
- Delete: `frontend/app/models/ModelBrowser.tsx`
- Delete: `frontend/app/models/HardwareOverview.tsx`
- Delete: `frontend/app/models/DownloadQueuePanel.tsx`

- [ ] **Step 1: Delete dead files**

```bash
cd frontend
rm -f app/models/components/CompareModal.tsx
rm -f app/models/components/CompareTray.tsx
rm -f app/models/components/CategorySection.tsx
rm -f app/models/components/RecommendedRow.tsx
rm -f app/models/components/SearchBar.tsx
rm -f app/models/components/ModelCard.tsx
rm -f app/models/InstalledModelsPanel.tsx
rm -f app/models/ModelBrowser.tsx
rm -f app/models/HardwareOverview.tsx
rm -f app/models/DownloadQueuePanel.tsx
```

- [ ] **Step 2: Verify no remaining imports**

Run: `cd frontend && npx --no-install tsc --noEmit 2>&1 | grep -E "CompareModal|CompareTray|CategorySection|RecommendedRow|SearchBar|ModelCard|InstalledModelsPanel|ModelBrowser|HardwareOverview|DownloadQueuePanel"`
Expected: No output (no remaining imports)

- [ ] **Step 3: Run all tests**

Run: `cd frontend && npx vitest run`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add -A frontend/app/models/
git commit -m "chore(models): remove dead components from old design"
```

---

### Task 9: Final Validation

- [ ] **Step 1: Run all backend tests**

Run: `cd /home/adi/Desktop/Cortex-Workspace && python -m pytest backend/tests/ -x -q`
Expected: ALL PASS

- [ ] **Step 2: Run all frontend tests**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npx vitest run`
Expected: ALL PASS

- [ ] **Step 3: Run TypeScript check**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npx --no-install tsc --noEmit`
Expected: No new errors in models/ files

- [ ] **Step 4: Run ruff lint**

Run: `cd /home/adi/Desktop/Cortex-Workspace && python -m ruff check backend/`
Expected: No new errors

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat(models): complete Models page redesign — Focused Intelligence

- Netflix-style TopPicksCarousel with auto-rotation and 10 ranked cards
- WorkloadColumns showing top 3 per category (Chat, Code, Vision)
- CatalogTable with search, type/size filters, pagination
- InstalledBar with expandable model list
- HardwareBar with GPU/RAM/Disk display
- Removed 10 dead components (CompareTray, CompareModal, etc.)
- All new components have unit tests
- Decomposed 927-line monolith into 6 focused components (~810 lines)"
```
