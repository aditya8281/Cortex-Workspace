"use client";

import { useRef, useState, type ChangeEvent } from "react";
import {
  apiVaultDeleteFile,
  apiVaultUploadFile,
  apiVaultCreateFolder,
  apiVaultRenameItem,
  apiVaultMoveFile,
  apiVaultUpdateMetadata,
  apiVaultExport,
  apiVaultChangePassword,
} from "../../../src/shared/auth/cortexApi";
import type { VaultFileEntry } from "../../../src/shared/types";

interface UseVaultCrudParams {
  currentFolder: string;
  loadFiles: (folder?: string) => Promise<void>;
  loadRecursiveFiles: () => Promise<void>;
  setLoading: (loading: boolean) => void;
  setError: (error: string) => void;
  setSuccessMsg: (msg: string) => void;
  setSelectedPaths: (paths: Set<string>) => void;
}

export default function useVaultCrud({
  currentFolder,
  loadFiles,
  loadRecursiveFiles,
  setLoading,
  setError,
  setSuccessMsg,
  setSelectedPaths,
}: UseVaultCrudParams) {
  const [modalNewFolder, setModalNewFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [modalRename, setModalRename] = useState<VaultFileEntry | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [modalDelete, setModalDelete] = useState<string[] | null>(null);
  const [modalExport, setModalExport] = useState<string[] | null>(null);
  const [exportDest, setExportDest] = useState("~/Desktop");
  const [modalChangePw, setModalChangePw] = useState(false);
  const [oldPw, setOldPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmNewPw, setConfirmNewPw] = useState("");
  const [dragOverFolder, setDragOverFolder] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;
    setLoading(true); setError("");
    try {
      const parent = currentFolder === "/" ? "" : currentFolder + "/";
      await apiVaultCreateFolder(parent + newFolderName.trim());
      setNewFolderName(""); setModalNewFolder(false);
      await Promise.all([loadFiles(currentFolder), loadRecursiveFiles()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Folder creation failed");
    } finally { setLoading(false); }
  };

  const handleUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const filesUploaded = event.target.files;
    if (!filesUploaded || filesUploaded.length === 0) return;
    setLoading(true); setError("");
    try {
      for (let i = 0; i < filesUploaded.length; i++) {
        await apiVaultUploadFile(filesUploaded[i], currentFolder);
      }
      await Promise.all([loadFiles(currentFolder), loadRecursiveFiles()]);
      setSuccessMsg(`Uploaded ${filesUploaded.length} files.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally { setLoading(false); event.target.value = ""; }
  };

  const handleRename = async () => {
    if (!modalRename || !renameValue.trim()) return;
    setLoading(true); setError("");
    try {
      await apiVaultRenameItem(modalRename.path, renameValue.trim());
      setModalRename(null); setRenameValue("");
      await Promise.all([loadFiles(currentFolder), loadRecursiveFiles()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rename failed");
    } finally { setLoading(false); }
  };

  const handleDelete = async () => {
    if (!modalDelete) return;
    setLoading(true); setError("");
    try {
      for (const p of modalDelete) await apiVaultDeleteFile(p);
      setModalDelete(null); setSelectedPaths(new Set());
      await Promise.all([loadFiles(currentFolder), loadRecursiveFiles()]);
      setSuccessMsg("Items deleted successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    } finally { setLoading(false); }
  };

  const handleExport = async () => {
    if (!modalExport || !exportDest.trim()) return;
    setLoading(true); setError("");
    try {
      const res = await apiVaultExport({ paths: modalExport, destination_dir: exportDest });
      setModalExport(null);
      setSuccessMsg(`Successfully exported ${res.count} files to ${exportDest}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally { setLoading(false); }
  };

  const handleChangePassword = async () => {
    if (!oldPw || !newPw || !confirmNewPw) { setError("Please fill in all password fields."); return; }
    if (newPw !== confirmNewPw) { setError("New passwords do not match."); return; }
    setLoading(true); setError("");
    try {
      await apiVaultChangePassword({ old_password: oldPw, new_password: newPw });
      setModalChangePw(false); setOldPw(""); setNewPw(""); setConfirmNewPw("");
      setSuccessMsg("Vault password changed and files re-encrypted successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Password change failed");
    } finally { setLoading(false); }
  };

  const handleToggleFavorite = async (item: VaultFileEntry) => {
    try {
      await apiVaultUpdateMetadata(item.path, { favorite: !item.favorite });
      await Promise.all([loadFiles(currentFolder), loadRecursiveFiles()]);
    } catch { setError("Failed to update favorite status"); }
  };

  const handleAddTag = async (item: VaultFileEntry, tag: string) => {
    if (!tag.trim()) return;
    const currentTags = item.tags || [];
    if (currentTags.includes(tag.trim())) return;
    try {
      await apiVaultUpdateMetadata(item.path, { tags: [...currentTags, tag.trim()] });
      await Promise.all([loadFiles(currentFolder), loadRecursiveFiles()]);
    } catch { setError("Failed to add tag"); }
  };

  const handleRemoveTag = async (item: VaultFileEntry, tag: string) => {
    try {
      await apiVaultUpdateMetadata(item.path, { tags: (item.tags || []).filter((t) => t !== tag) });
      await Promise.all([loadFiles(currentFolder), loadRecursiveFiles()]);
    } catch { setError("Failed to remove tag"); }
  };

  const handleMoveItem = async (sourcePath: string, destFolder: string) => {
    setLoading(true); setError("");
    try {
      await apiVaultMoveFile(sourcePath, destFolder);
      await Promise.all([loadFiles(currentFolder), loadRecursiveFiles()]);
      setSuccessMsg("Item moved successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Move failed");
    } finally { setLoading(false); }
  };

  const handleDragStart = (e: React.DragEvent, item: VaultFileEntry) => {
    e.dataTransfer.setData("text/plain", item.path);
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDragOverFolder = (e: React.DragEvent, folderPath: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setDragOverFolder(folderPath);
  };

  const handleDropOnFolder = (e: React.DragEvent, folderPath: string) => {
    e.preventDefault();
    setDragOverFolder(null);
    const sourcePath = e.dataTransfer.getData("text/plain");
    if (sourcePath && sourcePath !== folderPath) {
      handleMoveItem(sourcePath, folderPath);
    }
  };

  const handleDragEnd = () => setDragOverFolder(null);

  return {
    modalNewFolder,
    newFolderName,
    modalRename,
    renameValue,
    modalDelete,
    modalExport,
    exportDest,
    modalChangePw,
    oldPw,
    newPw,
    confirmNewPw,
    dragOverFolder,
    fileInputRef,
    setModalNewFolder,
    setNewFolderName,
    setModalRename,
    setRenameValue,
    setModalDelete,
    setModalExport,
    setExportDest,
    setModalChangePw,
    setOldPw,
    setNewPw,
    setConfirmNewPw,
    setDragOverFolder,
    handleCreateFolder,
    handleUpload,
    handleRename,
    handleDelete,
    handleExport,
    handleChangePassword,
    handleToggleFavorite,
    handleAddTag,
    handleRemoveTag,
    handleMoveItem,
    handleDragStart,
    handleDragOverFolder,
    handleDropOnFolder,
    handleDragEnd,
  };
}
