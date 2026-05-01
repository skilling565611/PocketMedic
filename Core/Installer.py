"""Software installation engine for PocketMedic."""

import json
import os
import shutil
import subprocess
import ctypes
from datetime import datetime
from typing import Any, Dict, List, Optional

from Core.Paths import app_path, find_resource


DEFAULT_DEFINITIONS_PATH = find_resource(os.path.join("Config", "Package.Definitions.json"))


class Installer:
    """Manage package definitions, detection, and confirmed installs."""

    def __init__(self, logger=None):
        self._logger = logger

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_package_definitions(self, path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load package definitions from JSON config."""
        definitions_path = self._resolve(path or DEFAULT_DEFINITIONS_PATH)
        try:
            with open(definitions_path, "r", encoding="utf-8") as file_handle:
                data = json.load(file_handle)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            self._warning(f"Warning: failed to load package definitions {definitions_path!r}: {exc}")
            return []

        packages = data.get("packages", [])
        if not isinstance(packages, list):
            self._warning(f"Warning: package definitions must be a list: {definitions_path}")
            return []

        self._log(f"Loaded {len(packages)} package definitions from {definitions_path}")
        return packages

    def manager_status(self) -> Dict[str, object]:
        """Return availability details for supported package managers."""
        managers = {
            manager: shutil.which(manager)
            for manager in ("winget", "choco", "apt", "brew")
        }
        active = self._detect_manager()
        return {
            "active_manager": active,
            "available_managers": managers,
            "ready": active is not None,
        }

    def is_installed(self, tool_name: str) -> bool:
        """Return True if a tool is resolvable on PATH."""
        found = shutil.which(tool_name) is not None
        self._log(f"is_installed({tool_name!r}) -> {found}")
        return found

    def detect_package(self, definition: Dict[str, Any]) -> Dict[str, Any]:
        """Detect whether a package definition appears installed."""
        detect = definition.get("detect", {})
        commands = detect.get("commands", [])
        paths = detect.get("paths", [])
        registry_names = detect.get("registry_display_names", [])

        command_matches = [
            {"command": command, "path": shutil.which(command)}
            for command in commands
        ]
        path_matches = [
            {
                "path": self._expand_path(path),
                "exists": os.path.exists(self._expand_path(path)),
            }
            for path in paths
        ]
        registry_matches = self._find_registry_matches(
            registry_names or [definition.get("display_name"), definition.get("key")]
        )
        installed = (
            bool(registry_matches)
            or any(match["path"] for match in command_matches)
            or any(match["exists"] for match in path_matches)
        )
        self._log(f"detect_package({definition.get('key', 'unknown')!r}) -> {installed}")
        return {
            "installed": installed,
            "source": self._detection_source(registry_matches, command_matches, path_matches),
            "registry_matches": registry_matches,
            "command_matches": command_matches,
            "path_matches": path_matches,
        }

    def build_install_plan(
        self,
        definitions: Optional[List[Dict[str, Any]]] = None,
        include_disabled: bool = False,
        use_winget_fallback: bool = False,
    ) -> Dict[str, Any]:
        """Build a package install plan without installing anything."""
        manager = self._detect_manager() if use_winget_fallback else None
        packages = []
        for definition in definitions or self.load_package_definitions():
            if not include_disabled and not definition.get("enabled", True):
                continue

            detection = self.detect_package(definition)
            local_installer = self.find_local_installer(definition)
            installer_status = self._installer_status(detection["installed"], local_installer)
            install_source = self._install_source(local_installer)
            packages.append(
                {
                    "key": definition.get("key"),
                    "display_name": definition.get("display_name", definition.get("key")),
                    "category": definition.get("category"),
                    "enabled": definition.get("enabled", True),
                    "winget_id": definition.get("winget_id"),
                    "installed": detection["installed"],
                    "installer_status": installer_status,
                    "local_installer_found": local_installer is not None,
                    "local_installer": local_installer,
                    "installer_path": local_installer["path"] if local_installer else None,
                    "install_source": install_source,
                    "winget_fallback_enabled": use_winget_fallback,
                    "winget_fallback_command": (
                        self.preview_definition_install(definition, manager)
                        if use_winget_fallback
                        else ""
                    ),
                    "detection": detection,
                }
            )

        missing = [package for package in packages if not package["installed"]]
        manager_status = self.manager_status()
        if not use_winget_fallback:
            manager_status = {
                **manager_status,
                "active_manager": None,
                "ready": False,
                "fallback_available": bool(
                    manager_status["available_managers"].get("winget")
                ),
            }
        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "manager_status": manager_status,
            "use_winget_fallback": use_winget_fallback,
            "manual_confirmation_required": True,
            "packages": packages,
            "missing_count": len(missing),
        }

    def preview_definition_install(
        self,
        definition: Dict[str, Any],
        manager: Optional[str] = None,
    ) -> str:
        """Return the definition install command without running it."""
        resolved_manager = manager or self._detect_manager()
        if resolved_manager is None:
            return ""
        return " ".join(self._build_definition_install_cmd(resolved_manager, definition))

    def find_local_installer(self, definition: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Find a local installer EXE for a package definition."""
        patterns = definition.get("local_installers", [])
        if not patterns:
            key = definition.get("key", "")
            patterns = [f"{key}.exe", f"{key}-*.exe", f"*{key}*.exe"]

        for location in self.get_installer_search_paths():
            directory = location["path"]
            if not os.path.isdir(directory):
                continue
            for pattern in patterns:
                match = self._first_match(directory, pattern)
                if match:
                    return {
                        "path": match,
                        "source": location["source"],
                        "directory": directory,
                    }
        return None

    def get_installer_search_paths(self) -> List[Dict[str, str]]:
        """Return local EXE installer search paths."""
        paths = [{"source": "Local", "path": app_path("Installers")}]

        onedrive = os.environ.get("OneDrive") or os.environ.get("OneDriveConsumer")
        if not onedrive:
            candidate = os.path.expanduser("~/OneDrive")
            if os.path.isdir(candidate):
                onedrive = candidate
        if onedrive:
            paths.append(
                {
                    "source": "OneDrive",
                    "path": os.path.join(onedrive, "PocketMedic", "Installers"),
                }
            )

        paths.extend(
            {"source": "USB", "path": os.path.join(drive, "Installers")}
            for drive in self._removable_drives()
        )
        return self._dedupe_locations(paths)

    def verify_packages(self, package_names: List[str]) -> List[Dict[str, object]]:
        """Return install status and install previews for requested packages."""
        manager = self._detect_manager()
        return [
            {
                "package": package,
                "installed": self.is_installed(package),
                "manager": manager,
                "install_command": self.preview_install(package, manager),
            }
            for package in package_names
        ]

    def preview_install(self, package_name: str, manager: Optional[str] = None) -> str:
        """Return the install command that would be used without running it."""
        resolved_manager = manager or self._detect_manager()
        if resolved_manager is None:
            return ""
        return " ".join(self._build_install_cmd(resolved_manager, package_name))

    def install(self, package_name: str, manager: str = "auto") -> bool:
        """Install a package with the specified or auto-detected manager."""
        resolved_manager = self._detect_manager() if manager == "auto" else manager
        if resolved_manager is None:
            self._log(f"No supported package manager found; cannot install {package_name!r}.")
            return False

        cmd = self._build_install_cmd(resolved_manager, package_name)
        self._log(f"Installing {package_name!r} via {resolved_manager}: {' '.join(cmd)}")
        return self._run(cmd)

    def install_many(self, package_names: List[str], manager: str = "auto") -> Dict[str, bool]:
        """Install multiple packages and return a package-to-success map."""
        return {
            package_name: self.install(package_name, manager=manager)
            for package_name in package_names
        }

    def install_missing_from_plan(
        self,
        plan: Dict[str, Any],
        confirmed: bool = False,
        dry_run: bool = True,
    ) -> List[Dict[str, Any]]:
        """Install missing packages from a plan after explicit confirmation."""
        if not confirmed:
            self._log("Install skipped: manual confirmation was not provided.")
            return [
                {
                    "key": package.get("key"),
                    "status": "skipped",
                    "message": "Manual confirmation was not provided.",
                }
                for package in plan.get("packages", [])
                if not package.get("installed")
            ]

        use_winget_fallback = plan.get("use_winget_fallback", False)
        manager = (
            plan.get("manager_status", {}).get("active_manager")
            if use_winget_fallback
            else None
        )
        results = []
        definitions = {
            definition.get("key"): definition
            for definition in self.load_package_definitions()
        }
        for package in plan.get("packages", []):
            if package.get("installed"):
                continue

            key = package.get("key")
            definition = definitions.get(key)
            if not definition:
                results.append(
                    {"key": key, "status": "failed", "message": "Definition not found."}
                )
                continue

            local_installer = package.get("local_installer")
            if local_installer:
                command = [local_installer["path"]]
                install_source = local_installer.get("source", "Local")
            elif use_winget_fallback and manager:
                command = self._build_definition_install_cmd(manager, definition)
                install_source = "winget"
            else:
                results.append(
                    {
                        "key": key,
                        "status": "missing",
                        "message": "No local installer found. Winget fallback is disabled.",
                    }
                )
                continue

            if dry_run:
                self._log(f"Dry-run install prepared for {key!r}: {' '.join(command)}")
                results.append(
                    {
                        "key": key,
                        "status": "dry_run",
                        "source": install_source,
                        "command": " ".join(command),
                    }
                )
                continue

            success = self._run(command)
            results.append(
                {
                    "key": key,
                    "status": "installed" if success else "failed",
                    "source": install_source,
                    "command": " ".join(command),
                }
            )

        return results

    def uninstall(self, package_name: str, manager: str = "auto") -> bool:
        """Uninstall a package with the specified or auto-detected manager."""
        resolved_manager = self._detect_manager() if manager == "auto" else manager
        if resolved_manager is None:
            self._log(
                f"No supported package manager found; cannot uninstall {package_name!r}."
            )
            return False

        cmd = self._build_uninstall_cmd(resolved_manager, package_name)
        self._log(f"Uninstalling {package_name!r} via {resolved_manager}: {' '.join(cmd)}")
        return self._run(cmd)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_manager(self) -> Optional[str]:
        for manager in ("winget", "choco", "apt", "brew"):
            if shutil.which(manager):
                return manager
        return None

    def _build_install_cmd(self, manager: str, package: str) -> List[str]:
        mapping = {
            "winget": ["winget", "install", "--silent", package],
            "choco": ["choco", "install", "-y", package],
            "apt": ["apt-get", "install", "-y", package],
            "brew": ["brew", "install", package],
        }
        return mapping.get(manager, [manager, "install", package])

    def _build_definition_install_cmd(
        self,
        manager: str,
        definition: Dict[str, Any],
    ) -> List[str]:
        if manager == "winget":
            winget_id = definition.get("winget_id") or definition.get("key")
            return [
                "winget",
                "install",
                "--id",
                winget_id,
                "--silent",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ]
        return self._build_install_cmd(manager, definition.get("key", ""))

    def _build_uninstall_cmd(self, manager: str, package: str) -> List[str]:
        mapping = {
            "winget": ["winget", "uninstall", "--silent", package],
            "choco": ["choco", "uninstall", "-y", package],
            "apt": ["apt-get", "remove", "-y", package],
            "brew": ["brew", "uninstall", package],
        }
        return mapping.get(manager, [manager, "uninstall", package])

    def _run(self, cmd: List[str]) -> bool:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                self._log("Command succeeded.")
                return True

            error = result.stderr.strip()
            self._log(f"Command failed (exit {result.returncode}): {error}")
            return False
        except FileNotFoundError as exc:
            self._log(f"Command not found: {exc}")
            return False

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)

    def _warning(self, message: str) -> None:
        if self._logger:
            self._logger.warning(message)

    @staticmethod
    def _resolve(path: str) -> str:
        return find_resource(path)

    @staticmethod
    def _expand_path(path: str) -> str:
        return os.path.expandvars(os.path.expanduser(path))

    @staticmethod
    def _installer_status(installed: bool, local_installer: Optional[Dict[str, str]]) -> str:
        if installed:
            return "Installed"
        if local_installer:
            return "Available"
        return "Missing"

    @staticmethod
    def _install_source(local_installer: Optional[Dict[str, str]]) -> str:
        if not local_installer:
            return "Missing"
        source = local_installer.get("source", "Local")
        if source in {"Local", "OneDrive", "USB"}:
            return source
        return "Local"

    @staticmethod
    def _detection_source(
        registry_matches: List[Dict[str, str]],
        command_matches: List[Dict[str, Optional[str]]],
        path_matches: List[Dict[str, object]],
    ) -> str:
        if registry_matches:
            return "registry"
        if any(match["path"] for match in command_matches):
            return "executable"
        if any(match["exists"] for match in path_matches):
            return "known_path"
        return "not_detected"

    def _find_registry_matches(self, names: List[Optional[str]]) -> List[Dict[str, str]]:
        if os.name != "nt":
            return []

        needles = [name.casefold() for name in names if name]
        if not needles:
            return []

        matches = []
        for entry in self._windows_uninstall_entries():
            display_name = entry.get("display_name", "")
            normalized = display_name.casefold()
            if any(needle in normalized for needle in needles):
                matches.append(entry)
        return matches

    @staticmethod
    def _windows_uninstall_entries() -> List[Dict[str, str]]:
        try:
            import winreg  # type: ignore
        except ImportError:
            return []

        hives = [
            winreg.HKEY_CURRENT_USER,
            winreg.HKEY_LOCAL_MACHINE,
        ]
        paths = [
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
            r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ]
        entries: List[Dict[str, str]] = []
        for hive in hives:
            for key_path in paths:
                try:
                    with winreg.OpenKey(hive, key_path) as root_key:
                        index = 0
                        while True:
                            try:
                                subkey_name = winreg.EnumKey(root_key, index)
                                index += 1
                            except OSError:
                                break

                            try:
                                with winreg.OpenKey(root_key, subkey_name) as app_key:
                                    display_name, _ = winreg.QueryValueEx(app_key, "DisplayName")
                            except OSError:
                                continue

                            entry = {"display_name": str(display_name), "registry_key": subkey_name}
                            try:
                                version, _ = winreg.QueryValueEx(app_key, "DisplayVersion")
                                entry["version"] = str(version)
                            except OSError:
                                pass
                            entries.append(entry)
                except OSError:
                    continue
        return entries

    @staticmethod
    def _first_match(directory: str, pattern: str) -> Optional[str]:
        import glob

        matches = sorted(glob.glob(os.path.join(directory, pattern)))
        for match in matches:
            if os.path.isfile(match) and match.lower().endswith(".exe"):
                return match
        return None

    @staticmethod
    def _removable_drives() -> List[str]:
        if os.name != "nt":
            return []

        DRIVE_REMOVABLE = 2
        drives = []
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for index in range(26):
            if not bitmask & (1 << index):
                continue
            root = f"{chr(65 + index)}:\\"
            if ctypes.windll.kernel32.GetDriveTypeW(root) == DRIVE_REMOVABLE:
                drives.append(root)
        return drives

    @staticmethod
    def _dedupe_locations(paths: List[Dict[str, str]]) -> List[Dict[str, str]]:
        seen = set()
        unique = []
        for location in paths:
            path = location["path"]
            normalized = os.path.normcase(os.path.normpath(path))
            if normalized in seen:
                continue
            seen.add(normalized)
            unique.append(
                {
                    "source": location["source"],
                    "path": os.path.normpath(path),
                }
            )
        return unique
