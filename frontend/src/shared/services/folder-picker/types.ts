export interface FolderPickerResult {
  path: string;
  name: string;
}

export interface FolderPickerAdapter {
  pickFolder(): Promise<FolderPickerResult | null>;
  isSupported(): boolean;
}
