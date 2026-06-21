# Phase 5: Desktop Preparation & Tauri Integration

Context: Cortex should eventually run as a native desktop app. The frontend already has a Tauri adapter for folder picking. Service abstractions need to be complete for desktop deployment.

**Goals:**
- All services work through abstractions (no direct filesystem calls in business logic)
- File watching works cross-platform
- Desktop app can be built with Tauri
- Offline mode with local models

**Key Deliverables:**
| # | Deliverable | Description | Status |
|---|-------------|-------------|--------|
| 1 | Folder Picker Abstraction | Browser + Tauri adapters | DONE |
| 2 | File Watcher Abstraction | Cross-platform file watching | DONE |
| 3 | Storage Abstraction | Filesystem operations through service layer | PARTIAL |
| 4 | Platform Detection | Detect browser vs Tauri vs CLI | TODO |
| 5 | Offline Mode | Work without internet using local models | TODO |
| 6 | System Tray Integration | Background operation with tray icon | TODO |
| 7 | Native Notifications | OS-level notifications | TODO |
| 8 | Auto-update | Desktop app auto-update mechanism | TODO |
| 9 | Tauri Build Config | Build scripts for all platforms | TODO |
| 10 | Service Abstraction Audit | Ensure no direct OS calls in business logic | TODO |
| 11 | Embedded PostgreSQL | Bundle PG with desktop app | TODO |
| 12 | Performance Profiling | Optimize for desktop resource constraints | TODO |

**Validation Checkpoints:**
- All services use abstractions (no os.path, open() in service layer)
- Tauri build succeeds for target platforms
- App runs offline with local models
- File watching works on Linux, macOS, Windows

**Dependencies:** Phase 4 (learning systems need stable foundation)

**Complexity:** L (large - platform-specific work)
