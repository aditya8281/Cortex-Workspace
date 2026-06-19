/**
 * Vault modals — context menus, dialogs, and file preview overlay.
 * New modal designs with framer-motion.
 */
"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  FolderOpen, Eye, Download, Pencil, Trash2, AlertTriangle, X,
  File, Folder, FolderPlus,
} from "lucide-react";
import type { VaultContext } from "./useVaultState";
import { isTextPreviewable, isImagePreview } from "./useVaultState";
import type { VaultFileEntry } from "../../src/shared/types";

interface Props {
  vault: VaultContext;
}

export default function VaultModals({ vault }: Props) {
  const {
    contextMenu, treeContextMenu, previewFile, previewBlobUrl, previewText, previewLoading,
    modalNewFolder, newFolderName, modalRename, renameValue, modalDelete, modalExport, exportDest,
    modalChangePw, oldPw, newPw, confirmNewPw, currentFolder, loading,
    handleItemDoubleClick, handleOpenFilePreview, handleCreateFolder, handleRename, handleDelete,
    handleExport, handleChangePassword, handleDownloadFile, navigateTo,
    setContextMenu, setTreeContextMenu, setNewFolderName, setModalNewFolder,
    setModalRename, setRenameValue, setModalDelete, setModalExport, setExportDest,
    setModalChangePw, setOldPw, setNewPw, setConfirmNewPw,
    setPreviewFile, setPreviewText, setPreviewBlobUrl,
  } = vault;

  return (
    <>
      {/* ── Context Menu ── */}
      <AnimatePresence>
        {contextMenu && contextMenu.visible && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -4 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -4 }}
            transition={{ duration: 0.1 }}
            className="fixed z-50 min-w-[160px] glass-panel-strong rounded-xl p-1.5 shadow-modal text-xs"
            style={{ top: contextMenu.y, left: contextMenu.x }}
          >
            <ContextMenuRow
              icon={contextMenu.target.is_dir ? <FolderOpen className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              label={contextMenu.target.is_dir ? "Open" : "Preview"}
              onClick={() => handleItemDoubleClick(contextMenu.target)}
            />
            {!contextMenu.target.is_dir && (
              <ContextMenuRow
                icon={<Eye className="w-3.5 h-3.5" />}
                label="Preview"
                onClick={() => handleOpenFilePreview(contextMenu.target)}
              />
            )}
            <ContextMenuRow
              icon={<Download className="w-3.5 h-3.5" />}
              label="Export"
              onClick={() => setModalExport([contextMenu.target.path])}
            />
            <ContextMenuRow
              icon={<Pencil className="w-3.5 h-3.5" />}
              label="Rename"
              onClick={() => { setModalRename(contextMenu.target); setRenameValue(contextMenu.target.name); }}
            />
            <ContextMenuRow
              icon={<Trash2 className="w-3.5 h-3.5" />}
              label="Delete"
              onClick={() => setModalDelete([contextMenu.target.path])}
              destructive
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Tree Context Menu ── */}
      <AnimatePresence>
        {treeContextMenu && treeContextMenu.visible && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -4 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -4 }}
            transition={{ duration: 0.1 }}
            className="fixed z-50 min-w-[160px] glass-panel-strong rounded-xl p-1.5 shadow-modal text-xs"
            style={{ top: treeContextMenu.y, left: treeContextMenu.x }}
          >
            <ContextMenuRow
              icon={<FolderOpen className="w-3.5 h-3.5" />}
              label="Open"
              onClick={() => { navigateTo(treeContextMenu.path); setTreeContextMenu(null); }}
            />
            <ContextMenuRow
              icon={<FolderPlus className="w-3.5 h-3.5" />}
              label="New Folder"
              onClick={() => { setNewFolderName(""); setModalNewFolder(true); setTreeContextMenu(null); }}
            />
            <ContextMenuRow
              icon={<Pencil className="w-3.5 h-3.5" />}
              label="Rename"
              onClick={() => {
                const folderName = treeContextMenu.path.split("/").pop() ?? "";
                setModalRename({ name: folderName, path: treeContextMenu.path, is_dir: true, size: 0 } as VaultFileEntry);
                setRenameValue(folderName);
                setTreeContextMenu(null);
              }}
            />
            <ContextMenuRow
              icon={<Trash2 className="w-3.5 h-3.5" />}
              label="Delete"
              onClick={() => { setModalDelete([treeContextMenu.path]); setTreeContextMenu(null); }}
              destructive
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── New Folder Modal ── */}
      <ModalShell open={modalNewFolder} onClose={() => { setModalNewFolder(false); setNewFolderName(""); }}>
        <h3 className="text-sm font-bold text-text mb-1 font-display">Create Folder</h3>
        <p className="text-[10px] text-text-muted mb-4 font-mono">{currentFolder === "/" ? "Creating in root" : `Creating in ${currentFolder}`}</p>
        <input
          type="text"
          value={newFolderName}
          onChange={(e) => setNewFolderName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCreateFolder()}
          placeholder="Folder name"
          autoFocus
          className="w-full rounded-xl border border-border-subtle bg-bg px-4 py-3 text-xs text-text placeholder-text-muted focus:border-accent focus:ring-2 focus:ring-accent/10 outline-none mb-5 transition-all duration-200"
        />
        <div className="flex justify-end gap-2 text-xs">
          <button onClick={() => { setModalNewFolder(false); setNewFolderName(""); }} className="px-4 py-2 rounded-xl border border-border-subtle bg-bg-surface hover:bg-bg-hover text-text transition-colors font-medium">Cancel</button>
          <motion.button
            onClick={handleCreateFolder}
            disabled={loading || !newFolderName.trim()}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            className="px-4 py-2 rounded-xl bg-accent hover:bg-accent-hover text-bg font-bold transition-all duration-200 disabled:opacity-40 flex items-center gap-1.5"
          >
            {loading ? <div className="h-3 w-3 animate-spin rounded-full border-2 border-bg border-t-transparent" /> : null} Create
          </motion.button>
        </div>
      </ModalShell>

      {/* ── Rename Modal ── */}
      <ModalShell open={!!modalRename} onClose={() => { setModalRename(null); setRenameValue(""); }}>
        <h3 className="text-sm font-bold text-text mb-1 font-display">Rename</h3>
        <p className="text-[10px] text-text-muted mb-4 truncate font-mono">Current: {modalRename?.name}</p>
        <input
          type="text"
          value={renameValue}
          onChange={(e) => setRenameValue(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleRename()}
          placeholder="New name"
          autoFocus
          className="w-full rounded-xl border border-border-subtle bg-bg px-4 py-3 text-xs text-text placeholder-text-muted focus:border-accent focus:ring-2 focus:ring-accent/10 outline-none mb-5 transition-all duration-200"
        />
        <div className="flex justify-end gap-2 text-xs">
          <button onClick={() => { setModalRename(null); setRenameValue(""); }} className="px-4 py-2 rounded-xl border border-border-subtle bg-bg-surface hover:bg-bg-hover text-text transition-colors font-medium">Cancel</button>
          <motion.button
            onClick={handleRename}
            disabled={loading || !renameValue.trim() || renameValue.trim() === modalRename?.name}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            className="px-4 py-2 rounded-xl bg-accent hover:bg-accent-hover text-bg font-bold transition-all duration-200 disabled:opacity-40 flex items-center gap-1.5"
          >
            {loading ? <div className="h-3 w-3 animate-spin rounded-full border-2 border-bg border-t-transparent" /> : null} Rename
          </motion.button>
        </div>
      </ModalShell>

      {/* ── Delete Modal ── */}
      <ModalShell open={!!modalDelete} onClose={() => setModalDelete(null)}>
        <div className="flex items-center gap-2 mb-2 text-error">
          <AlertTriangle className="w-4 h-4" />
          <h3 className="text-sm font-bold font-display">Confirm Delete</h3>
        </div>
        <p className="text-xs text-text-secondary mb-3 leading-relaxed">Are you sure you want to permanently delete the following {modalDelete?.length} item(s)?</p>
        <div className="max-h-[120px] overflow-y-auto rounded-xl border border-border-subtle bg-bg/50 p-2.5 mb-4">
          {modalDelete?.slice(0, 10).map((p: string) => (
            <div key={p} className="flex items-center gap-2 py-1 text-xs text-text-secondary">
              <File className="w-3 h-3 text-text-muted shrink-0" />
              <span className="truncate font-mono">{p.split("/").pop()}</span>
            </div>
          ))}
          {(modalDelete?.length ?? 0) > 10 && <p className="text-[10px] text-text-muted pt-1 font-mono">...and {(modalDelete?.length ?? 0) - 10} more</p>}
        </div>
        <p className="text-[10px] text-error mb-4 font-mono">This action is irreversible. Decrypted file keys and data will be shredded.</p>
        <div className="flex justify-end gap-2 text-xs">
          <button onClick={() => setModalDelete(null)} className="px-4 py-2 rounded-xl border border-border-subtle bg-bg-surface hover:bg-bg-hover text-text transition-colors font-medium">Cancel</button>
          <motion.button
            onClick={handleDelete}
            disabled={loading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            className="px-4 py-2 rounded-xl bg-error hover:bg-red-600 text-white font-bold transition-all duration-200 disabled:opacity-40 flex items-center gap-1.5"
          >
            {loading ? <div className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" /> : null} Delete {modalDelete?.length} item(s)
          </motion.button>
        </div>
      </ModalShell>

      {/* ── Export Modal ── */}
      <ModalShell open={!!modalExport} onClose={() => setModalExport(null)}>
        <h3 className="text-sm font-bold text-text mb-1 font-display">Export Decrypted Files</h3>
        <p className="text-xs text-text-muted mb-4">Decrypt and copy {modalExport?.length} selected item(s) to a local directory on your machine.</p>
        <div className="mb-3">
          <label className="micro-label mb-1.5 block">Shortcut Presets</label>
          <div className="flex gap-2">
            {[{ label: "Desktop", path: "~/Desktop" }, { label: "Downloads", path: "~/Downloads" }, { label: "Documents", path: "~/Documents" }].map((preset) => (
              <button key={preset.label} type="button" onClick={() => setExportDest(preset.path)} className={`interactive-card px-3 py-2 text-xs font-semibold ${exportDest === preset.path ? "!border-accent !text-accent" : ""}`}>
                {preset.label}
              </button>
            ))}
          </div>
        </div>
        <div className="mb-5">
          <label className="micro-label mb-1.5 block">Target Directory Path</label>
          <input type="text" value={exportDest} onChange={(e) => setExportDest(e.target.value)} placeholder="Absolute folder path" className="w-full rounded-xl border border-border-subtle bg-bg px-4 py-3 text-xs text-text placeholder-text-muted focus:border-accent focus:ring-2 focus:ring-accent/10 outline-none font-mono transition-all duration-200" />
        </div>
        <div className="flex justify-end gap-2 text-xs">
          <button onClick={() => setModalExport(null)} className="px-4 py-2 rounded-xl border border-border-subtle bg-bg-surface hover:bg-bg-hover text-text transition-colors font-medium">Cancel</button>
          <motion.button
            onClick={handleExport}
            disabled={loading || !exportDest.trim()}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            className="px-4 py-2 rounded-xl bg-accent hover:bg-accent-hover text-bg font-bold transition-all duration-200 disabled:opacity-40"
          >
            Decrypt & Export
          </motion.button>
        </div>
      </ModalShell>

      {/* ── Change Password Modal ── */}
      <ModalShell open={modalChangePw} onClose={() => { setModalChangePw(false); setOldPw(""); setNewPw(""); setConfirmNewPw(""); }}>
        <h3 className="text-sm font-bold text-text mb-1 font-display">Vault Rekey (Change Password)</h3>
        <p className="text-xs text-text-muted mb-4 leading-relaxed">Changes your locker password. The system will recursively decrypt and re-encrypt all existing items in your vault. Do not close the window.</p>
        <div className="space-y-3 mb-5">
          <div>
            <label className="micro-label mb-1.5 block">Current Password</label>
            <input type="password" value={oldPw} onChange={(e) => setOldPw(e.target.value)} className="w-full rounded-xl border border-border-subtle bg-bg px-4 py-3 text-xs text-text placeholder-text-muted focus:border-accent focus:ring-2 focus:ring-accent/10 outline-none transition-all duration-200" placeholder="Enter current password" />
          </div>
          <div>
            <label className="micro-label mb-1.5 block">New Password</label>
            <input type="password" value={newPw} onChange={(e) => setNewPw(e.target.value)} className="w-full rounded-xl border border-border-subtle bg-bg px-4 py-3 text-xs text-text placeholder-text-muted focus:border-accent focus:ring-2 focus:ring-accent/10 outline-none transition-all duration-200" placeholder="Enter new password" />
          </div>
          <div>
            <label className="micro-label mb-1.5 block">Confirm New Password</label>
            <input type="password" value={confirmNewPw} onChange={(e) => setConfirmNewPw(e.target.value)} className="w-full rounded-xl border border-border-subtle bg-bg px-4 py-3 text-xs text-text placeholder-text-muted focus:border-accent focus:ring-2 focus:ring-accent/10 outline-none transition-all duration-200" placeholder="Confirm new password" />
          </div>
        </div>
        <div className="flex justify-end gap-2 text-xs">
          <button onClick={() => { setModalChangePw(false); setOldPw(""); setNewPw(""); setConfirmNewPw(""); }} className="px-4 py-2 rounded-xl border border-border-subtle bg-bg-surface hover:bg-bg-hover text-text transition-colors font-medium">Cancel</button>
          <motion.button
            onClick={handleChangePassword}
            disabled={loading || !oldPw || !newPw || !confirmNewPw}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            className="px-4 py-2 rounded-xl bg-accent hover:bg-accent-hover text-bg font-bold transition-all duration-200 disabled:opacity-40"
          >
            Rotate Key
          </motion.button>
        </div>
      </ModalShell>

      {/* ── Preview Modal ── */}
      <AnimatePresence>
        {previewFile && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-void/90 backdrop-blur-md p-4"
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="w-full max-w-[900px] h-[90vh] rounded-2xl border border-border-subtle bg-bg-elevated flex flex-col shadow-modal overflow-hidden"
            >
              <div className="flex items-center justify-between border-b border-border-subtle px-5 py-4 bg-bg-surface/50">
                <div className="min-w-0">
                  <span className="micro-label text-accent">Preview</span>
                  <h3 className="text-sm font-bold text-text truncate mt-0.5 font-display">{previewFile.name}</h3>
                </div>
                <motion.button
                  onClick={() => { setPreviewFile(null); setPreviewText(null); if (previewBlobUrl) { URL.revokeObjectURL(previewBlobUrl); setPreviewBlobUrl(null); } }}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  className="p-2 rounded-xl hover:bg-bg-hover text-text-muted hover:text-text transition-colors"
                >
                  <X className="w-4 h-4" />
                </motion.button>
              </div>
              <div className="flex-1 overflow-auto p-4 flex items-center justify-center bg-bg/10 relative">
                {previewLoading ? (
                  <div className="flex flex-col items-center gap-3">
                    <div className="h-10 w-10 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                    <p className="text-xs text-text-muted font-medium font-mono">Decrypting file...</p>
                  </div>
                ) : previewText !== null ? (
                  <pre className="w-full h-full overflow-auto text-xs font-mono p-5 bg-bg-surface rounded-xl border border-border-subtle whitespace-pre-wrap text-text-secondary select-text">{previewText}</pre>
                ) : previewBlobUrl && previewFile.name.toLowerCase().endsWith(".pdf") ? (
                  <iframe className="w-full h-full rounded-xl border border-border-subtle" src={previewBlobUrl} />
                ) : previewBlobUrl && isImagePreview(previewFile.name) ? (
                  <img className="max-w-full max-h-full object-contain rounded-xl border border-border-subtle" src={previewBlobUrl} alt={previewFile.name} />
                ) : (
                  <div className="flex flex-col items-center justify-center text-center">
                    <File className="w-14 h-14 text-text-muted mb-3" strokeWidth={1.5} />
                    <p className="text-xs font-bold text-text-secondary">Preview not supported for this file type.</p>
                    <p className="text-[10px] text-text-muted mt-1">Download to view on your local system.</p>
                  </div>
                )}
              </div>
              <div className="border-t border-border-subtle px-5 py-3 flex justify-end gap-2 bg-bg-surface/50">
                <motion.button
                  onClick={() => handleDownloadFile(previewFile)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.97 }}
                  className="px-4 py-2 rounded-xl bg-accent hover:bg-accent-hover text-bg text-xs font-bold transition-all duration-200 flex items-center gap-2 shadow-glow"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download Decrypted
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// ── Shared modal shell ──

function ModalShell({ open, onClose, children }: { open: boolean; onClose: () => void; children: React.ReactNode }) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="modal-overlay"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="modal-content max-w-[380px]"
            onClick={(e) => e.stopPropagation()}
          >
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ── Context menu row ──

function ContextMenuRow({ icon, label, onClick, destructive }: { icon: React.ReactNode; label: string; onClick: () => void; destructive?: boolean }) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left py-2 px-3 rounded-lg flex items-center gap-2.5 transition-colors ${
        destructive
          ? "text-error hover:bg-error-muted"
          : "text-text hover:bg-bg-hover"
      }`}
    >
      <span className={destructive ? "text-error" : "text-text-muted"}>{icon}</span>
      <span className="font-medium">{label}</span>
    </button>
  );
}
