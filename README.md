# PocketMedic

> Portable PC Maintenance & Repair Toolkit - run from a USB drive, fix any machine.

## Version

Current version: **3.1.0**

PocketMedic is a lightweight, portable Python toolkit designed to diagnose,
maintain, rebuild, and repair Windows PCs while staying laptop-friendly for
systems like Arctic Prime.

## Feature List

| Feature | Module | Status |
|---------|--------|--------|
| Logging | `Core/Logger.py` | Stable |
| Enhanced System Scanner | `Core/Scanner.py` | Stable |
| Hardware Report | `Core/Hardware.py` | Stable |
| Network Diagnostics | `Core/Network.py` | Stable |
| Startup Manager | `Core/Startup.py` | Stable |
| Backup & Restore | `Core/Backup.py` | Stable |
| OneDrive Sync | `Core/OneDrive.py` | Stable |
| App Installer Framework | `Core/Installer.py` | v3.1.0 |
| Storage Helpers | `Core/Storage.py` | Stable |
| Rebuild Assistant | `Core/RebuildAssistant.py` | v2.1+ |
| Version / Build Info | `Core/BuildInfo.py` | v3.1.0 |
| Terminal UI | `GUI/TerminalUI.py` | Active |

## Quick Start

```bash
python PocketMedic.py
```

Optional dependency for detailed hardware data:

```bash
pip install psutil
```

## Installer Framework

Package definitions live in `Config/Package.Definitions.json`.

PocketMedic 3.1.0 detects installed apps from:

- Windows uninstall registry entries
- known executable commands
- known executable paths

Install readiness is EXE-only. PocketMedic searches approved installer folders:

- `Installers/` beside the app or EXE
- `OneDrive/PocketMedic/Installers/`
- `Installers/` on connected USB drives

Installers are never run automatically. Terminal option `[8] App Installer`
requires typed confirmation:

- `DRYRUN` previews installer commands
- `RUN` executes missing installers

Winget, Microsoft Store aliases, WindowsApps aliases, `py.exe`, and launcher
aliases are not installer sources.

## PyInstaller Build

Use the tracked spec file so bundled config files are included:

```bash
python -m PyInstaller --clean --noconfirm PocketMedic.spec
```

or:

```powershell
Scripts\Build-PocketMedic.ps1 -Clean
```

The spec bundles `Config/*.json`. At runtime, PocketMedic loads bundled config
from `sys._MEIPASS` in onefile EXEs and falls back to the project `Config/`
folder when running from source.

## Profiles

Device-specific behavior is controlled by JSON profiles in `Config/`.

| Profile | Target Device |
|---------|---------------|
| `ArcticPrime.Profile.json` | ArcticPrime PC |
| `ControlPrime.Profile.json` | ControlPrime PC |

The active profile is set in `Config/Global.Settings.json`.

## Safety Rules

- No uninstall workflow is exposed.
- No package is auto-installed.
- Installer execution requires explicit terminal confirmation.
- Installer readiness requires an actual `.exe` in an approved installer folder.
- Dry-run mode is available for install preview.

## License

See [LICENSE](LICENSE) for details.
