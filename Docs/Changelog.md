# Changelog

All notable changes to PocketMedic will be documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- Initial project structure scaffolded under v0.1 Core Framework milestone
- `Core/Logger.py` — dated log files + console output
- `Core/Scanner.py` — OS and disk scan
- `Core/Hardware.py` — CPU, RAM, disk, platform report
- `Core/Network.py` — connectivity, DNS, and ping checks
- `Core/Startup.py` — list OS startup entries (Windows, Linux, macOS)
- `Core/Backup.py` — ZIP-based backup/restore engine
- `Core/OneDrive.py` — OneDrive detection and file copy helper
- `Core/Installer.py` — winget / choco / apt / brew install wrapper
- `Core/Storage.py` — JSON read/write and filesystem helpers
- `GUI/TerminalUI.py` — interactive menu-driven CLI
- `GUI/Dashboard.py` — Tkinter GUI dashboard
- `Config/Global.Settings.json` — global application settings
- `Config/ArcticPrime.Profile.json` — ArcticPrime hardware profile
- `Config/ControlPrime.Profile.json` — ControlPrime hardware profile
- `Docs/FeatureRoadmap.md`, `Docs/SetupGuide.md`, `Docs/Changelog.md`
- `PortableTools/`, `Scripts/`, `Logs/` directories with README files
- Updated `README.md` with project overview, feature list, and roadmap

---

## [0.1.0] — 2026-05-01

- Initial repository creation
- Added `README.md`, `LICENSE`, `.gitignore`
