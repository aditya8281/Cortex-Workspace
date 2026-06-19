"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { motion, useInView } from "framer-motion";
import { ArrowRight, Shield, Brain, Cpu, Lock } from "lucide-react";
import GlowOrb from "../src/shared/ui/GlowOrb";
import BrainBackground from "../src/shared/ui/BrainBackground";
import AuthRedirect from "../src/shared/ui/AuthRedirect";

const PARTICLE_COUNT = 40;

function ParticleDots() {
  const [particles] = useState(() =>
    Array.from({ length: PARTICLE_COUNT }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      delay: Math.random() * 5,
      duration: Math.random() * 8 + 6,
      opacity: Math.random() * 0.4 + 0.1,
      xDrift: Math.random() * 20 - 10,
    }))
  );

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map((p) => (
        <motion.div
          key={p.id}
          className="absolute rounded-full"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            background: `radial-gradient(circle, rgba(6,182,212,${p.opacity}) 0%, transparent 70%)`,
            boxShadow: `0 0 ${p.size * 3}px rgba(6,182,212,${p.opacity * 0.5})`,
          }}
          animate={{
            y: [0, -30, 0],
            x: [0, p.xDrift, 0],
            opacity: [p.opacity, p.opacity * 1.5, p.opacity],
          }}
          transition={{
            duration: p.duration,
            repeat: Infinity,
            ease: "easeInOut",
            delay: p.delay,
          }}
        />
      ))}
    </div>
  );
}

function TypewriterTagline() {
  const text = "Your AI workspace, locally run.";
  const [displayed, setDisplayed] = useState("");

  useEffect(() => {
    let i = 0;
    const timer = setInterval(() => {
      if (i < text.length) {
        setDisplayed(text.slice(0, i + 1));
        i++;
      } else {
        clearInterval(timer);
      }
    }, 60);
    return () => clearInterval(timer);
  }, []);

  return (
    <span className="text-gradient-accent">
      {displayed}
      {displayed.length < text.length && (
        <span className="inline-block w-[2px] h-[1em] bg-accent ml-0.5 animate-pulse align-middle" />
      )}
    </span>
  );
}

const FEATURES = [
  {
    icon: <Lock className="h-5 w-5" />,
    title: "Private by Default",
    desc: "All data stays on your machine. End-to-end encryption for your vault.",
  },
  {
    icon: <Brain className="h-5 w-5" />,
    title: "AI-Powered Memory",
    desc: "Persistent knowledge base that learns from your repos and documents.",
  },
  {
    icon: <Cpu className="h-5 w-5" />,
    title: "Multi-Model Routing",
    desc: "Seamlessly switch between local and cloud models based on your needs.",
  },
  {
    icon: <Shield className="h-5 w-5" />,
    title: "Lightning Fast",
    desc: "Local inference with zero latency. No cloud dependency, no API rate limits.",
  },
];

function FeatureCard({ feature, index }: { feature: typeof FEATURES[0]; index: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, delay: index * 0.1, type: "spring", damping: 25 }}
      whileHover={{
        rotateX: -4,
        rotateY: 4,
        scale: 1.02,
        transition: { duration: 0.3 },
      }}
      style={{ perspective: 1000 }}
      className="rounded-xl bg-bg-elevated border border-border-subtle shadow-card p-5 cursor-default transition-shadow duration-300 hover:border-border-accent hover:shadow-glow"
    >
      <div className="h-9 w-9 rounded-md bg-accent-faint border border-accent/10 flex items-center justify-center text-accent mb-3">
        {feature.icon}
      </div>
      <h3 className="text-sm font-medium text-text mb-1">{feature.title}</h3>
      <p className="text-xs text-text-muted leading-relaxed">{feature.desc}</p>
    </motion.div>
  );
}

export default function RootPage() {
  return (
    <div className="min-h-screen flex flex-col bg-bg">
      <BrainBackground intensity="high" />
      <AuthRedirect />

      <header className="glass-panel h-14 flex items-center justify-between px-6 shrink-0 sticky top-0 z-20">
        <Link href="/" className="flex items-center gap-2 group">
          <motion.div
            className="h-1.5 w-1.5 rounded-full bg-accent"
            animate={{
              boxShadow: [
                "0 0 8px rgba(6,182,212,0.4)",
                "0 0 16px rgba(6,182,212,0.6)",
                "0 0 8px rgba(6,182,212,0.4)",
              ],
            }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          />
          <span className="font-mono text-[11px] tracking-[0.2em] uppercase text-text-secondary group-hover:text-text transition-colors">
            Cortex
          </span>
        </Link>
        <Link
          href="/auth"
          className="h-8 px-4 rounded-lg text-xs font-medium text-text-secondary border border-border hover:bg-bg-hover hover:text-text hover:border-accent/20 transition-all"
        >
          Sign in
        </Link>
      </header>

      <main id="main-content" className="flex-1">
        {/* Hero Section */}
        <section className="relative flex flex-col items-center justify-center min-h-[85vh] px-6 overflow-hidden">
          <ParticleDots />

          <GlowOrb className="top-20 left-1/4 -translate-x-1/2" size={400} color="rgba(6,182,212,0.06)" />
          <GlowOrb className="bottom-20 right-1/4 translate-x-1/2" size={350} color="rgba(6,182,212,0.05)" delay={2} />

          <motion.div
            className="max-w-2xl text-center relative z-10"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8 }}
          >
            {/* Status badge */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-accent/20 bg-accent-faint mb-8"
            >
              <motion.span
                className="h-1.5 w-1.5 rounded-full bg-accent"
                animate={{
                  boxShadow: [
                    "0 0 4px rgba(6,182,212,0.4)",
                    "0 0 12px rgba(6,182,212,0.6)",
                    "0 0 4px rgba(6,182,212,0.4)",
                  ],
                }}
                transition={{ duration: 2, repeat: Infinity }}
              />
              <span className="text-[11px] font-medium text-accent tracking-wide uppercase">
                Local-first AI workspace
              </span>
            </motion.div>

            {/* Logo / Title */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4, type: "spring", damping: 20 }}
            >
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight leading-[1.1]">
                <span className="text-gradient">Your AI workspace,</span>
                <br />
                <TypewriterTagline />
              </h1>
            </motion.div>

            <motion.p
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 1.2 }}
              className="mt-6 text-base sm:text-lg text-text-secondary leading-relaxed max-w-lg mx-auto"
            >
              A private, local-first platform for orchestrating AI models,
              managing memory, and building intelligent workflows — all on your machine.
            </motion.p>

            {/* CTAs */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 1.6 }}
              className="mt-8 flex items-center justify-center gap-3"
            >
              <Link
                href="/auth"
                className="btn-glow h-12 px-7 rounded-xl bg-accent text-void text-sm font-semibold hover:bg-accent-hover active:scale-[0.97] transition-all shadow-glow hover:shadow-glow-strong inline-flex items-center gap-2.5"
              >
                Enter Cortex
                <ArrowRight className="h-4 w-4" />
              </Link>
              <a
                href="https://github.com"
                target="_blank"
                rel="noreferrer"
                className="h-12 px-6 rounded-xl border border-border text-sm text-text-secondary hover:bg-bg-hover hover:text-text hover:border-accent/20 transition-all inline-flex items-center gap-2"
              >
                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                GitHub
              </a>
            </motion.div>
          </motion.div>

          {/* Scroll indicator */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 2.5, duration: 0.5 }}
            className="absolute bottom-8 left-1/2 -translate-x-1/2"
          >
            <motion.div
              animate={{ y: [0, 8, 0] }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              className="w-5 h-8 rounded-full border border-border-subtle flex items-start justify-center p-1.5"
            >
              <motion.div
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="w-1 h-1.5 rounded-full bg-text-muted"
              />
            </motion.div>
          </motion.div>
        </section>

        {/* Features Section */}
        <section className="px-6 pb-24">
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-10">
              <h2 className="text-lg font-semibold text-text">Everything you need, locally</h2>
              <p className="text-sm text-text-muted mt-2">No cloud, no tracking, full control.</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {FEATURES.map((f, i) => (
                <FeatureCard key={i} feature={f} index={i} />
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="px-6 py-4 border-t border-border-subtle shrink-0">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <p className="text-xs text-text-muted font-mono tracking-wider uppercase">
            Local-first · Private by default
          </p>
          <p className="text-xs text-text-muted">&copy; 2026 Cortex</p>
        </div>
      </footer>
    </div>
  );
}
