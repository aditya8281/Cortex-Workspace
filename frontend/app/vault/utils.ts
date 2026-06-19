"use client";

export const formatSize = (bytes: number) => {
  if (bytes === 0) return "-";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
};

export const formatDate = (timestamp?: number) => {
  if (!timestamp) return "-";
  return new Date(timestamp * 1000).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export const getFileCategory = (filename: string) => {
  const ext = "." + filename.split(".").pop()?.toLowerCase();
  if ([".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".txt", ".md", ".json", ".yaml", ".yml", ".xml"].includes(ext)) return "Document";
  if ([".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"].includes(ext)) return "Image";
  if ([".zip", ".tar", ".gz", ".7z", ".rar"].includes(ext)) return "Archive";
  if ([".key", ".pem", ".crt", ".cer", ".der", ".p12", ".pfx"].includes(ext)) return "Certificate";
  return "File";
};

export const isTextPreviewable = (name: string) => {
  const ext = "." + name.split(".").pop()?.toLowerCase();
  return [".txt", ".md", ".json", ".csv", ".yaml", ".yml", ".py", ".js", ".ts", ".html", ".css", ".sql", ".sh", ".toml"].includes(ext);
};

export const isImagePreview = (name: string) => {
  const ext = name.split(".").pop()?.toLowerCase();
  return ["png", "jpg", "jpeg", "gif", "webp", "svg"].includes(ext ?? "");
};

export type SortKey = "name" | "type" | "size" | "created" | "modified";
export type SortDir = "asc" | "desc";
