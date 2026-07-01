"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { VaultIcon, SearchIcon } from "@/shared/ui/icons";
import { cn } from "@/shared/lib/utils";
import gsap from "gsap";
import { Draggable as DraggablePlugin } from "gsap/Draggable";
import { Flip } from "gsap/Flip";

gsap.registerPlugin(DraggablePlugin, Flip);

// ── Types ─────────────────────────────────────────────────────────────

interface VaultStatus {
  locked: boolean;
  has_vault_password: boolean;
}

interface VaultFileInfo {
  name: string;
  path: string;
  is_dir: boolean;
  size: number | null;
  modified: number | null;
  created: number | null;
  favorite: boolean;
  tags: string[];
}

interface VaultUploadResponse {
  path: string;
  name: string;
  size: number;
}

// ── Helpers ───────────────────────────────────────────────────────────

function formatSize(bytes: number | null): string {
  if (bytes == null) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatTime(ts: number | null): string {
  if (ts == null) return "—";
  return new Date(ts * 1000).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getFileIcon(name: string): string {
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  const img = ["png", "jpg", "jpeg", "gif", "svg", "webp"];
  const doc = ["txt", "md", "pdf", "csv", "json"];
  const code = ["py", "js", "ts", "tsx", "jsx", "rs", "go", "c", "cpp", "h"];
  if (img.includes(ext)) return "🖼️";
  if (doc.includes(ext)) return "📄";
  if (code.includes(ext)) return "💻";
  return "📁";
}

// ── Lock Screen ───────────────────────────────────────────────────────

function LockScreen({ onUnlocked }: { onUnlocked: () => void }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleUnlock = useCallback(async () => {
    if (!password.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/privacy/vault/unlock`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ vault_password: password }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? `Unlock failed (${res.status})`);
      }
      onUnlocked();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to unlock vault");
    } finally {
      setLoading(false);
    }
  }, [password, onUnlocked, API_BASE]);

  return (
    <div className="flex h-full items-center justify-center p-6">
      <div className={cn(
        "w-full max-w-sm rounded-2xl border p-8 text-center",
        "border-accent-red/30 bg-bg-widget backdrop-blur-xl",
        "shadow-[0_0_30px_-5px] shadow-accent-red/10",
      )}>
        {/* Icon */}
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-red/10">
          <VaultIcon size={28} className="text-accent-red" />
        </div>

        <h2 className="text-title font-semibold text-text-primary mb-1">Vault Locked</h2>
        <p className="text-sm text-text-muted mb-6">
          Enter your vault password to access encrypted files
        </p>

        {/* Password input */}
        <div className="space-y-3">
          <input
            ref={inputRef}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleUnlock(); }}
            placeholder="Vault password"
            autoComplete="current-password"
            aria-label="Vault password"
            className={cn(
              "w-full rounded-xl border px-4 py-2.5 text-sm",
              "bg-bg-surface text-text-primary placeholder:text-text-muted",
              "border-border-default focus:border-accent-red/50 focus:outline-none focus:ring-1 focus:ring-accent-red/25",
              "motion-safe:transition-colors motion-safe:duration-150",
            )}
          />

          {error && (
            <p className="text-xs text-danger animate-shake">{error}</p>
          )}

          <button
            onClick={handleUnlock}
            disabled={loading || !password.trim()}
            className={cn(
              "w-full rounded-xl py-2.5 text-sm font-semibold text-white",
              "bg-accent-red hover:bg-accent-red/90",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "motion-safe:transition-all motion-safe:duration-150",
              loading && "animate-pulse",
            )}
          >
            {loading ? "Unlocking…" : "Unlock Vault"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── File Row ──────────────────────────────────────────────────────────

function FileRow({
  file,
  onDelete,
  onRename,
  onDownload,
  onToggleFav,
  isFlatFile,
}: {
  file: VaultFileInfo;
  onDelete: (path: string) => void;
  onRename: (path: string, name: string) => void;
  onDownload: (path: string, name: string) => void;
  onToggleFav: (path: string) => void;
  isFlatFile?: boolean;
}) {
  const [renaming, setRenaming] = useState(false);
  const [newName, setNewName] = useState(file.name);

  return (
    <div
      data-file-path={file.path}
      className={cn(
        "group flex items-center gap-3 px-3 py-2.5 rounded-lg",
        "hover:bg-bg-hover motion-safe:transition-colors motion-safe:duration-150",
        file.is_dir && "text-accent",
        isFlatFile && "cursor-grab active:cursor-grabbing",
      )}>
      {/* Icon */}
      <span className="flex-shrink-0 text-base">{getFileIcon(file.name)}</span>

      {/* Name */}
      <div className="flex-1 min-w-0">
        {renaming ? (
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") { onRename(file.path, newName); setRenaming(false); }
              if (e.key === "Escape") { setRenaming(false); setNewName(file.name); }
            }}
            onBlur={() => { onRename(file.path, newName); setRenaming(false); }}
            autoFocus
            className="w-full bg-bg-surface text-sm text-text-primary rounded px-1.5 py-0.5 border border-accent/50 focus:outline-none"
          />
        ) : (
          <p className="text-sm text-text-primary truncate">{file.name}</p>
        )}
      </div>

      {/* Size */}
      {!file.is_dir && (
        <span className="text-xs text-text-muted tabular-nums hidden sm:block w-20 text-right">
          {formatSize(file.size)}
        </span>
      )}

      {/* Modified */}
      <span className="text-xs text-text-muted hidden md:block w-24 text-right tabular-nums">
        {formatTime(file.modified)}
      </span>

      {/* Tags */}
      {file.tags.length > 0 && (
        <div className="hidden lg:flex items-center gap-1">
          {file.tags.slice(0, 2).map((t) => (
            <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-bg-surface text-text-muted">
              {t}
            </span>
          ))}
        </div>
      )}

      {/* Favorite */}
      <button
        onClick={() => onToggleFav(file.path)}
        className={cn(
          "min-h-[44px] min-w-[44px] flex items-center justify-center",
          "text-base opacity-0 group-hover:opacity-100 motion-safe:transition-all motion-safe:duration-150",
          file.favorite ? "text-warning opacity-100" : "text-text-muted hover:text-warning",
        )}
        title={file.favorite ? "Unfavorite" : "Favorite"}
      >
        {file.favorite ? "★" : "☆"}
      </button>

      {/* Actions */}
      <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 motion-safe:transition-all motion-safe:duration-150">
        {!file.is_dir && (
          <button
            onClick={() => onDownload(file.path, file.name)}
            className="min-h-[44px] min-w-[44px] rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-elevated flex items-center justify-center motion-safe:transition-colors motion-safe:duration-150"
            title="Download"
          >
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M8 1v10m0 0l-4-4m4 4l4-4M2 13v1a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-1" />
            </svg>
          </button>
        )}
        <button
          onClick={() => { setNewName(file.name); setRenaming(true); }}
          className="min-h-[44px] min-w-[44px] rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-elevated flex items-center justify-center motion-safe:transition-colors motion-safe:duration-150"
          title="Rename"
        >
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 1.5l2.5 2.5L5 13.5 2 14l.5-3L12 1.5z" />
          </svg>
        </button>
        <button
          onClick={() => onDelete(file.path)}
          className="min-h-[44px] min-w-[44px] rounded-lg text-text-muted hover:text-danger hover:bg-danger/10 flex items-center justify-center motion-safe:transition-colors motion-safe:duration-150"
          title="Delete"
        >
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M2 4h12M5 4V2.5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1V4m-8 0v9a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4" />
          </svg>
        </button>
      </div>
    </div>
  );
}

// ── Upload Modal ──────────────────────────────────────────────────────

function UploadModal({ open, onClose, onUploaded }: { open: boolean; onClose: () => void; onUploaded: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const handleUpload = useCallback(async () => {
    if (!file) return;
    setUploading(true);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${API_BASE}/api/v1/privacy/vault/files/upload?folder=/`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });
      if (!res.ok) throw new Error(`Upload failed (${res.status})`);
      const data: VaultUploadResponse = await res.json();
      setResult(`Uploaded ${data.name} (${formatSize(data.size)})`);
      onUploaded();
    } catch (err) {
      setResult(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }, [file, onUploaded, API_BASE]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div
        className="w-full max-w-sm rounded-2xl border border-border-subtle bg-bg-widget backdrop-blur-xl p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-title font-semibold text-text-primary mb-1">Upload to Vault</h3>
        <p className="text-sm text-text-muted mb-4">Encrypt and store a file in your vault.</p>

        <label
          id="vault-upload-label"
          className={cn(
            "flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-8 mb-4 cursor-pointer",
            "border-border-subtle hover:border-accent-red/50 hover:bg-accent-red/5",
            "motion-safe:transition-colors motion-safe:duration-150",
            file && "border-accent-red/50 bg-accent-red/5",
          )}
          aria-label="Click to select a file for upload"
        >
          {file ? (
            <div className="text-center">
              <p className="text-sm text-text-primary font-medium">{file.name}</p>
              <p className="text-xs text-text-muted mt-1">{formatSize(file.size)}</p>
            </div>
          ) : (
            <div className="text-center">
              <VaultIcon size={24} className="text-text-muted mb-2 mx-auto" />
              <p className="text-sm text-text-muted">Drop a file or click to browse</p>
              <p className="text-xs text-text-muted mt-1">Max 10 MB</p>
            </div>
          )}
          <input
            type="file"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </label>

        {result && (
          <p className={cn("text-xs mb-3", result.includes("failed") ? "text-danger" : "text-success")}>
            {result}
          </p>
        )}

        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 rounded-xl py-2 text-sm font-medium text-text-muted hover:text-text-primary hover:bg-bg-hover motion-safe:transition-colors motion-safe:duration-150"
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className={cn(
              "flex-1 rounded-xl py-2 text-sm font-semibold text-white",
              "bg-accent-red hover:bg-accent-red/90",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "motion-safe:transition-colors motion-safe:duration-150",
            )}
          >
            {uploading ? "Encrypting…" : "Upload & Encrypt"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function VaultPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [locked, setLocked] = useState(true);
  const [files, setFiles] = useState<VaultFileInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const fileListRef = useRef<HTMLDivElement>(null);
  const draggableInstances = useRef<DraggablePlugin[]>([]);

  useEffect(() => {
    if (!authLoading && !user) router.push("/auth");
  }, [user, authLoading, router]);

  // Check vault status on mount
  useEffect(() => {
    if (authLoading || !user) return;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/privacy/vault/status`, { credentials: "include" });
        if (res.ok) {
          const data: VaultStatus = await res.json();
          setLocked(data.locked);
        }
      } catch { /* ignore */ }
    })();
  }, [user, authLoading]);

  const fetchFiles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/privacy/vault/files?folder=/&recursive=true`, { credentials: "include" });
      if (!res.ok) throw new Error(`Failed to load files (${res.status})`);
      const data: VaultFileInfo[] = await res.json();
      setFiles(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load files");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleUnlocked = useCallback(() => {
    setLocked(false);
    fetchFiles();
  }, [fetchFiles]);

  const handleLock = useCallback(async () => {
    try {
      await fetch(`${API_BASE}/api/v1/privacy/vault/lock`, {
        method: "POST",
        credentials: "include",
      });
      setLocked(true);
      setFiles([]);
    } catch { /* ignore */ }
  }, []);

  const handleDelete = useCallback(async (path: string) => {
    if (!confirm(`Delete "${path.split("/").pop()}"? This cannot be undone.`)) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/privacy/vault/files/${encodeURIComponent(path)}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error("Delete failed");
      setFiles((prev) => prev.filter((f) => f.path !== path));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }, []);

  const handleRename = useCallback(async (path: string, newName: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/privacy/vault/files/${encodeURIComponent(path)}/rename`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ new_name: newName }),
      });
      if (!res.ok) throw new Error("Rename failed");
      fetchFiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rename failed");
    }
  }, [fetchFiles]);

  const handleDownload = useCallback((path: string, name: string) => {
    const url = `${API_BASE}/api/v1/privacy/vault/files/download/${encodeURIComponent(path)}`;
    const a = window.document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
  }, []);

  const handleToggleFav = useCallback(async (path: string) => {
    const file = files.find((f) => f.path === path);
    if (!file) return;
    try {
      await fetch(`${API_BASE}/api/v1/privacy/vault/files/${encodeURIComponent(path)}/metadata`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ favorite: !file.favorite }),
      });
      setFiles((prev) => prev.map((f) => f.path === path ? { ...f, favorite: !f.favorite } : f));
    } catch { /* ignore */ }
  }, [files]);

  // ── Draggable + Flip for flat file reorder ──────────────────────────
  useEffect(() => {
    if (!fileListRef.current) return;
    const items = fileListRef.current.querySelectorAll("[data-file-path]");
    if (items.length < 2) return;

    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      draggableInstances.current = DraggablePlugin.create(items, {
        type: "y",
        bounds: fileListRef.current,
        edgeResistance: 0.85,
        dragResistance: 0.1,
        onDragStart: function () {
          gsap.set(this.target, { transform: "none" });
        },
        onDragEnd: function () {
          const container = fileListRef.current!;
          const all = Array.from(container.querySelectorAll("[data-file-path]"));
          const idx = all.indexOf(this.target);
          if (idx < 0) return;

          const rect = this.target.getBoundingClientRect();
          const mid = rect.top + rect.height / 2;

          let swapIdx = -1;
          for (let i = 0; i < all.length; i++) {
            if (i === idx) continue;
            const ir = all[i].getBoundingClientRect();
            if (mid >= ir.top && mid <= ir.bottom) { swapIdx = i; break; }
          }
          if (swapIdx < 0 || swapIdx === idx) return;

          const state = Flip.getState(all);

          if (swapIdx < idx) {
            container.insertBefore(this.target, all[swapIdx]);
          } else {
            container.insertBefore(this.target, all[swapIdx].nextSibling);
          }

          Flip.from(state, {
            duration: 0.35,
            ease: "power3.inOut",
            absolute: true,
            scale: false,
            target: container.querySelectorAll("[data-file-path]"),
          });
        },
      });
    });
    return () => {
      mm.revert();
      draggableInstances.current.forEach((d) => d.kill());
      draggableInstances.current = [];
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [files, searchQuery]);

  if (authLoading || !user) return null;

  // ── Show lock screen ────────────────────────────────────────────
  if (locked) {
    return <LockScreen onUnlocked={handleUnlocked} />;
  }

  // ── Filtered files ──────────────────────────────────────────────
  const filteredFiles = searchQuery.trim()
    ? files.filter((f) => f.name.toLowerCase().includes(searchQuery.toLowerCase()))
    : files;

  // Separate dirs and files
  const dirs = filteredFiles.filter((f) => f.is_dir);
  const flatFiles = filteredFiles.filter((f) => !f.is_dir);

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between px-6 pt-5 pb-3 border-b border-border-subtle">
        <div>
          <h1 className="text-headline font-semibold text-text-primary">Vault</h1>
          <p className="text-sm text-text-secondary mt-0.5">
            Encrypted file storage
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setUploadOpen(true)}
            className={cn(
              "flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-medium",
              "bg-accent-red text-white hover:bg-accent-red/90",
              "motion-safe:transition-colors motion-safe:duration-150",
            )}
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M8 2v12M2 8h12" />
            </svg>
            Upload
          </button>
          <button
            onClick={handleLock}
            className={cn(
              "flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium",
              "text-text-muted hover:text-text-primary hover:bg-bg-hover",
              "motion-safe:transition-colors motion-safe:duration-150",
            )}
            title="Lock vault"
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="7" width="10" height="8" rx="1" />
              <path d="M5 7V5a3 3 0 0 1 6 0v2" />
            </svg>
            Lock
          </button>
        </div>
      </div>

      {/* Search bar */}
      <div className="flex-shrink-0 px-6 py-3 border-b border-border-subtle">
        <div className="relative max-w-md">
          <SearchIcon size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search vault files…"
            className={cn(
              "w-full pl-8 pr-3 py-1.5 rounded-lg text-xs",
              "bg-bg-surface text-text-primary placeholder:text-text-muted",
              "border border-border-default focus:border-accent/50 focus:outline-none focus:ring-1 focus:ring-accent/25",
              "motion-safe:transition-colors motion-safe:duration-150",
            )}
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {error && (
          <div className="rounded-lg border border-danger/20 bg-danger/5 px-4 py-3 mb-4">
            <p className="text-sm text-danger">{error}</p>
            <button onClick={() => { setError(null); fetchFiles(); }} className="mt-1 text-xs text-danger underline">
              Retry
            </button>
          </div>
        )}

        {loading ? (
          <div className="space-y-1">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-12 rounded-lg bg-bg-surface animate-pulse" />
            ))}
          </div>
        ) : filteredFiles.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <VaultIcon size={40} className="text-text-muted/20 mb-4" />
            <p className="text-title font-semibold text-text-primary mb-1">
              {searchQuery ? "No matching files" : "Vault is empty"}
            </p>
            <p className="text-sm text-text-muted max-w-md mb-6">
              {searchQuery
                ? `No files match "${searchQuery}"`
                : "Upload files to encrypt and store them securely in your vault."}
            </p>
            {!searchQuery && (
              <button
                onClick={() => setUploadOpen(true)}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium bg-accent-red text-white hover:bg-accent-red/90 motion-safe:transition-colors motion-safe:duration-150"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M8 2v12M2 8h12" />
                </svg>
                Upload Your First File
              </button>
            )}
          </div>
        ) : (
          <>
            {/* Directories */}
            {dirs.length > 0 && (
              <div className="mb-4">
                <p className="text-xs text-text-muted font-medium mb-2 uppercase tracking-wider">Folders</p>
                <div className="rounded-xl border border-border-subtle overflow-hidden bg-bg-widget backdrop-blur-xl">
                  {dirs.map((d) => (
                    <FileRow
                      key={d.path}
                      file={d}
                      onDelete={handleDelete}
                      onRename={handleRename}
                      onDownload={handleDownload}
                      onToggleFav={handleToggleFav}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Files */}
            {flatFiles.length > 0 && (
              <div>
                <p className="text-xs text-text-muted font-medium mb-2 uppercase tracking-wider">
                  Files ({flatFiles.length})
                </p>
                <div ref={fileListRef} className="rounded-xl border border-border-subtle overflow-hidden bg-bg-widget backdrop-blur-xl">
                  {flatFiles.map((f) => (
                    <FileRow
                      key={f.path}
                      file={f}
                      isFlatFile
                      onDelete={handleDelete}
                      onRename={handleRename}
                      onDownload={handleDownload}
                      onToggleFav={handleToggleFav}
                    />
                  ))}
                </div>
              </div>
            )}

            <p className="text-xs text-text-muted mt-4 text-center">
              {files.length} file{files.length !== 1 ? "s" : ""} stored · AES-256 encrypted
            </p>
          </>
        )}
      </div>

      {/* Upload modal */}
      <UploadModal open={uploadOpen} onClose={() => setUploadOpen(false)} onUploaded={() => { fetchFiles(); setUploadOpen(false); }} />
    </div>
  );
}
