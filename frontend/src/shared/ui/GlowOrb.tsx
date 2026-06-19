"use client";

import { motion } from "framer-motion";
import { cn } from "../../lib/utils";

interface GlowOrbProps {
  className?: string;
  size?: number;
  color?: string;
  delay?: number;
}

export default function GlowOrb({ className, size = 300, color = "rgba(6,182,212,0.08)", delay = 0 }: GlowOrbProps) {
  return (
    <motion.div
      className={cn("absolute rounded-full pointer-events-none", className)}
      style={{
        width: size,
        height: size,
        background: `radial-gradient(circle, ${color} 0%, transparent 70%)`,
        filter: "blur(40px)",
      }}
      animate={{
        y: [0, -20, 0],
        x: [0, 10, 0],
        scale: [1, 1.1, 1],
      }}
      transition={{
        duration: 8,
        repeat: Infinity,
        ease: "easeInOut",
        delay,
      }}
    />
  );
}
