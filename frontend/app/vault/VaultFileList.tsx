/**
 * File list — table, list, and grid views for vault files.
 */
"use client";

import type { VaultContext, SortKey } from "./useVaultState";
import { formatSize, formatDate, getFileCategory } from "./useVaultState";

interface Props {
  vault: VaultContext;
}

function SortIndicator({ col, vault }: { col: SortKey; vault: VaultContext }) {
  if (vault.sortKey !== col) return null;
  return (
    <span className="ml-1 text-accent">
      <svg className="w-3 h-3 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d={vault.sortDir === "asc" ? "M5 15l7-7 7 7" : "M19 9l-7 7-7-7"} />
      </svg>
    </span>
  );
}

export default function VaultFileList({ vault }: Props) {
  const {
    currentViewItems, selectedPaths, dragOverFolder,
    handleItemClick, handleItemDoubleClick,
    handleContextMenu, handleSort, handleToggleFavorite,
    handleDragStart, handleDragOverFolder, handleDropOnFolder, handleDragEnd,
    selectedItems, activeView,
  } = vault;

  const sortColumns: { key: SortKey; label: string; width: string }[] = [
    { key: "name", label: "Name", width: "" },
    { key: "type", label: "Type", width: "w-24" },
    { key: "size", label: "Size", width: "w-20" },
    { key: "created", label: "Created", width: "w-36" },
    { key: "modified", label: "Modified", width: "w-36" },
  ];

  if (currentViewItems.length === 0) {
    return (
      <div className="flex-1 overflow-y-auto p-3 relative min-h-[400px]">
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <svg className="w-14 h-14 text-text-muted mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
          </svg>
          <p className="text-sm font-semibold text-text-secondary">This folder is empty</p>
          <p className="text-xs text-text-muted mt-1.5 max-w-xs">Upload encrypted files or create a new folder to get started.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-3 relative min-h-[400px]">
      {activeView === "table" ? (
        <table className="w-full text-left border-collapse select-none text-xs">
          <thead className="sticky top-0 z-10">
            <tr className="border-b border-border text-text-muted uppercase text-[10px] tracking-wider font-semibold bg-bg/90 backdrop-blur-sm">
              {sortColumns.map((col) => (
                <th
                  key={col.key}
                  className={`py-2.5 px-3 cursor-pointer hover:bg-bg-hover hover:text-text transition-colors select-none ${col.width}`}
                  onClick={() => handleSort(col.key)}
                >
                  {col.label}<SortIndicator col={col.key} vault={vault} />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {currentViewItems.map((item) => {
              const isSelected = selectedPaths.has(item.path);
              const isDragOver = dragOverFolder === item.path && item.is_dir;
              return (
                <tr
                  key={item.path}
                  onClick={(e) => handleItemClick(e, item)}
                  onDoubleClick={() => handleItemDoubleClick(item)}
                  onContextMenu={(e) => handleContextMenu(e, item)}
                  draggable
                  onDragStart={(e) => handleDragStart(e, item)}
                  onDragEnd={handleDragEnd}
                  onDragOver={item.is_dir ? (e) => handleDragOverFolder(e, item.path) : undefined}
                  onDrop={item.is_dir ? (e) => handleDropOnFolder(e, item.path) : undefined}
                  className={`file-item border-b border-border-subtle cursor-pointer transition-colors ${
                    isSelected
                      ? "selected"
                      : isDragOver
                        ? "bg-accent-muted border-l-2 border-l-accent"
                        : "text-text hover:bg-bg-hover/60"
                  }`}
                >
                  <td className="py-2.5 px-3 flex items-center gap-2 font-medium min-w-0">
                    <button
                      onClick={(e) => { e.stopPropagation(); handleToggleFavorite(item); }}
                      className={`p-0.5 rounded hover:bg-bg-hover transition-colors shrink-0 ${item.favorite ? "text-accent" : "text-text-muted"}`}
                    >
                      <svg className="w-3 h-3" fill={item.favorite ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.907c.961 0 1.371 1.24.588 1.81l-3.97 2.883a1 1 0 00-.364 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.971-2.883a1 1 0 00-1.18 0l-3.97 2.883c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.364-1.118l-3.97-2.883c-.783-.57-.372-1.81.588-1.81h4.906a1 1 0 00.95-.69l1.519-4.674z" />
                      </svg>
                    </button>
                    {item.is_dir ? (
                      <svg className="w-4 h-4 text-accent shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                      </svg>
                    ) : (
                      <svg className="w-4 h-4 text-text-muted shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                    )}
                    <span className="truncate">{item.name}</span>
                  </td>
                  <td className="py-2.5 px-3 text-text-secondary">{item.is_dir ? "Folder" : getFileCategory(item.name)}</td>
                  <td className="py-2.5 px-3 text-text-secondary">{formatSize(item.size)}</td>
                  <td className="py-2.5 px-3 text-text-muted">{formatDate(item.created)}</td>
                  <td className="py-2.5 px-3 text-text-muted">{formatDate(item.modified)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      ) : activeView === "list" ? (
        <div className="space-y-0.5 select-none">
          {currentViewItems.map((item) => {
            const isSelected = selectedPaths.has(item.path);
            const isDragOver = dragOverFolder === item.path && item.is_dir;
            return (
              <div
                key={item.path}
                onClick={(e) => handleItemClick(e, item)}
                onDoubleClick={() => handleItemDoubleClick(item)}
                onContextMenu={(e) => handleContextMenu(e, item)}
                draggable
                onDragStart={(e) => handleDragStart(e, item)}
                onDragEnd={handleDragEnd}
                onDragOver={item.is_dir ? (e) => handleDragOverFolder(e, item.path) : undefined}
                onDrop={item.is_dir ? (e) => handleDropOnFolder(e, item.path) : undefined}
                className={`file-item flex items-center justify-between rounded-lg px-3 py-1.5 cursor-pointer transition-colors text-xs ${
                  isSelected
                    ? "selected font-semibold"
                    : isDragOver
                      ? "bg-accent-muted border-l-2 border-l-accent"
                      : "text-text border border-transparent"
                }`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  {item.is_dir ? (
                    <svg className="w-4 h-4 text-accent shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4 text-text-muted shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                  )}
                  <span className="truncate">{item.name}</span>
                </div>
                <div className="flex items-center gap-4 text-text-muted text-[11px]">
                  <span>{item.is_dir ? "Folder" : formatSize(item.size)}</span>
                  <span>{formatDate(item.modified)}</span>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-3 xl:grid-cols-4 gap-3 select-none">
          {currentViewItems.map((item) => {
            const isSelected = selectedPaths.has(item.path);
            const isDragOver = dragOverFolder === item.path && item.is_dir;
            return (
              <div
                key={item.path}
                onClick={(e) => handleItemClick(e, item)}
                onDoubleClick={() => handleItemDoubleClick(item)}
                onContextMenu={(e) => handleContextMenu(e, item)}
                draggable
                onDragStart={(e) => handleDragStart(e, item)}
                onDragEnd={handleDragEnd}
                onDragOver={item.is_dir ? (e) => handleDragOverFolder(e, item.path) : undefined}
                onDrop={item.is_dir ? (e) => handleDropOnFolder(e, item.path) : undefined}
                className={`file-item interactive-card relative flex flex-col items-center justify-center p-3 text-center ${
                  isSelected
                    ? "selected !bg-accent-faint !border-accent"
                    : isDragOver
                      ? "bg-accent-muted border-accent text-accent"
                      : ""
                }`}
              >
                {item.favorite && (
                  <div className="absolute top-1.5 right-1.5 text-accent">
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" /></svg>
                  </div>
                )}
                {item.is_dir ? (
                  <svg className="w-10 h-10 text-accent mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                  </svg>
                ) : (
                  <svg className="w-10 h-10 text-text-secondary mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                )}
                <span className="text-xs font-semibold text-text max-w-full truncate px-1">{item.name}</span>
                <span className="text-[10px] text-text-muted mt-1">{item.is_dir ? "Folder" : formatSize(item.size)}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* Status Bar */}
      <div className="glass-panel absolute bottom-0 left-0 right-0 flex items-center justify-between rounded-none border-t border-border px-3 py-1.5 text-[10px] text-text-muted">
        <div className="flex items-center gap-3">
          <span>{currentViewItems.length} item{currentViewItems.length !== 1 ? "s" : ""}</span>
          {selectedItems.length > 0 && (
            <span className="text-accent font-medium">
              {selectedItems.length} selected
              {selectedItems.some((i) => !i.is_dir) && (
                <> ({formatSize(selectedItems.reduce((acc, v) => acc + v.size, 0))})</>
              )}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono">{vault.currentFolder}</span>
        </div>
      </div>
    </div>
  );
}
