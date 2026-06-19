import type { FolderPickerAdapter, FolderPickerResult } from './types';

declare global {
  interface Window {
    showDirectoryPicker?: (options?: { mode?: 'read' | 'readwrite' }) => Promise<FileSystemDirectoryHandle>;
  }
}

export class BrowserFolderPicker implements FolderPickerAdapter {
  async pickFolder(): Promise<FolderPickerResult | null> {
    if (!this.isSupported()) return null;
    try {
      const handle = await window.showDirectoryPicker!({ mode: 'readwrite' });
      return { path: handle.name, name: handle.name };
    } catch (e) {
      if ((e as DOMException).name === 'AbortError') return null;
      throw e;
    }
  }

  isSupported(): boolean {
    return typeof window !== 'undefined' && typeof window.showDirectoryPicker === 'function';
  }
}
