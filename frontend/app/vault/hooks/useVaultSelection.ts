"use client";

import { useMemo, useState } from "react";
import type { VaultFileEntry } from "../../../src/shared/types";

interface UseVaultSelectionParams {
  currentViewItems: VaultFileEntry[];
  setContextMenu: (menu: { visible: boolean; x: number; y: number; target: VaultFileEntry } | null) => void;
}

export default function useVaultSelection({ currentViewItems, setContextMenu }: UseVaultSelectionParams) {
  const [selectedPaths, setSelectedPaths] = useState<Set<string>>(new Set());
  const [lastSelectedPath, setLastSelectedPath] = useState<string | null>(null);

  const selectedItems = useMemo(() =>
    currentViewItems.filter((item) => selectedPaths.has(item.path)),
    [currentViewItems, selectedPaths],
  );

  const selectedSingleItem = selectedItems.length === 1 ? selectedItems[0] : null;

  const handleItemClick = (e: React.MouseEvent, item: VaultFileEntry) => {
    if (e.button !== 0) return;
    setContextMenu(null);
    const newSelected = new Set(selectedPaths);
    if (e.ctrlKey || e.metaKey) {
      if (newSelected.has(item.path)) newSelected.delete(item.path);
      else newSelected.add(item.path);
      setLastSelectedPath(item.path);
    } else if (e.shiftKey && lastSelectedPath) {
      const pathsList = currentViewItems.map((v) => v.path);
      const startIdx = pathsList.indexOf(lastSelectedPath);
      const endIdx = pathsList.indexOf(item.path);
      if (startIdx !== -1 && endIdx !== -1) {
        const min = Math.min(startIdx, endIdx);
        const max = Math.max(startIdx, endIdx);
        for (let i = min; i <= max; i++) newSelected.add(pathsList[i]);
      }
    } else {
      newSelected.clear();
      newSelected.add(item.path);
      setLastSelectedPath(item.path);
    }
    setSelectedPaths(newSelected);
  };

  const handlePanelClick = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest(".file-item") || (e.target as HTMLElement).closest(".toolbar-btn")) return;
    setSelectedPaths(new Set());
    setLastSelectedPath(null);
    setContextMenu(null);
  };

  const handleContextMenu = (e: React.MouseEvent, item: VaultFileEntry) => {
    e.preventDefault();
    if (!selectedPaths.has(item.path)) {
      setSelectedPaths(new Set([item.path]));
      setLastSelectedPath(item.path);
    }
    setContextMenu({ visible: true, x: e.clientX, y: e.clientY, target: item });
  };

  return {
    selectedPaths,
    lastSelectedPath,
    setSelectedPaths,
    setLastSelectedPath,
    handleItemClick,
    handlePanelClick,
    handleContextMenu,
    selectedItems,
    selectedSingleItem,
  };
}
