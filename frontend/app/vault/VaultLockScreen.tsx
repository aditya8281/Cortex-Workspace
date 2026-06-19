/**
 * Lock screen — shown when vault is locked.
 */
"use client";

import type { VaultContext } from "./useVaultState";

interface Props {
  vault: VaultContext;
}

export default function VaultLockScreen({ vault }: Props) {
  const {
    loading, error, successMsg,
    vaultPassword, showPassword,
    setVaultPassword, setShowPassword,
    handleUnlock,
  } = vault;

  return (
    <div className="mx-auto flex max-w-[420px] flex-col items-center justify-center py-16 animate-fade-in">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-bg-card border border-border text-accent shadow-glow">
        <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      </div>
      <h1 className="text-xl font-bold text-text">Cortex Vault</h1>
      <p className="mb-8 text-xs tracking-widest uppercase text-text-muted mt-1">Private Secure Cabinet</p>
      <div className="glass-panel-strong w-full rounded-xl p-6">
        <div className="flex items-center justify-between mb-4 border-b border-border-subtle pb-3">
          <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Unlock Locker</span>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-error/10 px-2.5 py-0.5 text-[10px] font-medium text-error">
            <span className="status-dot bg-error shadow-[0_0_6px_rgba(239,68,68,0.4)]" /> Locked
          </span>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-[11px] font-semibold text-text-secondary uppercase tracking-wider mb-2">Vault Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={vaultPassword}
                onChange={(e) => setVaultPassword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleUnlock()}
                placeholder="Enter secret vault password"
                className="w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm text-text placeholder-text-muted focus:border-accent focus:outline-none transition-colors"
              />
              <button onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-2.5 text-text-muted hover:text-text transition-colors">
                {showPassword ? (
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                ) : (
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
          </div>
          <button
            disabled={loading || !vaultPassword.trim()}
            onClick={handleUnlock}
            className="w-full rounded-lg bg-accent hover:bg-accent-hover text-bg py-2 text-sm font-semibold transition-colors disabled:opacity-40 shadow-glow flex items-center justify-center gap-2"
          >
            {loading ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-bg border-t-transparent" /> : null}
            Unlock Cabinet
          </button>
        </div>
        {error && <p className="mt-4 rounded-lg bg-error/10 border border-error/20 p-2.5 text-xs text-error font-medium">{error}</p>}
        {successMsg && <p className="mt-4 rounded-lg bg-success/10 border border-success/20 p-2.5 text-xs text-success font-medium">{successMsg}</p>}
      </div>
      <p className="mt-6 text-center text-[10px] text-text-muted max-w-[280px]">
        Private files never leave your local workspace. All operations are local, private, and zero-knowledge.
      </p>
    </div>
  );
}
