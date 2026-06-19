import type { FolderPickerAdapter, FolderPickerResult } from './types';

/**
 * Tauri adapter — swap this in when wrapping the app with Tauri.
 *
 * Uses @tauri-apps/api/dialog.open({ directory: true }).
 * To enable:
 *   1. Install: npm install @tauri-apps/api
 *   2. Uncomment the import and pickFolder body below
 *   3. Call setFolderPicker(new TauriFolderPicker()) at app init
 *   4. Set isSupported() to return true
 */
export class TauriFolderPicker implements FolderPickerAdapter {
  async pickFolder(): Promise<FolderPickerResult | null> {
    // TODO: Uncomment when @tauri-apps/api is installed
    // import { open } from '@tauri-apps/api/dialog';
    //
    // const selected = await open({
    //   directory: true,
    //   multiple: false,
    //   title: 'Select folder',
    // });
    //
    // if (typeof selected === 'string') {
    //   const name = selected.split(/[\\/]/).filter(Boolean).pop() || selected;
    //   return { path: selected, name };
    // }
    //
    // return null;
    throw new Error('Tauri adapter not yet implemented — install @tauri-apps/api and uncomment');
  }

  isSupported(): boolean {
    return false;
  }
}
