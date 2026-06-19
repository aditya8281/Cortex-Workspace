"use client";

import { useMemo, useState } from "react";
import { getFileCategory } from "../utils";
import type { SortKey, SortDir } from "../utils";
import type { VaultFileEntry } from "../../../src/shared/types";

interface UseVaultViewParams {
  files: VaultFileEntry[];
  recursiveFiles: VaultFileEntry[];
  currentFolder: string;
}

export default function useVaultView({ files, recursiveFiles, currentFolder }: UseVaultViewParams) {
  const [activeCategory, setActiveCategory] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("name");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [activeView, setActiveView] = useState<"table" | "list" | "grid">("table");

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => d === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const currentViewItems = useMemo(() => {
    let list: VaultFileEntry[] = [];
    if (activeCategory === "all") {
      list = files;
    } else {
      list = recursiveFiles.filter((item) => {
        if (item.is_dir) return false;
        const ext = "." + item.name.split(".").pop()?.toLowerCase();
        switch (activeCategory) {
          case "documents":
            return [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".txt", ".md", ".json", ".yaml", ".yml", ".xml"].includes(ext);
          case "images":
            return [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"].includes(ext);
          case "archives":
            return [".zip", ".tar", ".gz", ".7z", ".rar"].includes(ext);
          case "certificates":
            return [".key", ".pem", ".crt", ".cer", ".der", ".p12", ".pfx"].includes(ext);
          case "favorites":
            return !!item.favorite;
          case "recent":
            return true;
          default:
            return false;
        }
      });
      if (activeCategory === "recent") {
        list = [...list].sort((a, b) => (b.modified ?? 0) - (a.modified ?? 0)).slice(0, 20);
      }
    }

    const q = searchQuery.trim().toLowerCase();
    if (q) {
      list = list.filter((item) => {
        const matchName = item.name.toLowerCase().includes(q);
        const matchTags = item.tags?.some((t) => t.toLowerCase().includes(q)) ?? false;
        return matchName || matchTags;
      });
    }

    list.sort((a, b) => {
      if (a.is_dir && !b.is_dir) return -1;
      if (!a.is_dir && b.is_dir) return 1;

      let cmp = 0;
      switch (sortKey) {
        case "name": cmp = a.name.localeCompare(b.name); break;
        case "type": cmp = getFileCategory(a.name).localeCompare(getFileCategory(b.name)); break;
        case "size": cmp = a.size - b.size; break;
        case "created": cmp = (a.created ?? 0) - (b.created ?? 0); break;
        case "modified": cmp = (a.modified ?? 0) - (b.modified ?? 0); break;
      }
      return sortDir === "asc" ? cmp : -cmp;
    });

    return list;
  }, [files, recursiveFiles, activeCategory, searchQuery, sortKey, sortDir]);

  const currentTitle = useMemo(() => {
    if (activeCategory !== "all") return activeCategory.charAt(0).toUpperCase() + activeCategory.slice(1);
    return currentFolder === "/" ? "Vault" : currentFolder.split("/").pop() ?? "Vault";
  }, [activeCategory, currentFolder]);

  const breadcrumbs = useMemo(() => {
    if (activeCategory !== "all") {
      return [{ name: "Vault", path: "/" }, { name: activeCategory, path: "" }];
    }
    const parts = currentFolder.split("/").filter(Boolean);
    const result = [{ name: "Vault", path: "/" }];
    let acc = "";
    parts.forEach((p) => { acc += "/" + p; result.push({ name: p, path: acc }); });
    return result;
  }, [activeCategory, currentFolder]);

  return {
    activeCategory,
    searchQuery,
    sortKey,
    sortDir,
    activeView,
    setActiveCategory,
    setSearchQuery,
    setSortKey,
    setSortDir,
    setActiveView,
    handleSort,
    currentViewItems,
    currentTitle,
    breadcrumbs,
  };
}
