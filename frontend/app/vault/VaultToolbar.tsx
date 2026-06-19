/**
 * Toolbar — upload, new folder, export, rekey, search, view toggle.
 */
"use client";

import type { VaultContext } from "./useVaultState";

interface Props {
  vault: VaultContext;
}

export default function VaultToolbar({ vault }: Props) {
  const {
    loading, fileInputRef, handleUpload,
    setModalNewFolder, setModalChangePw, setModalExport,
    activeCategory, selectedPaths,
    searchQuery, setSearchQuery,
    activeView, setActiveView,
  } = vault;

  return (
    <div className="flex flex-wrap gap-1.5 items-center justify-between border-b border-border p-2 bg-bg/50">
      <div className="flex flex-wrap items-center gap-1">
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
          className="toolbar-btn inline-flex items-center gap-1 rounded-lg bg-accent hover:bg-accent-hover text-bg px-2.5 py-1.5 text-xs font-semibold transition-colors disabled:opacity-40 disabled:pointer-events-none"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          <span>Upload</span>
        </button>
        <input type="file" multiple className="hidden" ref={fileInputRef} onChange={handleUpload} />

        <button
          onClick={() => setModalNewFolder(true)}
          disabled={loading || activeCategory !== "all"}
          className="toolbar-btn inline-flex items-center gap-1 rounded-lg border border-border bg-bg hover:bg-bg-hover text-text-secondary hover:text-text px-2.5 py-1.5 text-xs font-medium transition-colors disabled:opacity-40 disabled:pointer-events-none"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
          </svg>
          <span>New Folder</span>
        </button>

        <button
          onClick={() => setModalExport(Array.from(selectedPaths))}
          disabled={selectedPaths.size === 0}
          className="toolbar-btn inline-flex items-center gap-1 rounded-lg border border-border bg-bg hover:bg-bg-hover text-text-secondary hover:text-text px-2.5 py-1.5 text-xs font-medium transition-colors disabled:opacity-40 disabled:pointer-events-none"
        >
          <svg className="w-3.5 h-3.5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 4H6a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-2m-4-1v8m0 0l3-3m-3 3L9 8m-5 5h2.586a1 1 0 01.707.293l2.414 2.414a1 1 0 00.707.293h3.172a1 1 0 00.707-.293l2.414-2.414a1 1 0 01.707-.293H20" />
          </svg>
          <span>Export</span>
        </button>

        <button
          onClick={() => setModalChangePw(true)}
          className="toolbar-btn inline-flex items-center gap-1 rounded-lg border border-border bg-bg hover:bg-bg-hover text-text-secondary hover:text-text px-2.5 py-1.5 text-xs font-medium transition-colors"
        >
          <svg className="w-3.5 h-3.5 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m-2 4a2 2 0 012 2m-2-4a2 2 0 012-2m-2 4a2 2 0 012 2m-5-4H5a2 2 0 00-2 2v6a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1-5l-2 2-2-2" />
          </svg>
          <span>Rekey</span>
        </button>
      </div>

      <div className="flex items-center gap-1.5 ml-auto">
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search..."
            className="rounded-lg border border-border bg-bg/60 backdrop-blur-sm px-2.5 py-1.5 text-xs text-text placeholder-text-muted focus:border-accent focus:outline-none w-36 sm:w-44 transition-all"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery("")} className="absolute right-2 top-1.5 text-text-muted hover:text-text transition-colors">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        <div className="flex border border-border rounded-lg overflow-hidden bg-bg">
          {(["table", "list", "grid"] as const).map((view) => (
            <button
              key={view}
              onClick={() => setActiveView(view)}
              className={`toolbar-btn p-1.5 text-xs ${activeView === view ? "bg-bg-hover text-accent" : "bg-transparent text-text-secondary hover:bg-bg-hover hover:text-text"} transition-colors`}
            >
              {view === "table" && <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>}
              {view === "list" && <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>}
              {view === "grid" && <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
