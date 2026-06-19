"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { cn } from "../../lib/utils";

interface Stream {
  points: { x: number; y: number }[];
  speed: number;
  opacity: number;
  width: number;
  offset: number;
}

interface EnergyStreamsProps {
  className?: string;
  streamCount?: number;
}

export default function EnergyStreams({
  className,
  streamCount = 5,
}: EnergyStreamsProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamsRef = useRef<Stream[]>([]);
  const animationRef = useRef<number>(0);
  const timeRef = useRef(0);
  const [reducedMotion] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  });

  const initStreams = useCallback(
    (width: number, height: number) => {
      const streams: Stream[] = [];
      for (let i = 0; i < streamCount; i++) {
        const points: { x: number; y: number }[] = [];
        const segmentCount = 8 + Math.floor(Math.random() * 4);
        for (let j = 0; j < segmentCount; j++) {
          points.push({
            x: (width / (segmentCount - 1)) * j,
            y: height * 0.2 + Math.random() * height * 0.6,
          });
        }
        streams.push({
          points,
          speed: 0.2 + Math.random() * 0.3,
          opacity: 0.03 + Math.random() * 0.04,
          width: 1 + Math.random() * 1.5,
          offset: Math.random() * Math.PI * 2,
        });
      }
      streamsRef.current = streams;
    },
    [streamCount],
  );

  useEffect(() => {
    if (reducedMotion) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      if (streamsRef.current.length === 0) {
        initStreams(canvas.width, canvas.height);
      }
    };
    resize();
    window.addEventListener("resize", resize);

    const animate = () => {
      if (!canvas || !ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      timeRef.current += 0.016;

      for (const stream of streamsRef.current) {
        ctx.beginPath();
        const pts = stream.points;
        if (pts.length < 2) continue;

        const animatedPts = pts.map((p, i) => ({
          x: p.x,
          y:
            p.y +
            Math.sin(timeRef.current * stream.speed + stream.offset + i * 0.5) *
              30,
        }));

        ctx.moveTo(animatedPts[0].x, animatedPts[0].y);
        for (let i = 1; i < animatedPts.length - 1; i++) {
          const xc = (animatedPts[i].x + animatedPts[i + 1].x) / 2;
          const yc = (animatedPts[i].y + animatedPts[i + 1].y) / 2;
          ctx.quadraticCurveTo(
            animatedPts[i].x,
            animatedPts[i].y,
            xc,
            yc,
          );
        }
        const last = animatedPts[animatedPts.length - 1];
        ctx.lineTo(last.x, last.y);

        ctx.strokeStyle = `rgba(6, 182, 212, ${stream.opacity})`;
        ctx.lineWidth = stream.width;
        ctx.stroke();
      }

      animationRef.current = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(animationRef.current);
    };
  }, [reducedMotion, initStreams]);

  if (reducedMotion) return null;

  return (
    <canvas
      ref={canvasRef}
      className={cn("pointer-events-none fixed inset-0 z-[-1]", className)}
    />
  );
}
