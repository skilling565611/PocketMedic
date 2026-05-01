# Changelog

All notable changes to PocketMedic will be documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- Initial project structure scaffolded under v0.1 Core Framework milestone
- Core modules for logging, scanning, hardware, network, startup, backup, OneDrive, installer, and storage workflows
- Terminal UI and Tkinter dashboard scaffolds
- Config profiles for ArcticPrime and ControlPrime
- Documentation and runtime folders

### Changed
- V3.1 installer behavior now prefers local, OneDrive, and USB installer sources before optional winget fallback
- Winget fallback is disabled by default through `use_winget_fallback: false`
- App Installer display now reports installed status, local installer availability, installer path, install source, and fallback state

---

## [3.0.1] - 2026-05-01

### Added
- App Installer Framework with package definitions in `Config/Package.Definitions.json`
- Local EXE installer discovery from app-local, OneDrive, and USB `Installers/` folders
- Dry-run installer mode and explicit terminal confirmation before execution
- Version/build info display and V3.1 prep metadata
- Installer cache structure prep with `Installers/README.md`

### Changed
- Updated application version to `3.0.1`
- Winget is now treated as an optional fallback after local installer search
- PyInstaller config loading supports bundled `sys._MEIPASS` resources

### Fixed
- Installer detection no longer treats config entries as installed packages
- Installed status now comes from Windows uninstall registry entries, known commands, or known paths
- Missing config files are logged as clear warnings instead of crashing terminal workflows

---

## [0.1.0] - 2026-05-01

- Initial repository creation
- Added `README.md`, `LICENSE`, `.gitignore`
