"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { cn } from "../../lib/utils";

/* ── Types ── */

interface Neuron {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  isHub: boolean;
  phase: number;
  pulseSpeed: number;
  glowOpacity: number;
  lastSignalTime: number;
}

interface Signal {
  fromIdx: number;
  toIdx: number;
  progress: number;
  speed: number;
  chainDepth: number;
}

interface BurstState {
  nextBurstAt: number;
  inBurst: boolean;
  burstCount: number;
}

interface NeuralNetworkProps {
  className?: string;
  intensity?: "low" | "medium" | "high";
}

/* ── Config ── */

const INTENSITY_CONFIG = {
  low: { neurons: 30, hubPercent: 0.10, burstInterval: [4000, 8000] as const, chainChance: 0.20, burstSize: [1, 2] as const },
  medium: { neurons: 50, hubPercent: 0.10, burstInterval: [2000, 5000] as const, chainChance: 0.30, burstSize: [2, 3] as const },
  high: { neurons: 80, hubPercent: 0.12, burstInterval: [1500, 3000] as const, chainChance: 0.35, burstSize: [2, 4] as const },
} as const;

const CONNECTION_DIST_CENTER = 150;
const CONNECTION_DIST_EDGE = 200;
const HUB_RADIUS_MIN = 6;
const HUB_RADIUS_MAX = 10;
const REGULAR_RADIUS_MIN = 3;
const REGULAR_RADIUS_MAX = 5;
const DRIFT_SPEED_HUB = 0.08;
const DRIFT_SPEED_REGULAR = 0.15;
const SIGNAL_SPEED = 0.012;
const MAX_CHAIN_DEPTH = 3;
const SIGNAL_HEAD_RADIUS = 2.5;
const SIGNAL_TRAIL_LEN = 30;

type ConfigValue = (typeof INTENSITY_CONFIG)[keyof typeof INTENSITY_CONFIG];

/* ── Seeded random ── */

function seededRandom(seed: number) {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

/* ── Network construction ── */

function buildNetwork(
  count: number,
  hubPercent: number,
  width: number,
  height: number,
  rand: () => number,
): Neuron[] {
  const neurons: Neuron[] = [];
  const hubCount = Math.max(3, Math.floor(count * hubPercent));
  const regCount = count - hubCount;
  const cx = width / 2;
  const cy = height / 2;
  const spreadX = width * 0.35;
  const spreadY = height * 0.35;

  // Place hub neurons along the horizontal center line, distributed left→right
  for (let i = 0; i < hubCount; i++) {
    const t = (i + 0.5) / hubCount; // 0→1 left to right
    const x = cx - spreadX + t * spreadX * 2 + (rand() - 0.5) * 60;
    const y = cy + (rand() - 0.5) * spreadY * 0.8;
    const angle = rand() * Math.PI * 2;
    const speed = DRIFT_SPEED_HUB * (0.6 + rand() * 0.4);
    neurons.push({
      x, y,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      radius: HUB_RADIUS_MIN + rand() * (HUB_RADIUS_MAX - HUB_RADIUS_MIN),
      isHub: true,
      phase: rand() * Math.PI * 2,
      pulseSpeed: 0.15 + rand() * 0.1, // slower pulse
      glowOpacity: 0.45 + rand() * 0.15,
      lastSignalTime: 0,
    });
  }

  // Place regular neurons with central bias
  for (let i = 0; i < regCount; i++) {
    const angle = rand() * Math.PI * 2;
    const dist = Math.pow(rand(), 0.7); // central bias
    const x = cx + Math.cos(angle) * dist * spreadX * 1.2 + (rand() - 0.5) * 40;
    const y = cy + Math.sin(angle) * dist * spreadY * 1.2 + (rand() - 0.5) * 40;
    const vAngle = rand() * Math.PI * 2;
    const speed = DRIFT_SPEED_REGULAR * (0.5 + rand() * 0.5);
    neurons.push({
      x: Math.max(30, Math.min(width - 30, x)),
      y: Math.max(30, Math.min(height - 30, y)),
      vx: Math.cos(vAngle) * speed,
      vy: Math.sin(vAngle) * speed,
      radius: REGULAR_RADIUS_MIN + rand() * (REGULAR_RADIUS_MAX - REGULAR_RADIUS_MIN),
      isHub: false,
      phase: rand() * Math.PI * 2,
      pulseSpeed: 0.25 + rand() * 0.2, // faster pulse
      glowOpacity: 0.3 + rand() * 0.15,
      lastSignalTime: 0,
    });
  }

  return neurons;
}

/* ── Component ── */

export default function NeuralNetwork({
  className,
  intensity = "medium",
}: NeuralNetworkProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const neuronsRef = useRef<Neuron[]>([]);
  const signalsRef = useRef<Signal[]>([]);
  const burstRef = useRef<BurstState>({ nextBurstAt: 0, inBurst: false, burstCount: 0 });
  const animationRef = useRef<number>(0);
  const timeRef = useRef(0);
  const lastFrameRef = useRef(0);

  const [reducedMotion] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  });

  const config = INTENSITY_CONFIG[intensity];

  const animate = useCallback(
    (ctx: CanvasRenderingContext2D, width: number, height: number) => {
      const now = performance.now();
      const rawDt = lastFrameRef.current ? (now - lastFrameRef.current) / 16.667 : 1;
      const dt = Math.min(rawDt, 3); // cap to prevent jumps
      lastFrameRef.current = now;
      timeRef.current += 0.016 * dt;
      const t = timeRef.current * 1000; // ms

      ctx.clearRect(0, 0, width, height);
      const neurons = neuronsRef.current;
      const signals = signalsRef.current;
      const burst = burstRef.current;

      // ── 1. Update neuron positions ──
      for (const n of neurons) {
        n.x += n.vx * dt;
        n.y += n.vy * dt;

        const pad = 40;
        if (n.x < pad) n.vx = Math.abs(n.vx);
        if (n.x > width - pad) n.vx = -Math.abs(n.vx);
        if (n.y < pad) n.vy = Math.abs(n.vy);
        if (n.y > height - pad) n.vy = -Math.abs(n.vy);

        n.x = Math.max(pad, Math.min(width - pad, n.x));
        n.y = Math.max(pad, Math.min(height - pad, n.y));
      }

      // ── 2. Draw connections ──
      for (let i = 0; i < neurons.length; i++) {
        for (let j = i + 1; j < neurons.length; j++) {
          const a = neurons[i];
          const b = neurons[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          // Dynamic connection distance: tighter in center
          const midX = (a.x + b.x) / 2;
          const distFromCenter = Math.abs(midX - width / 2) / (width / 2);
          const maxDist = CONNECTION_DIST_CENTER + distFromCenter * (CONNECTION_DIST_EDGE - CONNECTION_DIST_CENTER);

          if (dist < maxDist) {
            const alpha = (1 - dist / maxDist) * 0.12;
            const isHubConnection = a.isHub || b.isHub;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.strokeStyle = `rgba(6, 182, 212, ${alpha * (isHubConnection ? 1.4 : 1)})`;
            ctx.lineWidth = isHubConnection ? 0.8 : 0.5;
            ctx.stroke();
          }
        }
      }

      // ── 3. Burst signal spawning ──
      if (t >= burst.nextBurstAt && !burst.inBurst) {
        burst.inBurst = true;
        const [minB, maxB] = config.burstSize;
        burst.burstCount = minB + Math.floor(Math.random() * (maxB - minB + 1));
      }

      if (burst.inBurst && burst.burstCount > 0) {
        // Spawn one signal from the burst
        burst.burstCount--;
        spawnSignal(neurons, signals, t, config);

        if (burst.burstCount <= 0) {
          burst.inBurst = false;
          const [minI, maxI] = config.burstInterval;
          burst.nextBurstAt = t + minI + Math.random() * (maxI - minI);
        }
      }

      // ── 4. Update and draw signals ──
      for (let s = signals.length - 1; s >= 0; s--) {
        const sig = signals[s];
        sig.progress += sig.speed * dt;

        if (sig.progress >= 1) {
          const target = neurons[sig.toIdx];
          if (target) {
            target.glowOpacity = Math.min(1, target.glowOpacity + 0.35);
            target.lastSignalTime = t;

            // Chain propagation
            if (sig.chainDepth < MAX_CHAIN_DEPTH && Math.random() < config.chainChance) {
              const chainTarget = findRightwardNeighbor(neurons, sig.toIdx, width);
              if (chainTarget !== -1) {
                signals.push({
                  fromIdx: sig.toIdx,
                  toIdx: chainTarget,
                  progress: 0,
                  speed: SIGNAL_SPEED * (0.8 + Math.random() * 0.4),
                  chainDepth: sig.chainDepth + 1,
                });
              }
            }
          }
          signals.splice(s, 1);
          continue;
        }

        const from = neurons[sig.fromIdx];
        const to = neurons[sig.toIdx];
        if (!from || !to) {
          signals.splice(s, 1);
          continue;
        }

        const x = from.x + (to.x - from.x) * sig.progress;
        const y = from.y + (to.y - from.y) * sig.progress;

        // Trail
        for (let ti = 0; ti < SIGNAL_TRAIL_LEN; ti++) {
          const trailProg = sig.progress - (ti / SIGNAL_TRAIL_LEN) * sig.speed * SIGNAL_TRAIL_LEN * 0.015;
          if (trailProg < 0) break;
          const tx = from.x + (to.x - from.x) * trailProg;
          const ty = from.y + (to.y - from.y) * trailProg;
          const trailAlpha = (1 - ti / SIGNAL_TRAIL_LEN) * 0.45;
          ctx.beginPath();
          ctx.arc(tx, ty, 1.5 - (ti / SIGNAL_TRAIL_LEN) * 1, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(6, 182, 212, ${trailAlpha})`;
          ctx.fill();
        }

        // Head
        ctx.beginPath();
        ctx.arc(x, y, SIGNAL_HEAD_RADIUS, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(6, 182, 212, 0.9)";
        ctx.fill();

        // Head glow
        const glow = ctx.createRadialGradient(x, y, 0, x, y, 10);
        glow.addColorStop(0, "rgba(6, 182, 212, 0.3)");
        glow.addColorStop(1, "rgba(6, 182, 212, 0)");
        ctx.beginPath();
        ctx.arc(x, y, 10, 0, Math.PI * 2);
        ctx.fillStyle = glow;
        ctx.fill();
      }

      // ── 5. Draw neurons ──
      for (const n of neurons) {
        const pulse = Math.sin(t / 1000 * n.pulseSpeed + n.phase) * 0.12;
        const currentRadius = n.radius * (1 + pulse);

        // Decay glow toward base
        const baseGlow = n.isHub ? 0.5 : 0.35;
        if (n.glowOpacity > baseGlow + 0.1) {
          n.glowOpacity -= 0.003 * dt;
        } else if (n.glowOpacity < baseGlow) {
          n.glowOpacity += 0.001 * dt;
        }

        // Outer glow
        const glowR = currentRadius * 3.5;
        const glow = ctx.createRadialGradient(n.x, n.y, currentRadius * 0.3, n.x, n.y, glowR);
        glow.addColorStop(0, `rgba(6, 182, 212, ${n.glowOpacity * 0.3})`);
        glow.addColorStop(1, "rgba(6, 182, 212, 0)");
        ctx.beginPath();
        ctx.arc(n.x, n.y, glowR, 0, Math.PI * 2);
        ctx.fillStyle = glow;
        ctx.fill();

        // Core
        ctx.beginPath();
        ctx.arc(n.x, n.y, currentRadius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(6, 182, 212, ${n.glowOpacity})`;
        ctx.fill();
      }

      animationRef.current = requestAnimationFrame(() => animate(ctx, width, height));
    },
    [config],
  );

  useEffect(() => {
    if (reducedMotion) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const rand = seededRandom(42);

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      if (neuronsRef.current.length === 0) {
        neuronsRef.current = buildNetwork(
          config.neurons,
          config.hubPercent,
          canvas.width,
          canvas.height,
          rand,
        );
        // Set initial burst time
        const [minI, maxI] = config.burstInterval;
        burstRef.current.nextBurstAt = performance.now() + minI + Math.random() * (maxI - minI);
      }
    };
    resize();
    window.addEventListener("resize", resize);

    lastFrameRef.current = 0;
    animate(ctx, canvas.width, canvas.height);

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(animationRef.current);
    };
  }, [reducedMotion, config, animate]);

  if (reducedMotion) {
    return (
      <div className={cn("pointer-events-none fixed inset-0 z-[-1]", className)}>
        <div className="h-full w-full bg-bg" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(6,182,212,0.04),transparent_70%)]" />
      </div>
    );
  }

  return (
    <canvas
      ref={canvasRef}
      className={cn("pointer-events-none fixed inset-0 z-[-1]", className)}
    />
  );
}

/* ── Helpers (module-level, no hooks) ── */

function spawnSignal(
  neurons: Neuron[],
  signals: Signal[],
  now: number,
  config: ConfigValue,
) {
  if (neurons.length < 2) return;

  // Weight toward left-side neurons (input side)
  const weights = neurons.map((n) => {
    const xRatio = n.x / (typeof window !== "undefined" ? window.innerWidth : 1200);
    return xRatio < 0.3 ? 3 : xRatio < 0.6 ? 1.5 : 0.5;
  });
  const totalWeight = weights.reduce((a, b) => a + b, 0);
  let r = Math.random() * totalWeight;
  let fromIdx = 0;
  for (let i = 0; i < weights.length; i++) {
    r -= weights[i];
    if (r <= 0) { fromIdx = i; break; }
  }

  // Find a connected neighbor, prefer rightward
  const from = neurons[fromIdx];
  let bestIdx = -1;
  let bestScore = -Infinity;
  const maxDist = 200;

  for (let j = 0; j < neurons.length; j++) {
    if (j === fromIdx) continue;
    const dx = neurons[j].x - from.x;
    const dy = neurons[j].y - from.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist > maxDist) continue;

    // Score: prefer rightward, penalize far
    const rightwardBonus = dx * 0.5;
    const distPenalty = dist * 0.3;
    const score = rightwardBonus - distPenalty;
    if (score > bestScore) {
      bestScore = score;
      bestIdx = j;
    }
  }

  if (bestIdx === -1) {
    // Fallback: any random neighbor
    const candidates = neurons
      .map((n, i) => ({ i, d: Math.hypot(n.x - from.x, n.y - from.y) }))
      .filter((c) => c.i !== fromIdx && c.d < maxDist);
    if (candidates.length === 0) return;
    bestIdx = candidates[Math.floor(Math.random() * candidates.length)].i;
  }

  from.lastSignalTime = now;
  signals.push({
    fromIdx,
    toIdx: bestIdx,
    progress: 0,
    speed: SIGNAL_SPEED * (0.8 + Math.random() * 0.4),
    chainDepth: 0,
  });
}

function findRightwardNeighbor(neurons: Neuron[], fromIdx: number, width: number): number {
  const from = neurons[fromIdx];
  let bestIdx = -1;
  let bestScore = -Infinity;

  for (let j = 0; j < neurons.length; j++) {
    if (j === fromIdx) continue;
    const dx = neurons[j].x - from.x;
    const dy = neurons[j].y - from.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist > 200) continue;

    // Strongly prefer rightward
    if (dx < -20) continue; // skip leftward
    const score = dx * 0.8 - dist * 0.2;
    if (score > bestScore) {
      bestScore = score;
      bestIdx = j;
    }
  }

  return bestIdx;
}
