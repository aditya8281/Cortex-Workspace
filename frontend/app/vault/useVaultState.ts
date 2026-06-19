/**
 * Vault state management hook — composed from focused sub-hooks.
 */
"use client";

import { useCallback, useEffect, useRef } from "react";
import useVaultCore from "./hooks/useVaultCore";
import useVaultSelection from "./hooks/useVaultSelection";
import useVaultNavigation from "./hooks/useVaultNavigation";
import useVaultView from "./hooks/useVaultView";
import useVaultCrud from "./hooks/useVaultCrud";
import useVaultPreview from "./hooks/useVaultPreview";
import useVaultUI from "./hooks/useVaultUI";
import type { VaultFileEntry } from "../../src/shared/types";

export { formatSize, formatDate, getFileCategory, isTextPreviewable, isImagePreview } from "./utils";
export type { SortKey, SortDir } from "./utils";

export default function useVaultState() {
  const ui = useVaultUI();
  const core = useVaultCore();
  const view = useVaultView({
    files: core.files,
    recursiveFiles: core.recursiveFiles,
    currentFolder: core.currentFolder,
  });
  const selection = useVaultSelection({
    currentViewItems: view.currentViewItems,
    setContextMenu: ui.setContextMenu,
  });
  const nav = useVaultNavigation({
    loadFiles: core.loadFiles,
    currentFolder: core.currentFolder,
    setCurrentFolder: core.setCurrentFolder,
    setActiveCategory: view.setActiveCategory,
    setSelectedPaths: selection.setSelectedPaths,
    recursiveFiles: core.recursiveFiles,
    activeCategory: view.activeCategory,
  });
  const crud = useVaultCrud({
    currentFolder: core.currentFolder,
    loadFiles: core.loadFiles,
    loadRecursiveFiles: core.loadRecursiveFiles,
    setLoading: core.setLoading,
    setError: core.setError,
    setSuccessMsg: core.setSuccessMsg,
    setSelectedPaths: selection.setSelectedPaths,
  });
  const preview = useVaultPreview({
    setError: core.setError,
  });

  // ── Refs for keyboard handler ──
  const currentViewItemsRef = useRef<VaultFileEntry[]>([]);
  const handleItemDoubleClickRef = useRef<(item: VaultFileEntry) => void>(() => {});
  const navigateUpRef = useRef<() => void>(() => {});

  // ── Cross-cutting handlers ──

  const handleItemDoubleClick = (item: VaultFileEntry) => {
    if (item.is_dir) {
      nav.navigateTo(item.path);
    } else {
      preview.handleOpenFilePreview(item);
    }
  };

  // Keep refs up to date
  useEffect(() => {
    currentViewItemsRef.current = view.currentViewItems;
    handleItemDoubleClickRef.current = handleItemDoubleClick;
    navigateUpRef.current = nav.navigateUp;
  });

  // Keyboard events
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (core.status?.locked) return;
      const targetTag = (e.target as HTMLElement).tagName;
      if (targetTag === "INPUT" || targetTag === "TEXTAREA") return;

      if (e.key === "a" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        selection.setSelectedPaths(new Set(currentViewItemsRef.current.map((item) => item.path)));
      } else if (e.key === "Delete" && selection.selectedPaths.size > 0) {
        crud.setModalDelete(Array.from(selection.selectedPaths));
      } else if (e.key === "Escape") {
        selection.setSelectedPaths(new Set());
        ui.setContextMenu(null);
        nav.setTreeContextMenu(null);
      } else if (e.key === "F2" && selection.selectedPaths.size === 1) {
        const item = currentViewItemsRef.current.find((i) => selection.selectedPaths.has(i.path));
        if (item) {
          crud.setModalRename(item);
          crud.setRenameValue(item.name);
        }
      } else if (e.key === "Enter" && selection.selectedPaths.size === 1) {
        const item = currentViewItemsRef.current.find((i) => selection.selectedPaths.has(i.path));
        if (item) handleItemDoubleClickRef.current(item);
      } else if (e.key === "Backspace" && !nav.addressBarEditing) {
        e.preventDefault();
        navigateUpRef.current();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selection.selectedPaths, core.status, nav.addressBarEditing]);

  return {
    // ── Auth ──
    user: core.user,
    authLoading: core.authLoading,

    // ── State ──
    status: core.status,
    files: core.files,
    recursiveFiles: core.recursiveFiles,
    currentFolder: core.currentFolder,
    activeCategory: view.activeCategory,
    searchQuery: view.searchQuery,
    activeView: view.activeView,
    selectedPaths: selection.selectedPaths,
    lastSelectedPath: selection.lastSelectedPath,
    sortKey: view.sortKey,
    sortDir: view.sortDir,
    navHistory: nav.navHistory,
    navIndex: nav.navIndex,
    expandedFolders: nav.expandedFolders,
    treeContextMenu: nav.treeContextMenu,
    loading: core.loading,
    error: core.error,
    successMsg: core.successMsg,
    vaultPassword: core.vaultPassword,
    showPassword: core.showPassword,
    sidebarWidth: ui.sidebarWidth,
    propertiesWidth: ui.propertiesWidth,
    sidebarCollapsed: ui.sidebarCollapsed,
    propertiesCollapsed: ui.propertiesCollapsed,
    contextMenu: ui.contextMenu,
    modalNewFolder: crud.modalNewFolder,
    newFolderName: crud.newFolderName,
    modalRename: crud.modalRename,
    renameValue: crud.renameValue,
    modalDelete: crud.modalDelete,
    modalExport: crud.modalExport,
    exportDest: crud.exportDest,
    modalChangePw: crud.modalChangePw,
    oldPw: crud.oldPw,
    newPw: crud.newPw,
    confirmNewPw: crud.confirmNewPw,
    previewFile: preview.previewFile,
    previewBlobUrl: preview.previewBlobUrl,
    previewText: preview.previewText,
    previewLoading: preview.previewLoading,
    dragOverFolder: crud.dragOverFolder,
    addressBarEditing: nav.addressBarEditing,
    addressBarValue: nav.addressBarValue,

    // ── Refs ──
    fileInputRef: crud.fileInputRef,
    addressInputRef: nav.addressInputRef,
    containerRef: ui.containerRef,
    resizingRef: ui.resizingRef,

    // ── Derived ──
    currentViewItems: view.currentViewItems,
    selectedItems: selection.selectedItems,
    selectedSingleItem: selection.selectedSingleItem,
    currentTitle: view.currentTitle,
    breadcrumbs: view.breadcrumbs,
    folderTree: nav.folderTree,
    effectiveAddressBarValue: nav.effectiveAddressBarValue,

    // ── Setters ──
    setSearchQuery: view.setSearchQuery,
    setActiveView: view.setActiveView,
    setError: core.setError,
    setSuccessMsg: core.setSuccessMsg,
    setVaultPassword: core.setVaultPassword,
    setShowPassword: core.setShowPassword,
    setSidebarWidth: ui.setSidebarWidth,
    setPropertiesWidth: ui.setPropertiesWidth,
    setSidebarCollapsed: ui.setSidebarCollapsed,
    setPropertiesCollapsed: ui.setPropertiesCollapsed,
    setNewFolderName: crud.setNewFolderName,
    setRenameValue: crud.setRenameValue,
    setExportDest: crud.setExportDest,
    setOldPw: crud.setOldPw,
    setNewPw: crud.setNewPw,
    setConfirmNewPw: crud.setConfirmNewPw,
    setAddressBarEditing: nav.setAddressBarEditing,
    setAddressBarValue: nav.setAddressBarValue,
    setModalNewFolder: crud.setModalNewFolder,
    setModalRename: crud.setModalRename,
    setModalDelete: crud.setModalDelete,
    setModalExport: crud.setModalExport,
    setModalChangePw: crud.setModalChangePw,
    setPreviewFile: preview.setPreviewFile,
    setPreviewBlobUrl: preview.setPreviewBlobUrl,
    setPreviewText: preview.setPreviewText,
    setActiveCategory: view.setActiveCategory,
    setCurrentFolder: core.setCurrentFolder,
    setSelectedPaths: selection.setSelectedPaths,
    setLastSelectedPath: selection.setLastSelectedPath,
    setExpandedFolders: nav.setExpandedFolders,
    setTreeContextMenu: nav.setTreeContextMenu,
    setContextMenu: ui.setContextMenu,

    // ── Handlers ──
    handleUnlock: core.handleUnlock,
    handleLock: core.handleLock,
    handleItemClick: selection.handleItemClick,
    handlePanelClick: selection.handlePanelClick,
    handleItemDoubleClick,
    handleContextMenu: selection.handleContextMenu,
    handleSort: view.handleSort,
    handleCreateFolder: crud.handleCreateFolder,
    handleUpload: crud.handleUpload,
    handleRename: crud.handleRename,
    handleDelete: crud.handleDelete,
    handleExport: crud.handleExport,
    handleChangePassword: crud.handleChangePassword,
    handleToggleFavorite: crud.handleToggleFavorite,
    handleAddTag: crud.handleAddTag,
    handleRemoveTag: crud.handleRemoveTag,
    handleMoveItem: crud.handleMoveItem,
    handleOpenFilePreview: preview.handleOpenFilePreview,
    handleDownloadFile: preview.handleDownloadFile,
    handleDragStart: crud.handleDragStart,
    handleDragOverFolder: crud.handleDragOverFolder,
    handleDropOnFolder: crud.handleDropOnFolder,
    handleDragEnd: crud.handleDragEnd,
    navigateTo: nav.navigateTo,
    navigateBack: nav.navigateBack,
    navigateForward: nav.navigateForward,
    navigateUp: nav.navigateUp,
    handleAddressBarSubmit: nav.handleAddressBarSubmit,
    toggleFolder: nav.toggleFolder,
    buildTreeChildren: nav.buildTreeChildren,
    refreshStatus: core.refreshStatus,
    loadFiles: core.loadFiles,
    loadRecursiveFiles: core.loadRecursiveFiles,
  };
}

export type VaultContext = ReturnType<typeof useVaultState>;
