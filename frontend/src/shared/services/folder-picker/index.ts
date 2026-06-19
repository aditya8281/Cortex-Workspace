import type { FolderPickerAdapter } from './types';
import { BrowserFolderPicker } from './browser-adapter';

let adapter: FolderPickerAdapter = new BrowserFolderPicker();

export function getFolderPicker(): FolderPickerAdapter {
  return adapter;
}

export function setFolderPicker(a: FolderPickerAdapter): void {
  adapter = a;
}

export type { FolderPickerAdapter, FolderPickerResult } from './types';
