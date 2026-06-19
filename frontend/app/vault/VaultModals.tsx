/**
 * Vault modals — context menus, dialogs, and file preview overlay.
 */
"use client";

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
      {contextMenu && contextMenu.visible && (
        <div
          className="fixed z-50 min-w-[150px] rounded-lg border border-border bg-bg-elevated/95 backdrop-blur-xl p-1 shadow-glow text-xs"
          style={{ top: contextMenu.y, left: contextMenu.x }}
        >
          <button onClick={() => handleItemDoubleClick(contextMenu.target)} className="w-full text-left py-1.5 px-2.5 rounded hover:bg-bg-hover text-text flex items-center gap-2">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d={contextMenu.target.is_dir ? "M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" : "M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"} /></svg>
            <span>{contextMenu.target.is_dir ? "Open" : "Preview"}</span>
          </button>
          {!contextMenu.target.is_dir && (
            <button onClick={() => handleOpenFilePreview(contextMenu.target)} className="w-full text-left py-1.5 px-2.5 rounded hover:bg-bg-hover text-text flex items-center gap-2">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
              <span>Preview</span>
            </button>
          )}
          <button onClick={() => setModalExport([contextMenu.target.path])} className="w-full text-left py-1.5 px-2.5 rounded hover:bg-bg-hover text-text flex items-center gap-2">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
            <span>Export</span>
          </button>
          <button onClick={() => { setModalRename(contextMenu.target); setRenameValue(contextMenu.target.name); }} className="w-full text-left py-1.5 px-2.5 rounded hover:bg-bg-hover text-text flex items-center gap-2">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
            <span>Rename</span>
          </button>
          <button onClick={() => setModalDelete([contextMenu.target.path])} className="w-full text-left py-1.5 px-2.5 rounded hover:bg-bg-hover text-error flex items-center gap-2">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
            <span>Delete</span>
          </button>
        </div>
      )}

      {/* ── Tree Context Menu ── */}
      {treeContextMenu && treeContextMenu.visible && (
        <div
          className="fixed z-50 min-w-[150px] rounded-lg border border-border bg-bg-elevated/95 backdrop-blur-xl p-1 shadow-glow text-xs"
          style={{ top: treeContextMenu.y, left: treeContextMenu.x }}
        >
          <button onClick={() => { navigateTo(treeContextMenu.path); setTreeContextMenu(null); }} className="w-full text-left py-1.5 px-2.5 rounded hover:bg-bg-hover text-text flex items-center gap-2">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" /></svg>
            <span>Open</span>
          </button>
          <button onClick={() => { setNewFolderName(""); setModalNewFolder(true); setTreeContextMenu(null); }} className="w-full text-left py-1.5 px-2.5 rounded hover:bg-bg-hover text-text flex items-center gap-2">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" /></svg>
            <span>New Folder</span>
          </button>
          <button onClick={() => {
            const folderName = treeContextMenu.path.split("/").pop() ?? "";
            setModalRename({ name: folderName, path: treeContextMenu.path, is_dir: true, size: 0 } as VaultFileEntry);
            setRenameValue(folderName);
            setTreeContextMenu(null);
          }} className="w-full text-left py-1.5 px-2.5 rounded hover:bg-bg-hover text-text flex items-center gap-2">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
            <span>Rename</span>
          </button>
          <button onClick={() => { setModalDelete([treeContextMenu.path]); setTreeContextMenu(null); }} className="w-full text-left py-1.5 px-2.5 rounded hover:bg-bg-hover text-error flex items-center gap-2">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
            <span>Delete</span>
          </button>
        </div>
      )}

      {/* ── New Folder Modal ── */}
      {modalNewFolder && (
        <div className="modal-overlay" onClick={() => { setModalNewFolder(false); setNewFolderName(""); }}>
          <div className="modal-content max-w-[360px]" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-sm font-bold text-text mb-1">Create Folder</h3>
            <p className="text-[10px] text-text-muted mb-3">{currentFolder === "/" ? "Creating in root" : `Creating in ${currentFolder}`}</p>
            <input type="text" value={newFolderName} onChange={(e) => setNewFolderName(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleCreateFolder()} placeholder="Folder name" autoFocus className="w-full rounded-lg border border-border bg-bg px-3 py-2 text-xs text-text placeholder-text-muted focus:border-accent focus:outline-none mb-4 transition-colors" />
            <div className="flex justify-end gap-2 text-xs">
              <button onClick={() => { setModalNewFolder(false); setNewFolderName(""); }} className="px-3 py-1.5 rounded-lg border border-border bg-bg hover:bg-bg-hover text-text transition-colors">Cancel</button>
              <button onClick={handleCreateFolder} disabled={loading || !newFolderName.trim()} className="px-3 py-1.5 rounded-lg bg-accent hover:bg-accent-hover text-bg font-semibold transition-colors disabled:opacity-40 flex items-center gap-1.5">
                {loading ? <span className="h-3 w-3 animate-spin rounded-full border-2 border-bg border-t-transparent" /> : null} Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Rename Modal ── */}
      {modalRename && (
        <div className="modal-overlay" onClick={() => { setModalRename(null); setRenameValue(""); }}>
          <div className="modal-content max-w-[360px]" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-sm font-bold text-text mb-1">Rename</h3>
            <p className="text-[10px] text-text-muted mb-3 truncate">Current: {modalRename.name}</p>
            <input type="text" value={renameValue} onChange={(e) => setRenameValue(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleRename()} placeholder="New name" autoFocus className="w-full rounded-lg border border-border bg-bg px-3 py-2 text-xs text-text placeholder-text-muted focus:border-accent focus:outline-none mb-4 transition-colors" />
            <div className="flex justify-end gap-2 text-xs">
              <button onClick={() => { setModalRename(null); setRenameValue(""); }} className="px-3 py-1.5 rounded-lg border border-border bg-bg hover:bg-bg-hover text-text transition-colors">Cancel</button>
              <button onClick={handleRename} disabled={loading || !renameValue.trim() || renameValue.trim() === modalRename.name} className="px-3 py-1.5 rounded-lg bg-accent hover:bg-accent-hover text-bg font-semibold transition-colors disabled:opacity-40 flex items-center gap-1.5">
                {loading ? <span className="h-3 w-3 animate-spin rounded-full border-2 border-bg border-t-transparent" /> : null} Rename
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Delete Modal ── */}
      {modalDelete && (
        <div className="modal-overlay" onClick={() => setModalDelete(null)}>
          <div className="modal-content max-w-[420px]" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-sm font-bold text-text mb-2 flex items-center gap-1.5 text-error">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" /></svg>
              <span>Confirm Delete</span>
            </h3>
            <p className="text-xs text-text-secondary mb-3 leading-relaxed">Are you sure you want to permanently delete the following {modalDelete.length} item(s)?</p>
            <div className="max-h-[120px] overflow-y-auto rounded-lg border border-border bg-bg/50 p-2 mb-4">
              {modalDelete.slice(0, 10).map((p: string) => (
                <div key={p} className="flex items-center gap-2 py-1 text-xs text-text-secondary">
                  <svg className="w-3 h-3 text-text-muted shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
                  <span className="truncate font-mono">{p.split("/").pop()}</span>
                </div>
              ))}
              {modalDelete.length > 10 && <p className="text-[10px] text-text-muted pt-1">...and {modalDelete.length - 10} more</p>}
            </div>
            <p className="text-[10px] text-error mb-4">This action is irreversible. Decrypted file keys and data will be shredded.</p>
            <div className="flex justify-end gap-2 text-xs">
              <button onClick={() => setModalDelete(null)} className="px-3 py-1.5 rounded-lg border border-border bg-bg hover:bg-bg-hover text-text transition-colors">Cancel</button>
              <button onClick={handleDelete} disabled={loading} className="px-3 py-1.5 rounded-lg bg-error hover:bg-red-600 text-white font-semibold transition-colors disabled:opacity-40 flex items-center gap-1.5">
                {loading ? <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" /> : null} Delete {modalDelete.length} item(s)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Export Modal ── */}
      {modalExport && (
        <div className="modal-overlay" onClick={() => setModalExport(null)}>
          <div className="modal-content max-w-[420px]" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-sm font-bold text-text mb-2">Export Decrypted Files</h3>
            <p className="text-xs text-text-muted mb-4">Decrypt and copy {modalExport.length} selected item(s) to a local directory on your machine.</p>
            <div className="mb-3">
              <label className="block text-[10px] font-bold text-text-muted uppercase tracking-wider mb-1.5">Shortcut Presets</label>
              <div className="flex gap-2">
                {[{ label: "Desktop", path: "~/Desktop" }, { label: "Downloads", path: "~/Downloads" }, { label: "Documents", path: "~/Documents" }].map((preset) => (
                  <button key={preset.label} type="button" onClick={() => setExportDest(preset.path)} className={`interactive-card px-2.5 py-1.5 text-xs font-semibold ${exportDest === preset.path ? "!border-accent !text-accent" : ""}`}>
                    {preset.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="mb-4">
              <label className="block text-[10px] font-bold text-text-muted uppercase tracking-wider mb-1.5">Target Directory Path</label>
              <input type="text" value={exportDest} onChange={(e) => setExportDest(e.target.value)} placeholder="Absolute folder path" className="w-full rounded-lg border border-border bg-bg px-3 py-2 text-xs text-text placeholder-text-muted focus:border-accent focus:outline-none font-mono transition-colors" />
            </div>
            <div className="flex justify-end gap-2 text-xs">
              <button onClick={() => setModalExport(null)} className="px-3 py-1.5 rounded-lg border border-border bg-bg hover:bg-bg-hover text-text transition-colors">Cancel</button>
              <button onClick={handleExport} disabled={loading || !exportDest.trim()} className="px-3 py-1.5 rounded-lg bg-accent hover:bg-accent-hover text-bg font-semibold transition-colors disabled:opacity-40">Decrypt & Export</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Change Password Modal ── */}
      {modalChangePw && (
        <div className="modal-overlay" onClick={() => { setModalChangePw(false); setOldPw(""); setNewPw(""); setConfirmNewPw(""); }}>
          <div className="modal-content max-w-[380px]" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-sm font-bold text-text mb-2">Vault Rekey (Change Password)</h3>
            <p className="text-xs text-text-muted mb-4 leading-relaxed">Changes your locker password. The system will recursively decrypt and re-encrypt all existing items in your vault. Do not close the window.</p>
            <div className="space-y-3 mb-4">
              <div>
                <label className="block text-[9px] font-bold text-text-muted uppercase tracking-wider mb-1.5">Current Password</label>
                <input type="password" value={oldPw} onChange={(e) => setOldPw(e.target.value)} className="w-full rounded-lg border border-border bg-bg px-3 py-2 text-xs text-text placeholder-text-muted focus:border-accent focus:outline-none transition-colors" placeholder="Enter current password" />
              </div>
              <div>
                <label className="block text-[9px] font-bold text-text-muted uppercase tracking-wider mb-1.5">New Password</label>
                <input type="password" value={newPw} onChange={(e) => setNewPw(e.target.value)} className="w-full rounded-lg border border-border bg-bg px-3 py-2 text-xs text-text placeholder-text-muted focus:border-accent focus:outline-none transition-colors" placeholder="Enter new password" />
              </div>
              <div>
                <label className="block text-[9px] font-bold text-text-muted uppercase tracking-wider mb-1.5">Confirm New Password</label>
                <input type="password" value={confirmNewPw} onChange={(e) => setConfirmNewPw(e.target.value)} className="w-full rounded-lg border border-border bg-bg px-3 py-2 text-xs text-text placeholder-text-muted focus:border-accent focus:outline-none transition-colors" placeholder="Confirm new password" />
              </div>
            </div>
            <div className="flex justify-end gap-2 text-xs">
              <button onClick={() => { setModalChangePw(false); setOldPw(""); setNewPw(""); setConfirmNewPw(""); }} className="px-3 py-1.5 rounded-lg border border-border bg-bg hover:bg-bg-hover text-text transition-colors">Cancel</button>
              <button onClick={handleChangePassword} disabled={loading || !oldPw || !newPw || !confirmNewPw} className="px-3 py-1.5 rounded-lg bg-accent hover:bg-accent-hover text-bg font-semibold transition-colors disabled:opacity-40">Rotate Key</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Preview Modal ── */}
      {previewFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-bg/95 backdrop-blur-md p-4">
          <div className="w-full max-w-[900px] h-[90vh] rounded-xl border border-border bg-bg-surface flex flex-col shadow-modal animate-fade-in-scale overflow-hidden">
            <div className="flex items-center justify-between border-b border-border px-5 py-4 bg-bg/40">
              <div className="min-w-0">
                <span className="text-[10px] text-accent uppercase font-bold tracking-wider">Preview</span>
                <h3 className="text-sm font-bold text-text truncate mt-0.5">{previewFile.name}</h3>
              </div>
              <button onClick={() => { setPreviewFile(null); setPreviewText(null); if (previewBlobUrl) { URL.revokeObjectURL(previewBlobUrl); setPreviewBlobUrl(null); } }} className="p-1.5 rounded-lg hover:bg-bg-hover text-text-muted hover:text-text transition-colors">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4 flex items-center justify-center bg-bg/10 relative">
              {previewLoading ? (
                <div className="flex flex-col items-center gap-2">
                  <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                  <p className="text-xs text-text-muted font-medium">Decrypting file...</p>
                </div>
              ) : previewText !== null ? (
                <pre className="w-full h-full overflow-auto text-xs font-mono p-5 bg-bg rounded-lg border border-border whitespace-pre-wrap text-text-secondary select-text">{previewText}</pre>
              ) : previewBlobUrl && previewFile.name.toLowerCase().endsWith(".pdf") ? (
                <iframe className="w-full h-full rounded-lg border border-border" src={previewBlobUrl} />
              ) : previewBlobUrl && isImagePreview(previewFile.name) ? (
                <img className="max-w-full max-h-full object-contain rounded-lg border border-border" src={previewBlobUrl} alt={previewFile.name} />
              ) : (
                <div className="flex flex-col items-center justify-center text-center">
                  <svg className="w-14 h-14 text-text-muted mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                  <p className="text-xs font-semibold text-text-secondary">Preview not supported for this file type.</p>
                  <p className="text-[10px] text-text-muted mt-1">Download to view on your local system.</p>
                </div>
              )}
            </div>
            <div className="border-t border-border px-5 py-3 flex justify-end gap-2 bg-bg/40">
              <button onClick={() => handleDownloadFile(previewFile)} className="px-4 py-1.5 rounded-lg bg-accent hover:bg-accent-hover text-bg text-xs font-bold transition-colors flex items-center gap-1.5">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                Download Decrypted
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
