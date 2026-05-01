"""Software installation engine for PocketMedic."""

import json
import os
import shutil
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DEFINITIONS_PATH = os.path.join(PROJECT_ROOT, "Config", "Package.Definitions.json")


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
            self._log(f"Failed to load package definitions {definitions_path!r}: {exc}")
            return []

        packages = data.get("packages", [])
        if not isinstance(packages, list):
            self._log(f"Package definitions must be a list: {definitions_path}")
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
        installed = any(match["path"] for match in command_matches) or any(
            match["exists"] for match in path_matches
        )
        self._log(f"detect_package({definition.get('key', 'unknown')!r}) -> {installed}")
        return {
            "installed": installed,
            "command_matches": command_matches,
            "path_matches": path_matches,
        }

    def build_install_plan(
        self,
        definitions: Optional[List[Dict[str, Any]]] = None,
        include_disabled: bool = False,
    ) -> Dict[str, Any]:
        """Build a package install plan without installing anything."""
        manager = self._detect_manager()
        packages = []
        for definition in definitions or self.load_package_definitions():
            if not include_disabled and not definition.get("enabled", True):
                continue

            detection = self.detect_package(definition)
            packages.append(
                {
                    "key": definition.get("key"),
                    "display_name": definition.get("display_name", definition.get("key")),
                    "category": definition.get("category"),
                    "enabled": definition.get("enabled", True),
                    "winget_id": definition.get("winget_id"),
                    "installed": detection["installed"],
                    "install_command": self.preview_definition_install(definition, manager),
                    "detection": detection,
                }
            )

        missing = [package for package in packages if not package["installed"]]
        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "manager_status": self.manager_status(),
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

        manager = plan.get("manager_status", {}).get("active_manager")
        if not manager:
            self._log("Install skipped: no package manager available.")
            return [
                {
                    "key": package.get("key"),
                    "status": "failed",
                    "message": "No package manager available.",
                }
                for package in plan.get("packages", [])
                if not package.get("installed")
            ]

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

            command = self._build_definition_install_cmd(manager, definition)
            success = self._run(command)
            results.append(
                {
                    "key": key,
                    "status": "installed" if success else "failed",
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

    @staticmethod
    def _resolve(path: str) -> str:
        if os.path.isabs(path):
            return path
        return os.path.join(PROJECT_ROOT, path)

    @staticmethod
    def _expand_path(path: str) -> str:
        return os.path.expandvars(os.path.expanduser(path))
