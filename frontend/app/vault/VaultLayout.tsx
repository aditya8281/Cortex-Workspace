/**
 * Vault layout — alerts, nav bar, and 3-panel resizable shell.
 */
"use client";

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
      {error && (
        <div className="glass-panel flex items-center justify-between rounded-lg px-4 py-2.5 text-xs text-error font-medium">
          <span>{error}</span>
          <button onClick={() => setError("")} className="ml-3 p-0.5 rounded hover:bg-bg-hover text-error/70 hover:text-error transition-colors">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}
      {successMsg && (
        <div className="glass-panel flex items-center justify-between rounded-lg px-4 py-2.5 text-xs text-success font-medium">
          <span>{successMsg}</span>
          <button onClick={() => setSuccessMsg("")} className="ml-3 p-0.5 rounded hover:bg-bg-hover text-success/70 hover:text-success transition-colors">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Navigation Bar */}
      <div className="flex items-center gap-2 px-1">
        <div className="flex items-center gap-0.5">
          <button
            onClick={navigateBack}
            disabled={navIndex === 0}
            className="toolbar-btn p-1.5 rounded-lg hover:bg-bg-hover text-text-secondary hover:text-text disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            title="Back"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <button
            onClick={navigateForward}
            disabled={navIndex >= navHistory.length - 1}
            className="toolbar-btn p-1.5 rounded-lg hover:bg-bg-hover text-text-secondary hover:text-text disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            title="Forward"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
          <button
            onClick={navigateUp}
            disabled={currentFolder === "/"}
            className="toolbar-btn p-1.5 rounded-lg hover:bg-bg-hover text-text-secondary hover:text-text disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            title="Up one level"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
            </svg>
          </button>
          <button
            onClick={() => { refreshStatus(); setSuccessMsg("Refreshed."); }}
            className="toolbar-btn p-1.5 rounded-lg hover:bg-bg-hover text-text-secondary hover:text-text transition-colors"
            title="Refresh"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H17" />
            </svg>
          </button>
        </div>

        {/* Address Bar */}
        <div className="flex-1 flex items-center rounded-lg glass-panel overflow-hidden">
          {addressBarEditing ? (
            <input
              ref={addressInputRef}
              type="text"
              value={addressBarValue}
              onChange={(e) => setAddressBarValue(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleAddressBarSubmit(); if (e.key === "Escape") { setAddressBarEditing(false); } }}
              onBlur={handleAddressBarSubmit}
              autoFocus
              className="flex-1 px-3 py-1.5 text-xs font-mono text-text bg-transparent focus:outline-none"
            />
          ) : (
            <div
              className="flex-1 flex items-center gap-0.5 px-2 py-1.5 cursor-text overflow-x-auto"
              onClick={() => { setAddressBarEditing(true); setTimeout(() => addressInputRef.current?.focus(), 0); }}
            >
              {breadcrumbs.map((crumb: { name: string; path: string }, idx: number) => (
                <span key={idx} className="flex items-center gap-0.5 shrink-0">
                  {idx > 0 && <span className="text-text-muted mx-0.5">›</span>}
                  {crumb.path ? (
                    <button onClick={(e) => { e.stopPropagation(); navigateTo(crumb.path); }} className="text-xs text-text-secondary hover:text-accent hover:underline font-medium px-1 py-0.5 rounded hover:bg-bg-hover transition-colors">
                      {crumb.name}
                    </button>
                  ) : (
                    <span className="text-xs text-accent font-bold px-1">{crumb.name}</span>
                  )}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 3-Panel Layout */}
      <div ref={containerRef} className="grid gap-0 min-h-[65vh] items-stretch" style={{
        gridTemplateColumns: sidebarCollapsed
          ? `0px 1fr ${propertiesCollapsed ? "0px" : `${propertiesWidth}px`}`
          : `${sidebarWidth}px 0px 1fr 0px ${propertiesCollapsed ? "0px" : `${propertiesWidth}px`}`,
      }}>
        {!sidebarCollapsed && <VaultSidebar vault={vault} />}

        {!sidebarCollapsed && (
          <div className="w-1 cursor-col-resize bg-border hover:bg-accent hover:shadow-glow transition-all rounded-full" onMouseDown={() => { resizingRef.current = "left"; }} />
        )}

        <main className="flex flex-col border border-border bg-bg-surface overflow-hidden min-w-0 rounded-lg">
          <VaultToolbar vault={vault} />
          <VaultFileList vault={vault} />
        </main>

        {!propertiesCollapsed && (
          <div className="w-1 cursor-col-resize bg-border hover:bg-accent hover:shadow-glow transition-all rounded-full" onMouseDown={() => { resizingRef.current = "right"; }} />
        )}

        {!propertiesCollapsed && <VaultProperties vault={vault} />}
      </div>
    </>
  );
}
