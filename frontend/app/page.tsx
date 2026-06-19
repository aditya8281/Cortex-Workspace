import Link from "next/link";
import AuthRedirect from "../src/shared/ui/AuthRedirect";
import type { ReactNode } from "react";

interface Feature {
  icon: ReactNode;
  title: string;
  desc: string;
}

const FEATURES: Feature[] = [
  {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    title: "Lightning Fast",
    desc: "Local inference with zero latency. No cloud dependency, no API rate limits.",
  },
  {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
      </svg>
    ),
    title: "Private by Default",
    desc: "All data stays on your machine. End-to-end encryption for your vault.",
  },
  {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5" />
      </svg>
    ),
    title: "AI-Powered Memory",
    desc: "Persistent knowledge base that learns from your repos and documents.",
  },
  {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m9.86-2.556a4.5 4.5 0 00-6.364-6.364L4.5 8.25a4.5 4.5 0 006.364 6.364l4.5-4.5z" />
      </svg>
    ),
    title: "Multi-Model Routing",
    desc: "Seamlessly switch between local and cloud models based on your needs.",
  },
];

export default function RootPage() {
  return (
    <div className="min-h-screen flex flex-col bg-bg">
      <AuthRedirect />
      <header className="glass-panel h-14 flex items-center justify-between px-6 shrink-0 sticky top-0 z-20">
        <Link href="/" className="flex items-center gap-2 group">
          <div className="h-1.5 w-1.5 rounded-full bg-accent shadow-[0_0_8px_rgba(6,182,212,0.4)] group-hover:shadow-[0_0_12px_rgba(6,182,212,0.6)] transition-shadow" />
          <span className="font-mono text-[11px] tracking-[0.2em] uppercase text-text-secondary group-hover:text-text transition-colors">Cortex</span>
        </Link>
        <Link href="/auth" className="h-8 px-4 rounded-lg text-xs font-medium text-text-secondary border border-border hover:bg-bg-hover hover:text-text hover:border-accent/20 transition-all">Sign in</Link>
      </header>
      <main className="flex-1">
        <section className="flex flex-col items-center justify-center px-6 pt-24 pb-20 animate-fade-in">
          <div className="max-w-2xl text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-accent/20 bg-accent-faint mb-6">
              <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse-glow" />
              <span className="text-[11px] font-medium text-accent tracking-wide uppercase">Local-first AI workspace</span>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight leading-[1.1]">
              <span className="text-gradient">Your AI workspace,</span><br />
              <span className="text-gradient-accent">locally run.</span>
            </h1>
            <p className="mt-6 text-base sm:text-lg text-text-secondary leading-relaxed max-w-lg mx-auto">Cortex is a private, local-first platform for orchestrating AI models, managing memory, and building intelligent workflows — all on your machine.</p>
            <div className="mt-8 flex items-center justify-center gap-3">
              <Link href="/auth" className="h-11 px-6 rounded-lg bg-accent text-white text-sm font-medium hover:bg-accent-hover active:scale-[0.97] transition-all shadow-glow hover:shadow-glow-strong inline-flex items-center gap-2">
                Get started
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" /></svg>
              </Link>
              <a href="https://github.com" target="_blank" rel="noreferrer" className="h-11 px-6 rounded-lg border border-border text-sm text-text-secondary hover:bg-bg-hover hover:text-text hover:border-accent/20 transition-all inline-flex items-center gap-2">
                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                GitHub
              </a>
            </div>
          </div>
        </section>
        <section className="px-6 pb-20">
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-10">
              <h2 className="text-lg font-semibold text-text">Everything you need, locally</h2>
              <p className="text-sm text-text-muted mt-2">No cloud, no tracking, full control.</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {FEATURES.map((f, i) => (
                <div key={i} className="interactive-card p-5" style={{ animationDelay: `${i * 80}ms` }}>
                  <div className="h-9 w-9 rounded-md bg-accent-faint border border-accent/10 flex items-center justify-center text-accent mb-3">{f.icon}</div>
                  <h3 className="text-sm font-medium text-text mb-1">{f.title}</h3>
                  <p className="text-xs text-text-muted leading-relaxed">{f.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
      <footer className="px-6 py-4 border-t border-border shrink-0">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <p className="text-xs text-text-muted font-mono tracking-wider uppercase">Local-first · Private by default</p>
          <p className="text-xs text-text-muted">&copy; 2026 Cortex</p>
        </div>
      </footer>
    </div>
  );
}
