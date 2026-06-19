/**
 * Sidebar — folder tree + quick access categories.
 */
"use client";

import type { VaultContext } from "./useVaultState";
import type { VaultFileEntry } from "../../src/shared/types";

interface Props {
  vault: VaultContext;
}

const categories = [
  { id: "all", label: "All Files", icon: "M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" },
  { id: "documents", label: "Documents", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" },
  { id: "images", label: "Images", icon: "M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" },
  { id: "archives", label: "Archives", icon: "M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" },
  { id: "certificates", label: "Certificates", icon: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" },
  { id: "favorites", label: "Favorites", icon: "M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.907c.961 0 1.371 1.24.588 1.81l-3.97 2.883a1 1 0 00-.364 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.971-2.883a1 1 0 00-1.18 0l-3.97 2.883c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.364-1.118l-3.97-2.883c-.783-.57-.372-1.81.588-1.81h4.906a1 1 0 00.95-.69l1.519-4.674z" },
  { id: "recent", label: "Recent", icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" },
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
    <aside className="flex flex-col gap-3 border border-border bg-bg-surface rounded-l-xl p-3 overflow-hidden">
      {/* Sidebar Header */}
      <div className="glass-panel-strong flex items-center justify-between rounded-lg px-3 py-2">
        <div className="flex items-center gap-1.5">
          <svg className="h-3.5 w-3.5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <span className="text-xs font-bold text-text">Explorer</span>
        </div>
      </div>

      {/* Categories */}
      <div className="flex flex-col gap-0.5">
        <p className="text-[9px] font-bold tracking-wider text-text-muted uppercase mb-1 px-1">Quick Access</p>
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => {
              setActiveCategory(cat.id);
              if (cat.id === "all") navigateTo("/");
              else setSelectedPaths(new Set());
            }}
            className={`w-full text-left flex items-center gap-2 py-1.5 px-2 text-[11px] rounded-lg transition-colors ${
              activeCategory === cat.id
                ? "nav-item active"
                : "text-text-secondary hover:bg-bg-hover hover:text-text"
            }`}
          >
            <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d={cat.icon} />
            </svg>
            <span>{cat.label}</span>
          </button>
        ))}
      </div>

      {/* Folder Tree */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="flex items-center justify-between mb-1 px-1">
          <p className="text-[9px] font-bold tracking-wider text-text-muted uppercase">Folders</p>
          <button
            onClick={() => {
              const allPaths = folderTree.map((f) => f.path);
              if (expandedFolders.size > allPaths.length / 2) {
                setExpandedFolders(new Set(["/"]));
              } else {
                setExpandedFolders(new Set(["/", ...allPaths]));
              }
            }}
            className="text-[9px] text-text-muted hover:text-accent transition-colors"
            title="Expand/Collapse All"
          >
            {expandedFolders.size > folderTree.length / 2 ? "Collapse" : "Expand"}
          </button>
        </div>
        <div className="flex-1 overflow-y-auto overflow-x-auto border border-border-subtle rounded-lg bg-bg/50 p-1">
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
      <div className="border-t border-border pt-2 mt-auto">
        <button
          onClick={handleLock}
          className="w-full flex items-center justify-center gap-1.5 rounded-lg border border-error/20 bg-error/10 hover:bg-error/20 py-1.5 text-[11px] text-error font-medium transition-colors"
        >
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          Lock Cabinet
        </button>
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
      <button
        onClick={onClick}
        onDoubleClick={(e) => { e.stopPropagation(); onToggle(); }}
        onContextMenu={onContextMenu}
        onDragOver={onDragOver}
        onDrop={onDrop}
        onDragEnd={onDragEnd}
        className={`w-full text-left flex items-center gap-1 py-[3px] px-1 text-[11px] rounded-lg transition-colors ${
          isActive
            ? "file-item selected"
            : isDropTarget
              ? "bg-accent-muted text-accent"
              : "text-text-secondary hover:bg-bg-hover"
        }`}
        style={{ paddingLeft: `${depth * 14 + 4}px` }}
      >
        {hasChildren ? (
          <span
            onClick={(e) => { e.stopPropagation(); onToggle(); }}
            className="w-3.5 h-3.5 flex items-center justify-center shrink-0 text-text-muted hover:text-text"
          >
            {isExpanded ? "\u25BE" : "\u25B8"}
          </span>
        ) : (
          <span className="w-3.5 h-3.5 shrink-0" />
        )}
        <svg className="w-3.5 h-3.5 shrink-0 text-accent/70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isExpanded ? "M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" : "M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"} />
        </svg>
        <span className="truncate">{name}</span>
      </button>
      {childRenderer && isExpanded && childRenderer(path, childDepth + 1)}
    </>
  );
}
