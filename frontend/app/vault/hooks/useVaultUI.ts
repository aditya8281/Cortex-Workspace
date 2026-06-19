"use client";

import { useEffect, useRef, useState } from "react";
import type { VaultFileEntry } from "../../../src/shared/types";

export default function useVaultUI() {
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("vault-sidebar-width");
      return saved ? parseInt(saved, 10) : 240;
    }
    return 240;
  });
  const [propertiesWidth, setPropertiesWidth] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("vault-properties-width");
      return saved ? parseInt(saved, 10) : 280;
    }
    return 280;
  });
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [propertiesCollapsed, setPropertiesCollapsed] = useState(false);
  const [contextMenu, setContextMenu] = useState<{
    visible: boolean; x: number; y: number; target: VaultFileEntry;
  } | null>(null);
  const resizingRef = useRef<"left" | "right" | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!resizingRef.current || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      if (resizingRef.current === "left") {
        const newWidth = Math.max(160, Math.min(400, e.clientX - rect.left));
        setSidebarWidth(newWidth);
        localStorage.setItem("vault-sidebar-width", String(newWidth));
      } else {
        const newWidth = Math.max(200, Math.min(450, rect.right - e.clientX));
        setPropertiesWidth(newWidth);
        localStorage.setItem("vault-properties-width", String(newWidth));
      }
    };
    const handleMouseUp = () => { resizingRef.current = null; };
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, []);

  useEffect(() => {
    const hide = () => { setContextMenu(null); };
    window.addEventListener("click", hide);
    return () => window.removeEventListener("click", hide);
  }, []);

  return {
    sidebarWidth,
    propertiesWidth,
    sidebarCollapsed,
    propertiesCollapsed,
    contextMenu,
    resizingRef,
    containerRef,
    setSidebarWidth,
    setPropertiesWidth,
    setSidebarCollapsed,
    setPropertiesCollapsed,
    setContextMenu,
  };
}
