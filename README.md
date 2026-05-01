# PocketMedic

> Portable PC Maintenance & Repair Toolkit — run from a USB drive, fix any machine.

---

## Project Overview

PocketMedic is a lightweight, portable Python toolkit designed to diagnose,
maintain, and repair Windows PCs (with macOS/Linux support for most features).
It runs entirely from a USB drive — no installation required — and is built
feature-by-feature with a clean, maintainable structure.

---

## Feature List

| Feature              | Module                  | Status         |
|----------------------|-------------------------|----------------|
| Logging              | `Core/Logger.py`        | ✅ v0.2        |
| System Scanner       | `Core/Scanner.py`       | ✅ v0.3        |
| Hardware Report      | `Core/Hardware.py`      | ✅ v0.3        |
| Network Diagnostics  | `Core/Network.py`       | ✅ v0.6        |
| Startup Manager      | `Core/Startup.py`       | ✅ v0.5        |
| Backup & Restore     | `Core/Backup.py`        | ✅ v0.7        |
| OneDrive Sync        | `Core/OneDrive.py`      | 🔄 v0.8        |
| Installer Engine     | `Core/Installer.py`     | ✅ v0.4        |
| Storage Helpers      | `Core/Storage.py`       | ✅ v0.2        |
| Terminal UI          | `GUI/TerminalUI.py`     | ✅ v0.1        |
| GUI Dashboard        | `GUI/Dashboard.py`      | 🔄 v0.9        |

---

## Installation

See [Docs/SetupGuide.md](Docs/SetupGuide.md) for full setup instructions.

**Quick start:**

```bash
git clone https://github.com/skilling565611/PocketMedic.git
cd PocketMedic
python PocketMedic.py
```

Optional dependency for detailed CPU/RAM info:

```bash
pip install psutil
```

---

## Usage

Run the interactive terminal interface:

```bash
python PocketMedic.py
```

This launches the menu-driven CLI where you can:

- Run a full system scan
- View a hardware report
- Check network connectivity and DNS
- List startup entries
- Browse backup archives

---

## Profiles

Device-specific behaviour is controlled by JSON profiles in `Config/`:

| Profile                        | Target Device   |
|-------------------------------|-----------------|
| `ArcticPrime.Profile.json`    | ArcticPrime PC  |
| `ControlPrime.Profile.json`   | ControlPrime PC |

The active profile is set in `Config/Global.Settings.json`.

---

## Roadmap

| Version | Milestone             |
|---------|-----------------------|
| v0.1    | Core Framework        |
| v0.2    | Logging + Config      |
| v0.3    | System Scanner        |
| v0.4    | Installer Engine      |
| v0.5    | Startup Manager       |
| v0.6    | Network Diagnostics   |
| v0.7    | Backup & Restore      |
| v0.8    | OneDrive Integration  |
| v0.9    | GUI Dashboard         |
| v1.0    | Stable Release        |

See [Docs/FeatureRoadmap.md](Docs/FeatureRoadmap.md) for details.

---

## Known Limitations

- OneDrive integration is Windows-only
- Startup manager registry access requires elevated privileges on Windows
- GUI Dashboard requires Tkinter (included with most Python installs)
- `psutil` is optional but recommended for full hardware reporting

---

## License

See [LICENSE](LICENSE) for details.