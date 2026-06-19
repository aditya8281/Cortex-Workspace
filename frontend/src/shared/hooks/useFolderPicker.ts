"use client";

import { useState, useCallback } from "react";
import { getFolderPicker, type FolderPickerResult } from "../services/folder-picker";

export default function useFolderPicker() {
  const [result, setResult] = useState<FolderPickerResult | null>(null);
  const [isSupported] = useState(() => getFolderPicker().isSupported());

  const pick = useCallback(async () => {
    const r = await getFolderPicker().pickFolder();
    if (r) setResult(r);
    return r;
  }, []);

  const clear = useCallback(() => setResult(null), []);

  return { result, pick, isSupported, clear };
}
