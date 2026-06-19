"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import type { VaultFileEntry } from "../../../src/shared/types";

interface UseVaultNavigationParams {
  loadFiles: (folder?: string) => Promise<void>;
  currentFolder: string;
  setCurrentFolder: (folder: string) => void;
  setActiveCategory: (category: string) => void;
  setSelectedPaths: (paths: Set<string>) => void;
  recursiveFiles: VaultFileEntry[];
  activeCategory: string;
}

export default function useVaultNavigation({
  loadFiles,
  currentFolder,
  setCurrentFolder,
  setActiveCategory,
  setSelectedPaths,
  recursiveFiles,
  activeCategory,
}: UseVaultNavigationParams) {
  const [navHistory, setNavHistory] = useState<string[]>(["/"]);
  const [navIndex, setNavIndex] = useState(0);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(["/"]));
  const [editingTreePath, setEditingTreePath] = useState<string | null>(null);
  const [treeContextMenu, setTreeContextMenu] = useState<{ visible: boolean; x: number; y: number; path: string } | null>(null);
  const [addressBarEditing, setAddressBarEditing] = useState(false);
  const [addressBarValue, setAddressBarValue] = useState("/");
  const addressInputRef = useRef<HTMLInputElement>(null);

  const navigateTo = useCallback((folder: string, addToHistory = true) => {
    setActiveCategory("all");
    setCurrentFolder(folder);
    setSelectedPaths(new Set());
    if (addToHistory) {
      setNavHistory((prev) => {
        const newHistory = prev.slice(0, navIndex + 1);
        newHistory.push(folder);
        return newHistory;
      });
      setNavIndex((prev) => prev + 1);
    }
    loadFiles(folder);
    const parts = folder.split("/").filter(Boolean);
    let acc = "";
    setExpandedFolders((prev) => {
      const newExpanded = new Set(prev);
      newExpanded.add("/");
      for (const p of parts) {
        acc += "/" + p;
        newExpanded.add(acc);
      }
      return newExpanded;
    });
  }, [loadFiles, navIndex, setActiveCategory, setCurrentFolder, setExpandedFolders, setNavHistory, setNavIndex, setSelectedPaths]);

  const navigateBack = useCallback(() => {
    if (navIndex > 0) {
      const newIndex = navIndex - 1;
      setNavIndex(newIndex);
      const folder = navHistory[newIndex];
      setActiveCategory("all");
      setCurrentFolder(folder);
      setSelectedPaths(new Set());
      loadFiles(folder);
    }
  }, [navIndex, navHistory, loadFiles, setActiveCategory, setCurrentFolder, setSelectedPaths]);

  const navigateForward = useCallback(() => {
    if (navIndex < navHistory.length - 1) {
      const newIndex = navIndex + 1;
      setNavIndex(newIndex);
      const folder = navHistory[newIndex];
      setActiveCategory("all");
      setCurrentFolder(folder);
      setSelectedPaths(new Set());
      loadFiles(folder);
    }
  }, [navIndex, navHistory, loadFiles, setActiveCategory, setCurrentFolder, setSelectedPaths]);

  const navigateUp = useCallback(() => {
    if (currentFolder === "/") return;
    const parent = currentFolder.substring(0, currentFolder.lastIndexOf("/")) || "/";
    navigateTo(parent);
  }, [currentFolder, navigateTo]);

  const handleAddressBarSubmit = () => {
    setAddressBarEditing(false);
    const path = addressBarValue.trim() || "/";
    if (path.startsWith("/")) {
      navigateTo(path);
    } else {
      navigateTo("/" + path);
    }
  };

  const folderTree = useMemo(() => {
    return recursiveFiles
      .filter((f) => f.is_dir)
      .sort((a, b) => a.path.localeCompare(b.path));
  }, [recursiveFiles]);

  const buildTreeChildren = useCallback((parentPath: string) => {
    return folderTree.filter((f) => {
      if (f.path === parentPath) return false;
      const parent = parentPath === "/" ? "/" : parentPath + "/";
      return f.path.startsWith(parent) && !f.path.slice(parent.length).includes("/");
    }).sort((a, b) => a.name.localeCompare(b.name));
  }, [folderTree]);

  const toggleFolder = useCallback((path: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  }, []);

  const effectiveAddressBarValue = activeCategory !== "all"
    ? `/${activeCategory}`
    : addressBarEditing
      ? addressBarValue
      : currentFolder;

  return {
    navHistory,
    navIndex,
    expandedFolders,
    editingTreePath,
    treeContextMenu,
    addressBarEditing,
    addressBarValue,
    addressInputRef,
    setNavHistory,
    setNavIndex,
    setExpandedFolders,
    setEditingTreePath,
    setTreeContextMenu,
    setAddressBarEditing,
    setAddressBarValue,
    navigateTo,
    navigateBack,
    navigateForward,
    navigateUp,
    handleAddressBarSubmit,
    folderTree,
    buildTreeChildren,
    toggleFolder,
    effectiveAddressBarValue,
  };
}
