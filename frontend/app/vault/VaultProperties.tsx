/**
 * Properties panel — right panel showing metadata and tags for selected file.
 */
"use client";

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
    <aside className="border border-border bg-bg-surface rounded-r-xl p-3 flex flex-col gap-3 text-xs overflow-y-auto">
      <div className="glass-panel-strong rounded-lg px-3 py-2">
        <h2 className="text-xs font-bold text-text">Properties</h2>
      </div>

      {selectedSingleItem ? (
        <div className="space-y-3 flex-1 flex flex-col">
          <div className="flex flex-col items-center gap-2 bg-bg/40 rounded-lg p-3 border border-border-subtle">
            {selectedSingleItem.is_dir ? (
              <svg className="w-10 h-10 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            ) : (
              <svg className="w-10 h-10 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            )}
            <p className="font-bold text-text text-center break-all text-xs">{selectedSingleItem.name}</p>
            <p className="text-[10px] text-text-muted">{selectedSingleItem.is_dir ? "Directory" : getFileCategory(selectedSingleItem.name)}</p>
          </div>

          <div className="space-y-2">
            <div>
              <span className="block text-[9px] text-text-muted font-bold uppercase tracking-wider mb-0.5">Path</span>
              <span className="text-text-secondary break-all font-mono text-[11px]">{selectedSingleItem.path}</span>
            </div>
            {!selectedSingleItem.is_dir && (
              <div>
                <span className="block text-[9px] text-text-muted font-bold uppercase tracking-wider mb-0.5">Size</span>
                <span className="text-text-secondary">{formatSize(selectedSingleItem.size)}</span>
              </div>
            )}
            <div>
              <span className="block text-[9px] text-text-muted font-bold uppercase tracking-wider mb-0.5">Created</span>
              <span className="text-text-secondary">{formatDate(selectedSingleItem.created)}</span>
            </div>
            <div>
              <span className="block text-[9px] text-text-muted font-bold uppercase tracking-wider mb-0.5">Modified</span>
              <span className="text-text-secondary">{formatDate(selectedSingleItem.modified)}</span>
            </div>
            <div className="pt-2 border-t border-border-subtle flex items-center justify-between">
              <span className="text-[9px] text-text-muted font-bold uppercase tracking-wider">Favorite</span>
              <button
                onClick={() => handleToggleFavorite(selectedSingleItem)}
                className={`flex items-center gap-1 px-2 py-1 rounded-lg border transition-colors text-[11px] ${
                  selectedSingleItem.favorite
                    ? "bg-accent-muted border-accent text-accent"
                    : "border-border bg-bg hover:bg-bg-hover text-text-secondary"
                }`}
              >
                <svg className="w-3 h-3" fill={selectedSingleItem.favorite ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.907c.961 0 1.371 1.24.588 1.81l-3.97 2.883a1 1 0 00-.364 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.971-2.883a1 1 0 00-1.18 0l-3.97 2.883c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.364-1.118l-3.97-2.883c-.783-.57-.372-1.81.588-1.81h4.906a1 1 0 00.95-.69l1.519-4.674z" />
                </svg>
                <span>{selectedSingleItem.favorite ? "Starred" : "Star"}</span>
              </button>
            </div>
          </div>

          {/* Tags */}
          <div className="space-y-2 border-t border-border-subtle pt-2">
            <span className="block text-[9px] text-text-muted font-bold uppercase tracking-wider">Tags</span>
            <div className="flex flex-wrap gap-1">
              {selectedSingleItem.tags?.map((tag) => (
                <span key={tag} className="inline-flex items-center gap-1 rounded-lg bg-bg px-1.5 py-0.5 text-[10px] text-text-secondary border border-border">
                  <span>{tag}</span>
                  <button onClick={() => handleRemoveTag(selectedSingleItem, tag)} className="text-text-muted hover:text-error transition-colors">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </span>
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
              className="w-full rounded-lg border border-border bg-bg px-2 py-1 text-[11px] text-text placeholder-text-muted focus:border-accent focus:outline-none transition-colors"
            />
          </div>

          {!selectedSingleItem.is_dir && (
            <div className="mt-auto pt-3 border-t border-border-subtle">
              <button
                onClick={() => handleDownloadFile(selectedSingleItem)}
                className="w-full py-1.5 rounded-lg bg-accent hover:bg-accent-hover text-bg font-semibold flex items-center justify-center gap-1.5 text-[11px] transition-colors"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download decrypted
              </button>
            </div>
          )}
        </div>
      ) : selectedItems.length > 1 ? (
        <div className="space-y-3">
          <div className="flex flex-col items-center gap-2 bg-bg/40 rounded-lg p-3 border border-border-subtle">
            <svg className="w-10 h-10 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
            </svg>
            <p className="font-bold text-text text-center">{selectedItems.length} items selected</p>
          </div>
          <div className="space-y-2">
            <div>
              <span className="block text-[9px] text-text-muted font-bold uppercase tracking-wider mb-0.5">Combined Size</span>
              <span className="text-text-secondary">{formatSize(selectedItems.reduce((acc, v) => acc + v.size, 0))}</span>
            </div>
            <button onClick={() => setModalExport(Array.from(selectedPaths))} className="w-full py-1.5 rounded-lg bg-accent hover:bg-accent-hover text-bg font-semibold flex items-center justify-center gap-1.5 text-[11px] transition-colors">
              Export selected ({selectedItems.length})
            </button>
            <button onClick={() => setModalDelete(Array.from(selectedPaths))} className="w-full py-1.5 rounded-lg bg-error/10 hover:bg-error/20 border border-error/20 text-error font-semibold flex items-center justify-center gap-1.5 text-[11px] transition-colors">
              Delete selected ({selectedItems.length})
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-48 border border-dashed border-border rounded-lg bg-bg/20 text-text-muted">
          <svg className="w-8 h-8 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-center px-4 text-[11px]">Select an item to inspect properties</p>
        </div>
      )}
    </aside>
  );
}
