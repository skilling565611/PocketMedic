# PocketMedic External Data

This folder is user-editable and lives beside the app or EXE.

Files:

- `ExtraPackages.json` adds or overrides package definitions without rebuilding.
- `UserSettings.json` overrides global settings.
- `MachineOverrides.json` applies default or per-machine settings.

If any file is missing or invalid, PocketMedic logs a warning and continues
with bundled defaults.
