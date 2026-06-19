/**
 * Vault layout — alerts, nav bar, and 3-panel resizable shell.
 * Updated 3-panel layout with new styling.
 */
"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft, ChevronRight, ChevronUp, RefreshCw, X, AlertTriangle, CheckCircle,
} from "lucide-react";
import type { VaultContext } from "./useVaultState";
import VaultSidebar from "./VaultSidebar";
import VaultToolbar from "./VaultToolbar";
import VaultFileList from "./VaultFileList";
import VaultProperties from "./VaultProperties";

interface Props {
  vault: VaultContext;
}

export default function VaultLayout({ vault }: Props) {
  const {
    error, successMsg, setError, setSuccessMsg,
    navigateBack, navigateForward, navigateUp, navIndex, navHistory,
    currentFolder, refreshStatus, navigateTo,
    sidebarCollapsed, propertiesCollapsed, sidebarWidth, propertiesWidth,
    containerRef, resizingRef,
    addressBarEditing, addressBarValue, setAddressBarEditing,
    setAddressBarValue, handleAddressBarSubmit, addressInputRef,
    breadcrumbs,
  } = vault;

  return (
    <>
      {/* Alerts */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="glass-panel flex items-center justify-between rounded-xl px-4 py-3 text-xs text-error font-medium"
          >
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError("")} className="ml-3 p-1 rounded-lg hover:bg-error-muted text-error/70 hover:text-error transition-colors">
              <X className="w-3.5 h-3.5" />
            </button>
          </motion.div>
        )}
        {successMsg && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="glass-panel flex items-center justify-between rounded-xl px-4 py-3 text-xs text-success font-medium"
          >
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 shrink-0" />
              <span>{successMsg}</span>
            </div>
            <button onClick={() => setSuccessMsg("")} className="ml-3 p-1 rounded-lg hover:bg-success-muted text-success/70 hover:text-success transition-colors">
              <X className="w-3.5 h-3.5" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Navigation Bar */}
      <div className="flex items-center gap-2 px-1">
        <div className="flex items-center gap-0.5">
          <NavButton onClick={navigateBack} disabled={navIndex === 0} title="Back">
            <ChevronLeft className="w-4 h-4" />
          </NavButton>
          <NavButton onClick={navigateForward} disabled={navIndex >= navHistory.length - 1} title="Forward">
            <ChevronRight className="w-4 h-4" />
          </NavButton>
          <NavButton onClick={navigateUp} disabled={currentFolder === "/"} title="Up one level">
            <ChevronUp className="w-4 h-4" />
          </NavButton>
          <NavButton onClick={() => { refreshStatus(); setSuccessMsg("Refreshed."); }} title="Refresh">
            <RefreshCw className="w-4 h-4" />
          </NavButton>
        </div>

        {/* Address Bar */}
        <div className="flex-1 flex items-center rounded-xl glass-panel overflow-hidden">
          {addressBarEditing ? (
            <input
              ref={addressInputRef}
              type="text"
              value={addressBarValue}
              onChange={(e) => setAddressBarValue(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleAddressBarSubmit(); if (e.key === "Escape") { setAddressBarEditing(false); } }}
              onBlur={handleAddressBarSubmit}
              autoFocus
              className="flex-1 px-4 py-2 text-xs font-mono text-text bg-transparent focus:outline-none"
            />
          ) : (
            <div
              className="flex-1 flex items-center gap-0.5 px-3 py-2 cursor-text overflow-x-auto"
              onClick={() => { setAddressBarEditing(true); setTimeout(() => addressInputRef.current?.focus(), 0); }}
            >
              {breadcrumbs.map((crumb: { name: string; path: string }, idx: number) => (
                <span key={idx} className="flex items-center gap-0.5 shrink-0">
                  {idx > 0 && <span className="text-text-muted mx-1 font-mono">/</span>}
                  {crumb.path ? (
                    <button onClick={(e) => { e.stopPropagation(); navigateTo(crumb.path); }} className="text-xs text-text-secondary hover:text-accent hover:underline font-medium px-1.5 py-0.5 rounded-lg hover:bg-bg-hover transition-colors">
                      {crumb.name}
                    </button>
                  ) : (
                    <span className="text-xs text-accent font-bold px-1.5">{crumb.name}</span>
                  )}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 3-Panel Layout */}
      <div ref={containerRef} className="grid gap-2 min-h-[65vh] items-stretch" style={{
        gridTemplateColumns: sidebarCollapsed
          ? `0px 1fr ${propertiesCollapsed ? "0px" : `${propertiesWidth}px`}`
          : `${sidebarWidth}px 0px 1fr 0px ${propertiesCollapsed ? "0px" : `${propertiesWidth}px`}`,
      }}>
        {!sidebarCollapsed && <VaultSidebar vault={vault} />}

        {!sidebarCollapsed && (
          <div className="w-1 cursor-col-resize bg-border-subtle hover:bg-accent hover:shadow-glow transition-all rounded-full" onMouseDown={() => { resizingRef.current = "left"; }} />
        )}

        <main className="flex flex-col glass-panel overflow-hidden min-w-0 rounded-xl">
          <VaultToolbar vault={vault} />
          <VaultFileList vault={vault} />
        </main>

        {!propertiesCollapsed && (
          <div className="w-1 cursor-col-resize bg-border-subtle hover:bg-accent hover:shadow-glow transition-all rounded-full" onMouseDown={() => { resizingRef.current = "right"; }} />
        )}

        {!propertiesCollapsed && <VaultProperties vault={vault} />}
      </div>
    </>
  );
}

// ── Nav Button ──

function NavButton({ onClick, disabled, title, children }: { onClick: () => void; disabled?: boolean; title: string; children: React.ReactNode }) {
  return (
    <motion.button
      onClick={onClick}
      disabled={disabled}
      whileTap={disabled ? undefined : { scale: 0.9 }}
      title={title}
      className="toolbar-btn p-1.5 rounded-xl hover:bg-bg-hover text-text-secondary hover:text-text disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
    >
      {children}
    </motion.button>
  );
}
