/**
 * Properties panel — right panel showing metadata and tags for selected file.
 * Glass panel with metadata display.
 */
"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  Folder, File, Star, Tag, Download, Trash2, Info, Layers,
} from "lucide-react";
import type { VaultContext } from "./useVaultState";
import { formatSize, formatDate, getFileCategory } from "./useVaultState";

interface Props {
  vault: VaultContext;
}

export default function VaultProperties({ vault }: Props) {
  const {
    selectedSingleItem, selectedItems,
    handleToggleFavorite, handleAddTag, handleRemoveTag,
    handleDownloadFile, setModalExport, setModalDelete, selectedPaths,
  } = vault;

  return (
    <aside className="glass-panel rounded-2xl p-3 flex flex-col gap-3 text-xs overflow-y-auto h-full">
      <div className="glass-panel-strong rounded-xl px-3 py-2.5">
        <h2 className="text-xs font-bold text-text font-display">Properties</h2>
      </div>

      <AnimatePresence mode="wait">
        {selectedSingleItem ? (
          <motion.div
            key="single"
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -12 }}
            transition={{ duration: 0.15 }}
            className="space-y-3 flex-1 flex flex-col"
          >
            {/* File icon + name */}
            <div className="flex flex-col items-center gap-2.5 bg-bg/40 rounded-xl p-4 border border-border-subtle">
              <div className="relative">
                <div className="absolute inset-0 rounded-full bg-accent/5 blur-lg" />
                <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-bg-surface border border-border-subtle">
                  {selectedSingleItem.is_dir ? (
                    <Folder className="w-7 h-7 text-accent" strokeWidth={1.5} />
                  ) : (
                    <File className="w-7 h-7 text-text-muted" strokeWidth={1.5} />
                  )}
                </div>
              </div>
              <p className="font-bold text-text text-center break-all text-xs leading-relaxed">{selectedSingleItem.name}</p>
              <p className="text-[10px] text-text-muted font-mono">{selectedSingleItem.is_dir ? "Directory" : getFileCategory(selectedSingleItem.name)}</p>
            </div>

            {/* Metadata */}
            <div className="space-y-2.5">
              <MetaRow label="Path">
                <span className="text-text-secondary break-all font-mono text-[11px]">{selectedSingleItem.path}</span>
              </MetaRow>
              {!selectedSingleItem.is_dir && (
                <MetaRow label="Size">
                  <span className="text-text-secondary font-mono">{formatSize(selectedSingleItem.size)}</span>
                </MetaRow>
              )}
              <MetaRow label="Created">
                <span className="text-text-secondary font-mono">{formatDate(selectedSingleItem.created)}</span>
              </MetaRow>
              <MetaRow label="Modified">
                <span className="text-text-secondary font-mono">{formatDate(selectedSingleItem.modified)}</span>
              </MetaRow>
              <div className="pt-2 border-t border-border-subtle flex items-center justify-between">
                <span className="text-[9px] text-text-muted font-bold uppercase tracking-wider">Favorite</span>
                <motion.button
                  onClick={() => handleToggleFavorite(selectedSingleItem)}
                  whileTap={{ scale: 0.95 }}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border transition-all duration-200 text-[11px] font-medium ${
                    selectedSingleItem.favorite
                      ? "bg-accent-muted border-accent/30 text-accent"
                      : "border-border-subtle bg-bg-surface hover:bg-bg-hover hover:border-border text-text-secondary"
                  }`}
                >
                  <Star className="w-3 h-3" fill={selectedSingleItem.favorite ? "currentColor" : "none"} />
                  <span>{selectedSingleItem.favorite ? "Starred" : "Star"}</span>
                </motion.button>
              </div>
            </div>

            {/* Tags */}
            <div className="space-y-2 border-t border-border-subtle pt-2.5">
              <span className="text-[9px] text-text-muted font-bold uppercase tracking-wider flex items-center gap-1.5">
                <Tag className="w-3 h-3" />
                Tags
              </span>
              <div className="flex flex-wrap gap-1">
                {selectedSingleItem.tags?.map((tag) => (
                  <motion.span
                    key={tag}
                    layout
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="inline-flex items-center gap-1 rounded-lg bg-accent-faint border border-accent/20 px-2 py-0.5 text-[10px] text-accent font-medium"
                  >
                    <span>{tag}</span>
                    <button onClick={() => handleRemoveTag(selectedSingleItem, tag)} className="text-accent/60 hover:text-error transition-colors ml-0.5">
                      <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </motion.span>
                ))}
                {(!selectedSingleItem.tags || selectedSingleItem.tags.length === 0) && (
                  <span className="text-[10px] text-text-muted italic">No tags</span>
                )}
              </div>
              <input
                type="text"
                placeholder="Add tag + Enter..."
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    const target = e.target as HTMLInputElement;
                    handleAddTag(selectedSingleItem, target.value);
                    target.value = "";
                  }
                }}
                className="w-full rounded-xl border border-border-subtle bg-bg-surface px-3 py-2 text-[11px] text-text placeholder-text-muted focus:border-accent focus:ring-2 focus:ring-accent/10 outline-none transition-all duration-200"
              />
            </div>

            {!selectedSingleItem.is_dir && (
              <div className="mt-auto pt-3 border-t border-border-subtle">
                <motion.button
                  onClick={() => handleDownloadFile(selectedSingleItem)}
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full py-2.5 rounded-xl bg-accent hover:bg-accent-hover text-bg font-bold flex items-center justify-center gap-2 text-[11px] transition-all duration-200 shadow-glow btn-glow"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download decrypted
                </motion.button>
              </div>
            )}
          </motion.div>
        ) : selectedItems.length > 1 ? (
          <motion.div
            key="multi"
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -12 }}
            transition={{ duration: 0.15 }}
            className="space-y-3"
          >
            <div className="flex flex-col items-center gap-2.5 bg-bg/40 rounded-xl p-4 border border-border-subtle">
              <div className="relative">
                <div className="absolute inset-0 rounded-full bg-accent/5 blur-lg" />
                <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-bg-surface border border-border-subtle">
                  <Layers className="w-7 h-7 text-accent" strokeWidth={1.5} />
                </div>
              </div>
              <p className="font-bold text-text text-center">{selectedItems.length} items selected</p>
            </div>
            <div className="space-y-2.5">
              <MetaRow label="Combined Size">
                <span className="text-text-secondary font-mono">{formatSize(selectedItems.reduce((acc, v) => acc + v.size, 0))}</span>
              </MetaRow>
              <motion.button
                onClick={() => setModalExport(Array.from(selectedPaths))}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
                className="w-full py-2.5 rounded-xl bg-accent hover:bg-accent-hover text-bg font-bold flex items-center justify-center gap-2 text-[11px] transition-all duration-200"
              >
                Export selected ({selectedItems.length})
              </motion.button>
              <motion.button
                onClick={() => setModalDelete(Array.from(selectedPaths))}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
                className="w-full py-2.5 rounded-xl bg-error-muted hover:bg-error/20 border border-error/20 text-error font-bold flex items-center justify-center gap-2 text-[11px] transition-all duration-200"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Delete selected ({selectedItems.length})
              </motion.button>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center h-48 border border-dashed border-border-subtle rounded-xl bg-bg/20 text-text-muted"
          >
            <Info className="w-8 h-8 mb-2 text-text-muted" strokeWidth={1.5} />
            <p className="text-center px-4 text-[11px]">Select an item to inspect properties</p>
          </motion.div>
        )}
      </AnimatePresence>
    </aside>
  );
}

function MetaRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <span className="block text-[9px] text-text-muted font-bold uppercase tracking-wider mb-1">{label}</span>
      {children}
    </div>
  );
}
