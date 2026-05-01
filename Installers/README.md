# PocketMedic Installer Cache

Place optional offline installer `.exe` files here.

PocketMedic 3.0.1 searches these locations before offering winget fallback:

- `Installers/` beside the app
- `OneDrive/PocketMedic/Installers/`
- `Installers/` on connected USB drives

Installers are never run automatically. The terminal installer requires typed
manual confirmation, and dry-run mode is available for command preview.
