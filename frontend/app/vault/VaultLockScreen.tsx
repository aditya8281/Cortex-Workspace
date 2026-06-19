/**
 * Lock screen — shown when vault is locked.
 * Cinematic vault-door animation with matrix-style background.
 */
"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Lock, Eye, EyeOff, Shield, ShieldCheck, AlertTriangle, CheckCircle } from "lucide-react";
import type { VaultContext } from "./useVaultState";

interface Props {
  vault: VaultContext;
}

function MatrixRain() {
  const columns = useState<{ x: number; chars: string[]; delay: number; speed: number }[]>(() => {
    const chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノ";
    return Array.from({ length: 20 }, (_, i) => ({
      x: (i / 20) * 100,
      chars: Array.from({ length: 15 }, () => chars[Math.floor(Math.random() * chars.length)]),
      delay: Math.random() * 3,
      speed: 2 + Math.random() * 4,
    }));
  })[0];

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-20">
      {columns.map((col, i) => (
        <motion.div
          key={i}
          className="absolute font-mono text-[10px] text-accent/40 leading-tight"
          style={{ left: `${col.x}%` }}
          initial={{ y: -200 }}
          animate={{ y: "120vh" }}
          transition={{
            duration: col.speed,
            repeat: Infinity,
            delay: col.delay,
            ease: "linear",
          }}
        >
          {col.chars.map((char, j) => (
            <div key={j} style={{ opacity: 1 - j * 0.06 }}>{char}</div>
          ))}
        </motion.div>
      ))}
    </div>
  );
}

export default function VaultLockScreen({ vault }: Props) {
  const {
    loading, error, successMsg,
    vaultPassword, showPassword,
    setVaultPassword, setShowPassword,
    handleUnlock,
  } = vault;

  return (
    <div className="relative mx-auto flex max-w-[440px] flex-col items-center justify-center py-16 min-h-[75vh]">
      <MatrixRain />

      {/* Vault door icon with breathing glow */}
      <motion.div
        className="relative mb-8"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: "spring", damping: 20, stiffness: 200 }}
      >
        <div className="absolute inset-0 rounded-2xl bg-accent/10 blur-xl animate-pulse" />
        <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl bg-bg-surface border border-border-subtle shadow-glow">
          <motion.div
            animate={{ rotate: [0, 0, -5, 5, 0] }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          >
            <Shield className="h-10 w-10 text-accent" strokeWidth={1.5} />
          </motion.div>
        </div>
      </motion.div>

      {/* Title */}
      <motion.div
        className="text-center mb-8"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <h1 className="text-2xl font-bold text-text font-display tracking-tight">Cortex Vault</h1>
        <p className="text-xs tracking-[0.25em] uppercase text-text-muted mt-2 font-mono">Private Secure Cabinet</p>
      </motion.div>

      {/* Unlock card */}
      <motion.div
        className="glass-panel-strong w-full rounded-2xl p-6 shadow-modal"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, type: "spring", damping: 25, stiffness: 200 }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-5 pb-4 border-b border-border-subtle">
          <span className="text-[10px] font-mono font-bold text-text-muted uppercase tracking-[0.15em]">Unlock Locker</span>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-error-muted px-2.5 py-1 text-[10px] font-mono font-medium text-error">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-error opacity-75" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-error" />
            </span>
            Locked
          </span>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-[10px] font-mono font-bold text-text-muted uppercase tracking-[0.15em] mb-2">
              Vault Password
            </label>
            <div className="relative group">
              <input
                type={showPassword ? "text" : "password"}
                value={vaultPassword}
                onChange={(e) => setVaultPassword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleUnlock()}
                placeholder="Enter secret vault password"
                className="w-full rounded-xl border border-border-subtle bg-bg px-4 py-3 pr-10 text-sm text-text placeholder-text-muted focus:border-accent focus:ring-2 focus:ring-accent/10 focus:shadow-glow outline-none transition-all duration-200"
              />
              <button
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text transition-colors p-1"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <motion.button
            disabled={loading || !vaultPassword.trim()}
            onClick={handleUnlock}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
            className="w-full rounded-xl bg-accent hover:bg-accent-hover text-bg py-3 text-sm font-bold transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed shadow-glow hover:shadow-glow-strong flex items-center justify-center gap-2 btn-glow"
          >
            {loading ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-bg border-t-transparent" />
            ) : (
              <Lock className="h-4 w-4" />
            )}
            Unlock Cabinet
          </motion.button>
        </div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 flex items-center gap-2 rounded-xl bg-error-muted border border-error/20 p-3 text-xs text-error font-medium"
          >
            <AlertTriangle className="h-4 w-4 shrink-0" />
            {error}
          </motion.div>
        )}
        {successMsg && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 flex items-center gap-2 rounded-xl bg-success-muted border border-success/20 p-3 text-xs text-success font-medium"
          >
            <CheckCircle className="h-4 w-4 shrink-0" />
            {successMsg}
          </motion.div>
        )}
      </motion.div>

      <motion.p
        className="mt-8 text-center text-[10px] text-text-muted max-w-[300px] leading-relaxed"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
      >
        Private files never leave your local workspace. All operations are local, private, and zero-knowledge.
      </motion.p>
    </div>
  );
}
