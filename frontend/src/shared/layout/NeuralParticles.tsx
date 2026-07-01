"use client";

import { useEffect, useRef } from "react";

// ── Constants ─────────────────────────────────────────────────────────
const PARTICLE_COUNT = 35;
const CONNECTION_DIST = 150;
const PARTICLE_RADIUS = 1.5;
const FADE_SPEED = 0.003;
const MAX_OPACITY = 0.35;
const FAR_OPACITY = 0.015;

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  opacity: number;
  phase: number; // for slow sine-drift
}

// ── Component ─────────────────────────────────────────────────────────
export function NeuralParticles() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const animRef = useRef<number>(0);
  const mountedRef = useRef(true);

  useEffect(() => {
    // Respect reduced motion — fully remove
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (mq.matches) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let w = 0;
    let h = 0;

    function resize() {
      if (!canvas) return;
      w = window.innerWidth;
      h = window.innerHeight;
      canvas.width = w;
      canvas.height = h;
    }
    resize();
    window.addEventListener("resize", resize);

    // Init particles
    const particles: Particle[] = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        opacity: Math.random() * MAX_OPACITY,
        phase: Math.random() * Math.PI * 2,
      });
    }
    particlesRef.current = particles;

    // Throttle full updates — round-robin per frame
    let tick = 0;

    function draw() {
      if (!mountedRef.current) return;
      ctx!.clearRect(0, 0, w, h);

      // Only update subset of particles per frame for performance
      const subsetSize = Math.ceil(PARTICLE_COUNT / 3);
      const start = (tick % 3) * subsetSize;
      const end = Math.min(start + subsetSize, PARTICLE_COUNT);

      for (let i = start; i < end; i++) {
        const p = particles[i];
        // Sine drift for organic movement
        p.phase += FADE_SPEED;
        const drift = Math.sin(p.phase) * 0.1;

        p.x += p.vx + drift;
        p.y += p.vy;

        // Wrap edges
        if (p.x < -20) p.x = w + 20;
        if (p.x > w + 20) p.x = -20;
        if (p.y < -20) p.y = h + 20;
        if (p.y > h + 20) p.y = -20;

        // Slow opacity wave
        p.opacity = MAX_OPACITY * (0.5 + 0.5 * Math.sin(p.phase));
      }
      tick++;

      // ── Draw particles ────────────────────────────────────────
      ctx!.fillStyle = "rgba(0, 172, 193, 1)"; // cyan
      for (const p of particles) {
        ctx!.globalAlpha = p.opacity;
        ctx!.beginPath();
        ctx!.arc(p.x, p.y, PARTICLE_RADIUS, 0, Math.PI * 2);
        ctx!.fill();
      }

      // ── Draw connections ──────────────────────────────────────
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < CONNECTION_DIST) {
            const alpha = (1 - dist / CONNECTION_DIST) * MAX_OPACITY * 0.6;
            ctx!.globalAlpha = Math.max(alpha, FAR_OPACITY);
            ctx!.strokeStyle = "rgba(0, 172, 193, 1)";
            ctx!.lineWidth = 0.5;
            ctx!.beginPath();
            ctx!.moveTo(particles[i].x, particles[i].y);
            ctx!.lineTo(particles[j].x, particles[j].y);
            ctx!.stroke();
          }
        }
      }

      ctx!.globalAlpha = 1;
      animRef.current = requestAnimationFrame(draw);
    }

    animRef.current = requestAnimationFrame(draw);

    return () => {
      mountedRef.current = false;
      cancelAnimationFrame(animRef.current);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 z-base pointer-events-none motion-reduce:hidden"
      aria-hidden="true"
    />
  );
}
