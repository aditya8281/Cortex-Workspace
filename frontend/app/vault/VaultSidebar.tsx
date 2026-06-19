/**
 * Sidebar — folder tree + quick access categories.
 * Glass morphism sidebar with expand/collapse animations.
 */
"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  FolderLock, Files, FileText, Image, Archive, ShieldCheck, Star, Clock,
  FolderOpen, FolderClosed, ChevronRight, ChevronDown, Lock, Plus, Minus,
} from "lucide-react";
import type { VaultContext } from "./useVaultState";
import type { VaultFileEntry } from "../../src/shared/types";

interface Props {
  vault: VaultContext;
}

const categories = [
  { id: "all", label: "All Files", icon: Files },
  { id: "documents", label: "Documents", icon: FileText },
  { id: "images", label: "Images", icon: Image },
  { id: "archives", label: "Archives", icon: Archive },
  { id: "certificates", label: "Certificates", icon: ShieldCheck },
  { id: "favorites", label: "Favorites", icon: Star },
  { id: "recent", label: "Recent", icon: Clock },
];

export default function VaultSidebar({ vault }: Props) {
  const {
    activeCategory, setActiveCategory, currentFolder, navigateTo,
    expandedFolders, toggleFolder, setExpandedFolders,
    folderTree, buildTreeChildren,
    dragOverFolder, handleDragOverFolder, handleDropOnFolder, handleDragEnd,
    handleLock,
    setTreeContextMenu, setSelectedPaths,
    setModalNewFolder, setModalRename, setModalDelete, setNewFolderName, setRenameValue,
  } = vault;

  function renderTreeNodes(parentPath: string, depth: number): React.ReactNode {
    if (!expandedFolders.has(parentPath)) return null;
    const children = buildTreeChildren(parentPath);
    return children.map((child) => (
      <TreeRow
        key={child.path}
        name={child.name}
        path={child.path}
        depth={depth}
        isActive={currentFolder === child.path && activeCategory === "all"}
        isExpanded={expandedFolders.has(child.path)}
        hasChildren={folderTree.some((f) => f.path !== child.path && f.path.startsWith(child.path + "/"))}
        isDropTarget={dragOverFolder === child.path}
        onClick={() => navigateTo(child.path)}
        onToggle={() => toggleFolder(child.path)}
        onDragOver={(e) => handleDragOverFolder(e, child.path)}
        onDrop={(e) => handleDropOnFolder(e, child.path)}
        onDragEnd={handleDragEnd}
        onContextMenu={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setTreeContextMenu({ visible: true, x: e.clientX, y: e.clientY, path: child.path });
        }}
        childRenderer={(p, d) => renderTreeNodes(p, d)}
        childDepth={depth}
      />
    ));
  }

  return (
    <aside className="flex flex-col gap-3 glass-panel rounded-2xl p-3 overflow-hidden h-full">
      {/* Sidebar Header */}
      <div className="glass-panel-strong flex items-center justify-between rounded-xl px-3 py-2.5">
        <div className="flex items-center gap-2">
          <FolderLock className="h-4 w-4 text-accent" />
          <span className="text-xs font-bold text-text font-display">Explorer</span>
        </div>
      </div>

      {/* Categories */}
      <div className="flex flex-col gap-0.5">
        <p className="micro-label px-1 mb-1.5">Quick Access</p>
        {categories.map((cat) => {
          const Icon = cat.icon;
          const isActive = activeCategory === cat.id;
          return (
            <motion.button
              key={cat.id}
              onClick={() => {
                setActiveCategory(cat.id);
                if (cat.id === "all") navigateTo("/");
                else setSelectedPaths(new Set());
              }}
              whileTap={{ scale: 0.98 }}
              className={`w-full text-left flex items-center gap-2.5 py-2 px-2.5 text-[11px] rounded-xl transition-all duration-200 ${
                isActive
                  ? "nav-item active"
                  : "text-text-secondary hover:bg-bg-hover hover:text-text"
              }`}
            >
              <Icon className="w-3.5 h-3.5 shrink-0" />
              <span className="font-medium">{cat.label}</span>
            </motion.button>
          );
        })}
      </div>

      {/* Folder Tree */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="flex items-center justify-between mb-1.5 px-1">
          <p className="micro-label">Folders</p>
          <button
            onClick={() => {
              const allPaths = folderTree.map((f) => f.path);
              if (expandedFolders.size > allPaths.length / 2) {
                setExpandedFolders(new Set(["/"]));
              } else {
                setExpandedFolders(new Set(["/", ...allPaths]));
              }
            }}
            className="text-[9px] text-text-muted hover:text-accent transition-colors font-mono"
            title="Expand/Collapse All"
          >
            {expandedFolders.size > folderTree.length / 2 ? "Collapse" : "Expand"}
          </button>
        </div>
        <div className="flex-1 overflow-y-auto overflow-x-auto rounded-xl bg-bg/40 border border-border-subtle p-1.5">
          <TreeRow
            name="Vault"
            path="/"
            depth={0}
            isActive={currentFolder === "/" && activeCategory === "all"}
            isExpanded={expandedFolders.has("/")}
            hasChildren={folderTree.length > 0}
            isDropTarget={dragOverFolder === "/"}
            onClick={() => navigateTo("/")}
            onToggle={() => toggleFolder("/")}
            onDragOver={(e) => handleDragOverFolder(e, "/")}
            onDrop={(e) => handleDropOnFolder(e, "/")}
            onDragEnd={handleDragEnd}
            childDepth={0}
            childRenderer={renderTreeNodes}
          />
          {renderTreeNodes("/", 1)}
        </div>
      </div>

      {/* Lock Button */}
      <div className="border-t border-border-subtle pt-2.5 mt-auto">
        <motion.button
          onClick={handleLock}
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
          className="w-full flex items-center justify-center gap-2 rounded-xl border border-error/20 bg-error-muted hover:bg-error/20 py-2 text-[11px] text-error font-bold transition-all duration-200"
        >
          <Lock className="h-3.5 w-3.5" />
          Lock Cabinet
        </motion.button>
      </div>
    </aside>
  );
}

// ── Tree Row Component ──

function TreeRow({
  name, path, depth, isActive, isExpanded, hasChildren, isDropTarget,
  onClick, onToggle, onDragOver, onDrop, onDragEnd, onContextMenu,
  childRenderer, childDepth,
}: {
  name: string;
  path: string;
  depth: number;
  isActive: boolean;
  isExpanded: boolean;
  hasChildren: boolean;
  isDropTarget: boolean;
  onClick: () => void;
  onToggle: () => void;
  onDragOver: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => void;
  onDragEnd: () => void;
  onContextMenu?: (e: React.MouseEvent) => void;
  childRenderer?: (parentPath: string, depth: number) => React.ReactNode;
  childDepth: number;
}) {
  return (
    <>
      <motion.button
        onClick={onClick}
        onDoubleClick={(e) => { e.stopPropagation(); onToggle(); }}
        onContextMenu={onContextMenu}
        onDragOver={onDragOver}
        onDrop={onDrop}
        onDragEnd={onDragEnd}
        whileTap={{ scale: 0.98 }}
        className={`w-full text-left flex items-center gap-1.5 py-1.5 px-2 text-[11px] rounded-lg transition-all duration-150 ${
          isActive
            ? "file-item selected"
            : isDropTarget
              ? "bg-accent-muted text-accent border border-accent/20"
              : "text-text-secondary hover:bg-bg-hover hover:text-text"
        }`}
        style={{ paddingLeft: `${depth * 14 + 8}px` }}
      >
        {hasChildren ? (
          <span
            onClick={(e) => { e.stopPropagation(); onToggle(); }}
            className="w-4 h-4 flex items-center justify-center shrink-0 text-text-muted hover:text-text transition-colors"
          >
            {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          </span>
        ) : (
          <span className="w-4 h-4 shrink-0" />
        )}
        {isExpanded ? (
          <FolderOpen className="w-3.5 h-3.5 shrink-0 text-accent" />
        ) : (
          <FolderClosed className="w-3.5 h-3.5 shrink-0 text-accent/70" />
        )}
        <span className="truncate font-medium">{name}</span>
      </motion.button>
      <AnimatePresence>
        {childRenderer && isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.15 }}
          >
            {childRenderer(path, childDepth + 1)}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
