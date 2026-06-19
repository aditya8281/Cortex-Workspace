/**
 * File list — table, list, and grid views for vault files.
 * Smooth view transitions, drag feedback.
 */
"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  Folder, File, Star, ChevronUp, ChevronDown, FolderOpen,
} from "lucide-react";
import type { VaultContext, SortKey } from "./useVaultState";
import { formatSize, formatDate, getFileCategory } from "./useVaultState";

interface Props {
  vault: VaultContext;
}

function SortIndicator({ col, vault }: { col: SortKey; vault: VaultContext }) {
  if (vault.sortKey !== col) return null;
  return (
    <span className="ml-1 text-accent">
      {vault.sortDir === "asc" ? <ChevronUp className="w-3 h-3 inline" /> : <ChevronDown className="w-3 h-3 inline" />}
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
      <div className="flex-1 overflow-y-auto p-4 relative min-h-[400px]">
        <motion.div
          className="flex flex-col items-center justify-center py-20 text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: "spring", damping: 25, stiffness: 200 }}
        >
          <div className="relative mb-5">
            <div className="absolute inset-0 rounded-full bg-accent/5 blur-xl" />
            <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-bg-surface border border-border-subtle">
              <Folder className="w-8 h-8 text-text-muted" strokeWidth={1.5} />
            </div>
          </div>
          <p className="text-sm font-bold text-text-secondary">This folder is empty</p>
          <p className="text-xs text-text-muted mt-1.5 max-w-[260px] leading-relaxed">Upload encrypted files or create a new folder to get started.</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 relative min-h-[400px]">
      <AnimatePresence mode="wait">
        {activeView === "table" ? (
          <motion.div
            key="table"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
          >
            <table className="w-full text-left border-collapse select-none text-xs">
              <thead className="sticky top-0 z-10">
                <tr className="border-b border-border-subtle text-text-muted uppercase text-[10px] tracking-wider font-mono font-semibold bg-bg-elevated/90 backdrop-blur-sm">
                  {sortColumns.map((col) => (
                    <th
                      key={col.key}
                      className={`py-2.5 px-3 cursor-pointer hover:bg-bg-hover hover:text-text transition-colors select-none rounded-lg ${col.width}`}
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
                      onDragStart={(e) => handleDragStart(e as unknown as React.DragEvent, item)}
                      onDragEnd={handleDragEnd}
                      onDragOver={item.is_dir ? (e) => handleDragOverFolder(e as unknown as React.DragEvent, item.path) : undefined}
                      onDrop={item.is_dir ? (e) => handleDropOnFolder(e as unknown as React.DragEvent, item.path) : undefined}
                      className={`file-item border-b border-border-subtle/50 cursor-pointer transition-all duration-150 ${
                        isSelected
                          ? "selected"
                          : isDragOver
                            ? "bg-accent-muted border-l-2 border-l-accent"
                            : "text-text hover:bg-bg-hover/60"
                      }`}
                    >
                      <td className="py-2.5 px-3 flex items-center gap-2.5 font-medium min-w-0">
                        <button
                          onClick={(e) => { e.stopPropagation(); handleToggleFavorite(item); }}
                          className={`p-0.5 rounded hover:bg-bg-hover transition-colors shrink-0 ${item.favorite ? "text-accent" : "text-text-muted hover:text-text-secondary"}`}
                        >
                          <Star className="w-3 h-3" fill={item.favorite ? "currentColor" : "none"} />
                        </button>
                        {item.is_dir ? (
                          <Folder className="w-4 h-4 text-accent shrink-0" />
                        ) : (
                          <File className="w-4 h-4 text-text-muted shrink-0" />
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
          </motion.div>
        ) : activeView === "list" ? (
          <motion.div
            key="list"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
            className="space-y-0.5 select-none"
          >
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
                  onDragStart={(e) => handleDragStart(e as unknown as React.DragEvent, item)}
                  onDragEnd={handleDragEnd}
                  onDragOver={item.is_dir ? (e) => handleDragOverFolder(e as unknown as React.DragEvent, item.path) : undefined}
                  onDrop={item.is_dir ? (e) => handleDropOnFolder(e as unknown as React.DragEvent, item.path) : undefined}
                  className={`file-item flex items-center justify-between rounded-xl px-3 py-2 cursor-pointer transition-all duration-150 text-xs ${
                    isSelected
                      ? "selected font-semibold"
                      : isDragOver
                        ? "bg-accent-muted border-l-2 border-l-accent"
                        : "text-text border border-transparent hover:border-border-subtle hover:bg-bg-hover/40"
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    {item.is_dir ? (
                      <Folder className="w-4 h-4 text-accent shrink-0" />
                    ) : (
                      <File className="w-4 h-4 text-text-muted shrink-0" />
                    )}
                    <span className="truncate font-medium">{item.name}</span>
                  </div>
                  <div className="flex items-center gap-4 text-text-muted text-[11px]">
                    <span>{item.is_dir ? "Folder" : formatSize(item.size)}</span>
                    <span className="font-mono">{formatDate(item.modified)}</span>
                  </div>
                </div>
              );
            })}
          </motion.div>
        ) : (
          <motion.div
            key="grid"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
            className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-3 xl:grid-cols-4 gap-3 select-none"
          >
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
                  onDragStart={(e) => handleDragStart(e as unknown as React.DragEvent, item)}
                  onDragEnd={handleDragEnd}
                  onDragOver={item.is_dir ? (e) => handleDragOverFolder(e as unknown as React.DragEvent, item.path) : undefined}
                  onDrop={item.is_dir ? (e) => handleDropOnFolder(e as unknown as React.DragEvent, item.path) : undefined}
                  className={`file-item interactive-card relative flex flex-col items-center justify-center p-4 text-center hover:-translate-y-0.5 active:scale-[0.98] transition-all duration-200 ${
                    isSelected
                      ? "selected !bg-accent-faint !border-accent"
                      : isDragOver
                        ? "bg-accent-muted border-accent text-accent"
                        : ""
                  }`}
                >
                  {item.favorite && (
                    <div className="absolute top-2 right-2 text-accent">
                      <Star className="w-3 h-3" fill="currentColor" />
                    </div>
                  )}
                  {item.is_dir ? (
                    <FolderOpen className="w-10 h-10 text-accent mb-2.5" strokeWidth={1.5} />
                  ) : (
                    <File className="w-10 h-10 text-text-secondary mb-2.5" strokeWidth={1.5} />
                  )}
                  <span className="text-xs font-bold text-text max-w-full truncate px-1">{item.name}</span>
                  <span className="text-[10px] text-text-muted mt-1 font-mono">{item.is_dir ? "Folder" : formatSize(item.size)}</span>
                </div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Status Bar */}
      <div className="glass-panel-strong absolute bottom-0 left-0 right-0 flex items-center justify-between rounded-none border-t border-border-subtle px-4 py-2 text-[10px] text-text-muted font-mono">
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
          <span>{vault.currentFolder}</span>
        </div>
      </div>
    </div>
  );
}
