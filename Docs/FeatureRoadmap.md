# Feature Roadmap

## Version Milestones

| Version | Focus                  | Status      |
|---------|------------------------|-------------|
| v0.1    | Core Framework         | ✅ Complete  |
| v0.2    | Logging + Config       | ✅ Complete  |
| v0.3    | System Scanner         | 🔄 In Progress |
| v0.4    | Installer Engine       | 🔄 In Progress |
| v0.5    | Startup Manager        | 🔄 In Progress |
| v0.6    | Network Diagnostics    | 🔄 In Progress |
| v0.7    | Backup & Restore       | 🔄 In Progress |
| v0.8    | OneDrive Integration   | ⬜ Planned   |
| v0.9    | GUI Dashboard          | ⬜ Planned   |
| v1.0    | Stable Release         | ⬜ Planned   |

---

## Planned Features

### Core
- [x] Logger (file + console output, dated log files)
- [x] Global settings and per-device profiles (JSON)
- [x] System scanner (OS, disk)
- [x] Hardware report (CPU, RAM, disk, platform)
- [x] Network diagnostics (ping, DNS, connectivity check)
- [x] Startup manager (list startup entries)
- [x] Backup engine (ZIP archives, restore)
- [x] OneDrive detection and file sync
- [x] Installer (winget / choco / apt / brew wrapper)
- [x] Storage helpers (JSON read/write, filesystem utilities)

### GUI
- [x] Terminal UI (menu-driven CLI)
- [x] Tkinter Dashboard (buttons + output area)
- [ ] Themes (dark / light)
- [ ] Status bar with live CPU / RAM
- [ ] Log viewer tab

### PortableTools
- [ ] Auto-detect tools in `PortableTools/`
- [ ] Launch tools from the UI

### Scripts
- [ ] Script runner (execute `.py` / `.bat` / `.sh` from `Scripts/`)
- [ ] Built-in clear-temp script
- [ ] Built-in DNS flush script

### Cloud / Sync
- [ ] OneDrive backup destination
- [ ] Scheduled auto-backup

---

## Hardware Targets

- **ArcticPrime** — 8 GB RAM, SSD, deep scan profile
- **ControlPrime** — 16 GB RAM, NVMe, standard scan profile
