"""Software installation engine for PocketMedic.

Provides a simple interface for installing, verifying, and uninstalling tools.
Package managers are invoked through subprocess when available.
"""

import shutil
import subprocess
from typing import List, Optional


class Installer:
    """Manage installation of tools and packages."""

    def __init__(self, logger=None):
        self._logger = logger

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_installed(self, tool_name: str) -> bool:
        """Return True if a tool is resolvable on PATH."""
        found = shutil.which(tool_name) is not None
        self._log(f"is_installed({tool_name!r}) -> {found}")
        return found

    def install(self, package_name: str, manager: str = "auto") -> bool:
        """Install a package with the specified or auto-detected manager."""
        resolved_manager = self._detect_manager() if manager == "auto" else manager
        if resolved_manager is None:
            self._log(f"No supported package manager found; cannot install {package_name!r}.")
            return False

        cmd = self._build_install_cmd(resolved_manager, package_name)
        self._log(f"Installing {package_name!r} via {resolved_manager}: {' '.join(cmd)}")
        return self._run(cmd)

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
