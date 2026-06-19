/**
 * Toolbar — upload, new folder, export, rekey, search, view toggle.
 * Icon buttons with search and view toggle.
 */
"use client";

import { motion } from "framer-motion";
import {
  Upload, FolderPlus, Download, KeyRound, Search, X,
  LayoutGrid, List, Table, SlidersHorizontal,
} from "lucide-react";
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
    <div className="flex flex-wrap gap-2 items-center justify-between border-b border-border-subtle px-3 py-2.5 bg-bg-elevated/50">
      <div className="flex flex-wrap items-center gap-1.5">
        <motion.button
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          className="toolbar-btn inline-flex items-center gap-1.5 rounded-xl bg-accent hover:bg-accent-hover text-bg px-3 py-2 text-xs font-bold transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed shadow-glow"
        >
          <Upload className="w-3.5 h-3.5" />
          <span>Upload</span>
        </motion.button>
        <input type="file" multiple className="hidden" ref={fileInputRef} onChange={handleUpload} />

        <motion.button
          onClick={() => setModalNewFolder(true)}
          disabled={loading || activeCategory !== "all"}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          className="toolbar-btn inline-flex items-center gap-1.5 rounded-xl border border-border-subtle bg-bg-surface hover:border-border-accent hover:bg-bg-hover text-text-secondary hover:text-text px-3 py-2 text-xs font-medium transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <FolderPlus className="w-3.5 h-3.5" />
          <span>New Folder</span>
        </motion.button>

        <motion.button
          onClick={() => setModalExport(Array.from(selectedPaths))}
          disabled={selectedPaths.size === 0}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          className="toolbar-btn inline-flex items-center gap-1.5 rounded-xl border border-border-subtle bg-bg-surface hover:border-border-accent hover:bg-bg-hover text-text-secondary hover:text-text px-3 py-2 text-xs font-medium transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Download className="w-3.5 h-3.5 text-accent" />
          <span>Export</span>
        </motion.button>

        <motion.button
          onClick={() => setModalChangePw(true)}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          className="toolbar-btn inline-flex items-center gap-1.5 rounded-xl border border-border-subtle bg-bg-surface hover:border-border-accent hover:bg-bg-hover text-text-secondary hover:text-text px-3 py-2 text-xs font-medium transition-all duration-200"
        >
          <KeyRound className="w-3.5 h-3.5" />
          <span>Rekey</span>
        </motion.button>
      </div>

      <div className="flex items-center gap-2 ml-auto">
        {/* Search */}
        <div className="relative group">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted group-focus-within:text-accent transition-colors" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search files..."
            className="rounded-xl border border-border-subtle bg-bg-surface pl-8 pr-8 py-2 text-xs text-text placeholder-text-muted focus:border-accent focus:ring-2 focus:ring-accent/10 focus:shadow-glow outline-none w-36 sm:w-48 transition-all duration-200"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery("")} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text transition-colors">
              <X className="w-3 h-3" />
            </button>
          )}
        </div>

        {/* View Toggle */}
        <div className="flex border border-border-subtle rounded-xl overflow-hidden bg-bg-surface p-0.5">
          {([
            { view: "table" as const, icon: Table },
            { view: "list" as const, icon: List },
            { view: "grid" as const, icon: LayoutGrid },
          ]).map(({ view, icon: Icon }) => (
            <motion.button
              key={view}
              onClick={() => setActiveView(view)}
              whileTap={{ scale: 0.95 }}
              className={`toolbar-btn p-1.5 rounded-lg transition-all duration-200 ${
                activeView === view
                  ? "bg-accent/10 text-accent"
                  : "text-text-muted hover:bg-bg-hover hover:text-text"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
            </motion.button>
          ))}
        </div>
      </div>
    </div>
  );
}
