"use client";

import { useEffect, useState } from "react";
import {
  apiVaultPreviewFile,
  apiVaultDownloadFileBlob,
} from "../../../src/shared/auth/cortexApi";
import { isTextPreviewable } from "../utils";
import type { VaultFileEntry } from "../../../src/shared/types";

interface UseVaultPreviewParams {
  setError: (error: string) => void;
}

export default function useVaultPreview({ setError }: UseVaultPreviewParams) {
  const [previewFile, setPreviewFile] = useState<VaultFileEntry | null>(null);
  const [previewBlobUrl, setPreviewBlobUrl] = useState<string | null>(null);
  const [previewText, setPreviewText] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  useEffect(() => {
    return () => { if (previewBlobUrl) URL.revokeObjectURL(previewBlobUrl); };
  }, [previewBlobUrl]);

  const handleOpenFilePreview = async (item: VaultFileEntry) => {
    setPreviewFile(item); setPreviewLoading(true); setPreviewText(null);
    if (previewBlobUrl) { URL.revokeObjectURL(previewBlobUrl); setPreviewBlobUrl(null); }
    try {
      const blob = await apiVaultPreviewFile(item.path);
      if (isTextPreviewable(item.name)) {
        setPreviewText(await blob.text());
      } else {
        setPreviewBlobUrl(URL.createObjectURL(blob));
      }
    } catch {
      setError("Unable to decrypt file preview");
      setPreviewFile(null);
    } finally { setPreviewLoading(false); }
  };

  const handleDownloadFile = async (item: VaultFileEntry) => {
    try {
      const blob = await apiVaultDownloadFileBlob(item.path);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = item.name;
      document.body.appendChild(a); a.click();
      document.body.removeChild(a); URL.revokeObjectURL(url);
    } catch { setError("Download failed"); }
  };

  return {
    previewFile,
    previewBlobUrl,
    previewText,
    previewLoading,
    setPreviewFile,
    setPreviewBlobUrl,
    setPreviewText,
    handleOpenFilePreview,
    handleDownloadFile,
  };
}
