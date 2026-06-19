# Phase 5: Desktop V1 (Tauri v2)

**Goal:** Convert the web app to a Tauri v2 desktop app with offline capabilities. Backend becomes a sidecar process. File system access, native menus, system tray, and auto-updates.

**Depends on:** Phase 0-B (service abstraction, storage resolver), Phase 4 (intelligence), Phase 3 (agents)

**IMPORTANT:** This plan uses Tauri v2 APIs. Tauri v1 has different APIs (allowlist, SystemTray). This plan does NOT use v1 patterns.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│              TAURI v2 SHELL                     │
│  ┌──────────────┐    ┌──────────────────────┐  │
│  │   Frontend   │    │   Sidecar Process    │  │
│  │   (Vite)     │◄──►│   (FastAPI)          │  │
│  │   React      │    │   Python + Rust       │  │
│  └──────────────┘    └──────────────────────┘  │
│         │                      │                │
│  ┌──────▼──────────────────────▼──────────────┐│
│  │         Tauri v2 Plugins                   ││
│  │  fs, dialog, shell, tray, updater          ││
│  │  permissions (not allowlist)               ││
│  └────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
```

---

## Task 1: Tauri v2 Project Setup

### 1.1 Initialize Tauri

```bash
cd frontend
npm install @tauri-apps/api@^2
npm install -D @tauri-apps/cli@^2
npx tauri init
```

### 1.2 Configure `tauri.conf.json`

```json
{
  "productName": "Cortex",
  "version": "1.0.0",
  "identifier": "com.cortex.app",
  "build": {
    "beforeDevCommand": "npm run dev",
    "devUrl": "http://localhost:3000",
    "beforeBuildCommand": "npm run build",
    "frontendDist": "../dist"
  },
  "app": {
    "windows": [
      {
        "title": "Cortex",
        "width": 1200,
        "height": 800,
        "resizable": true,
        "fullscreen": false
      }
    ],
    "security": {
      "csp": "default-src 'self'; script-src 'self'"
    }
  },
  "plugins": {
    "shell": {
      "sidecar": true,
      "scope": [
        { "name": "cortex-backend", "sidecar": true, "args": true }
      ]
    },
    "fs": {
      "scope": {
        "allow": ["$APPDATA/**", "$DOWNLOAD/**"],
        "deny": ["$APPDATA/secrets/**"]
      }
    },
    "dialog": {
      "all": true
    },
    "updater": {
      "pubkey": "dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHJlcXVpcmVk",
      "endpoints": [
        "https://releases.cortex.app/{{target}}/{{arch}}/{{current_version}}"
      ]
    }
  }
}
```

### 1.3 Configure Permissions

**Create:** `frontend/src-tauri/capabilities/default.json`

```json
{
  "$schema": "https://raw.githubusercontent.com/tauri-apps/tauri/dev/crates/tauri-utils/schema.json",
  "identifier": "default",
  "description": "Default capabilities for Cortex",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "shell:allow-execute",
    "shell:allow-spawn",
    "shell:allow-stdin-write",
    "fs:default",
    "fs:allow-read",
    "fs:allow-write",
    "dialog:default",
    "dialog:allow-open",
    "dialog:allow-save",
    "dialog:allow-message",
    "tray:default"
  ]
}
```

---

## Task 2: Backend Sidecar

### 2.1 Create Sidecar Entry Point

**Create:** `backend/sidecar.py`

```python
import asyncio
import signal
import sys
from app.main import app
import uvicorn

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Handle shutdown signals
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
    
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")

async def shutdown():
    """Graceful shutdown."""
    # Cleanup resources
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### 2.2 Build Sidecar

**Create:** `backend/build-sidecar.sh`

```bash
#!/bin/bash
# Build Python sidecar as standalone executable
pip install pyinstaller
pyinstaller --onefile --name cortex-backend sidecar.py
```

### 2.3 Place Sidecar Binary

```bash
mkdir -p frontend/src-tauri/binaries
cp backend/dist/cortex-backend frontend/src-tauri/binaries/cortex-backend-x86_64-unknown-linux-gnu
```

---

## Task 3: Tauri Rust Plugins

### 3.1 Tray Plugin

**Create:** `frontend/src-tauri/src/tray.rs`

```rust
use tauri::{
    tray::{TrayIconBuilder, TrayIconEvent},
    Manager, Runtime,
};

pub fn create_tray<R: Runtime>(app: &tauri::AppHandle<R>) -> tauri::Result<()> {
    let _tray = TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .tooltip("Cortex - AI Assistant")
        .on_tray_icon_event(|tray_icon, event| {
            if let TrayIconEvent::Click { button, button_state, .. } = event {
                // Handle tray click
            }
        })
        .build(app)?;
    
    Ok(())
}
```

### 3.2 Window Management

**Create:** `frontend/src-tauri/src/window.rs`

```rust
use tauri::Manager;

#[tauri::command]
pub fn minimize_window(window: tauri::Window) {
    window.minimize().unwrap();
}

#[tauri::command]
pub fn maximize_window(window: tauri::Window) {
    if window.is_maximized().unwrap() {
        window.unmaximize().unwrap();
    } else {
        window.maximize().unwrap();
    }
}

#[tauri::command]
pub fn close_window(window: tauri::Window) {
    window.close().unwrap();
}
```

### 3.3 Main Tauri Setup

**Create:** `frontend/src-tauri/src/lib.rs`

```rust
mod tray;
mod window;

use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .invoke_handler(tauri::generate_handler![
            window::minimize_window,
            window::maximize_window,
            window::close_window,
        ])
        .setup(|app| {
            // Start sidecar
            let sidecar_command = app.shell().sidecar("cortex-backend").unwrap();
            let (mut _rx, _child) = sidecar_command.spawn().expect("Failed to spawn sidecar");
            
            // Create tray
            tray::create_tray(app.handle())?;
            
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

---

## Task 4: Frontend Tauri Adapter

### 4.1 Update Tauri Adapter

**Update:** `frontend/src/shared/services/folder-picker/tauri-adapter.ts`

```typescript
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";

export async function pickFolder(): Promise<string | null> {
  try {
    const selected = await open({
      directory: true,
      multiple: false,
      title: "Select Repository",
    });
    return selected as string | null;
  } catch {
    return null;
  }
}

export async function minimizeWindow() {
  await invoke("minimize_window");
}

export async function maximizeWindow() {
  await invoke("maximize_window");
}

export async function closeWindow() {
  await invoke("close_window");
}
```

### 4.2 Update API Client for Desktop

**Update:** `frontend/src/shared/auth/cortexApi.ts`

```typescript
const isDesktop = typeof window !== "undefined" && window.__TAURI__ !== undefined;

const API_BASE = isDesktop 
  ? "http://127.0.0.1:8001"  // Sidecar
  : process.env.NEXT_PUBLIC_API_BASE_URL || "";
```

### 4.3 Custom Window Controls

**Create:** `frontend/components/desktop/WindowControls.tsx`

```typescript
"use client";
import { minimizeWindow, maximizeWindow, closeWindow } from "@/shared/services/folder-picker/tauri-adapter";

export function WindowControls() {
  return (
    <div className="flex items-center gap-2" data-tauri-drag-region>
      <button onClick={minimizeWindow} className="w-3 h-3 rounded-full bg-yellow-500 hover:bg-yellow-400" />
      <button onClick={maximizeWindow} className="w-3 h-3 rounded-full bg-green-500 hover:bg-green-400" />
      <button onClick={closeWindow} className="w-3 h-3 rounded-full bg-red-500 hover:bg-red-400" />
    </div>
  );
}
```

---

## Task 5: Offline Capabilities

### 5.1 Local Storage

**Create:** `frontend/src/shared/services/offline/storage.ts`

```typescript
const DB_NAME = "cortex-offline";
const DB_VERSION = 1;

export async function initOfflineDB() {
  return new Promise<IDBDatabase>((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains("conversations")) {
        db.createObjectStore("conversations", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("cache")) {
        db.createObjectStore("cache", { keyPath: "key" });
      }
    };
  });
}

export async function saveOfflineConversations(conversations: any[]) {
  const db = await initOfflineDB();
  const tx = db.transaction("conversations", "readwrite");
  const store = tx.objectStore("conversations");
  for (const conv of conversations) {
    store.put(conv);
  }
}

export async function getOfflineConversations() {
  const db = await initOfflineDB();
  const tx = db.transaction("conversations", "readonly");
  const store = tx.objectStore("conversations");
  return new Promise<any[]>((resolve) => {
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result);
  });
}
```

### 5.2 Service Worker

**Create:** `frontend/public/sw.js`

```javascript
const CACHE_NAME = "cortex-v1";
const STATIC_ASSETS = ["/", "/memory", "/search", "/settings"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.url.includes("/api/")) {
    // Network first for API calls
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
  } else {
    // Cache first for static assets
    event.respondWith(
      caches.match(event.request).then((response) => response || fetch(event.request))
    );
  }
});
```

---

## Task 6: File System Integration

### 6.1 File Watcher with Rust

**Update:** `crates/file-watcher/src/main.rs`

```rust
use notify::{Watcher, RecursiveMode, Result};
use std::sync::mpsc::channel;

fn main() -> Result<()> {
    let (tx, rx) = channel();
    
    let mut watcher = notify::recommended_watcher(tx)?;
    watcher.watch(std::path::Path::new("."), RecursiveMode::Recursive)?;
    
    for res in rx {
        match res {
            Ok(event) => println!("File event: {:?}", event),
            Err(e) => eprintln!("Watch error: {}", e),
        }
    }
    
    Ok(())
}
```

### 6.2 File Picker Integration

**Update:** `frontend/src/shared/services/folder-picker/tauri-adapter.ts`

Add file system operations:

```typescript
import { readTextFile, writeTextFile, readDir } from "@tauri-apps/plugin-fs";

export async function readFile(path: string): Promise<string> {
  return await readTextFile(path);
}

export async function writeFile(path: string, content: string): Promise<void> {
  await writeTextFile(path, content);
}

export async function listFiles(path: string): Promise<string[]> {
  const entries = await readDir(path);
  return entries.map(e => e.name || "").filter(Boolean);
}
```

---

## Task 7: Auto-Updates

### 7.1 Update Checker

**Create:** `frontend/src/shared/services/updater.ts`

```typescript
import { check } from "@tauri-apps/plugin-updater";
import { relaunch } from "@tauri-apps/plugin-process";

export async function checkForUpdates() {
  try {
    const update = await check();
    if (update) {
      const yes = window.confirm(`Update available: ${update.version}. Install?`);
      if (yes) {
        await update.downloadAndInstall();
        await relaunch();
      }
    }
  } catch (error) {
    console.error("Update check failed:", error);
  }
}
```

---

## Verification Checklist

```bash
# Tauri setup
cd frontend && npx tauri info

# Build
cd frontend && npx tauri build

# Test sidecar
cd backend && python sidecar.py

# Test frontend
cd frontend && npm run build

# Rust
cd crates && cargo build
```

---

## Exit Criteria

- [ ] Tauri v2 project initialized with correct plugins
- [ ] Backend runs as sidecar process
- [ ] Custom window controls (minimize, maximize, close)
- [ ] System tray icon with menu
- [ ] File picker uses native dialog
- [ ] Offline storage works
- [ ] Service worker caches static assets
- [ ] File watcher binary compiles
- [ ] Auto-updater configured
- [ ] Desktop app builds successfully
- [ ] No hardcoded localhost URLs in production
