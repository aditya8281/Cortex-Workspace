"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { Mail, Lock, ShieldAlert, Cpu, Terminal, ArrowRight } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      await login({ email, password });
      router.push("/dashboard");
    } catch (err) {
      const errorMsg = err instanceof Error 
        ? err.message 
        : typeof err === 'object' && err !== null && 'response' in err 
          ? (err as any).response?.data?.detail || (err as any).response?.data?.message 
          : 'Login failed';
      setError(errorMsg || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030712] relative overflow-hidden flex items-center justify-center font-sans">
      {/* Background Decorative Tech Elements */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#0f172a_1px,transparent_1px),linear-gradient(to_bottom,#0f172a_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-30" />
      
      {/* Ambient Neon Blobs */}
      <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-purple-500/10 rounded-full blur-[100px] pointer-events-none animate-pulse" style={{ animationDuration: '6s' }} />

      <div className="relative w-full max-w-md px-4 py-8 z-10">
        {/* Top Branding / Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-slate-900 border border-cyan-500/30 rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(6,182,212,0.15)] mb-3">
            <Cpu className="w-6 h-6 text-cyan-400" />
          </div>
          <h1 className="text-3xl font-bold tracking-wider bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
            CORTEX<span className="text-cyan-400">.</span>
          </h1>
          <p className="text-xs text-cyan-500/80 font-mono tracking-widest mt-1.5 uppercase">
            AI Cognitive Workspace
          </p>
        </div>

        {/* Auth Glassmorphic Card */}
        <div className="bg-slate-950/65 backdrop-blur-md border border-slate-800/80 rounded-2xl p-8 shadow-[0_0_40px_rgba(0,0,0,0.5),_0_0_20px_rgba(6,182,212,0.05)]">
          {/* Tech Headers */}
          <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 border-b border-slate-900 pb-4 mb-6">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-ping" />
              <span className="text-slate-300">SYS_AUTH: SECURE</span>
            </div>
            <div>PROTO v1.4.2</div>
          </div>

          <h2 className="text-xl font-semibold text-white mb-2">Welcome Back</h2>
          <p className="text-sm text-slate-400 mb-6">Authenticate to access the cognitive node.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email Field */}
            <div className="space-y-1.5">
              <label className="text-xs font-mono text-slate-400 uppercase tracking-wider block">
                Security ID (Email)
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <Mail className="w-4 h-4 text-slate-500" />
                </span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@cortex.ai"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-900/60 border border-slate-800/80 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500/80 focus:ring-1 focus:ring-cyan-500/30 transition-all font-sans text-sm shadow-inner"
                  required
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-1.5">
              <label className="text-xs font-mono text-slate-400 uppercase tracking-wider block">
                Access Code (Password)
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <Lock className="w-4 h-4 text-slate-500" />
                </span>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-900/60 border border-slate-800/80 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500/80 focus:ring-1 focus:ring-cyan-500/30 transition-all font-sans text-sm shadow-inner"
                  required
                />
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="flex items-start gap-2.5 bg-red-950/20 border border-red-900/30 rounded-xl p-3 text-red-400 text-xs font-sans">
                <ShieldAlert className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{error}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full mt-4 flex items-center justify-center gap-2 py-3 px-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:from-slate-800 disabled:to-slate-800 text-white font-medium rounded-xl text-sm transition-all focus:outline-none focus:ring-2 focus:ring-cyan-500/50 shadow-[0_4px_12px_rgba(6,182,212,0.15)] disabled:shadow-none hover:translate-y-[-1px] active:translate-y-[1px]"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Initializing Session...
                </>
              ) : (
                <>
                  Establish Connection
                  <ArrowRight className="w-4 h-4 text-white/90" />
                </>
              )}
            </button>
          </form>

          {/* Technical Info Subtext */}
          <div className="mt-8 flex items-center justify-between text-[10px] font-mono text-slate-500 border-t border-slate-900/60 pt-4">
            <div className="flex items-center gap-1">
              <Terminal className="w-3 h-3 text-slate-600" />
              <span>TERMINAL STATUS: READY</span>
            </div>
            <button 
              onClick={() => router.push("/register")}
              className="text-cyan-400 hover:text-cyan-300 transition-colors uppercase hover:underline"
            >
              Register Node
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
