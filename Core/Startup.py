"""Startup program manager for PocketMedic.

Lists startup entries. On Windows this queries Run registry keys; on macOS and
Linux it checks common per-user startup folders.
"""

import os
import platform
from typing import Dict, List


class Startup:
    """List operating system startup entries."""

    def __init__(self, logger=None):
        self._logger = logger

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_entries(self) -> List[Dict[str, str]]:
        """Return startup entries with name and path keys."""
        system = platform.system()
        if system == "Windows":
            return self._list_windows()
        if system == "Linux":
            return self._list_linux()
        if system == "Darwin":
            return self._list_macos()

        self._log(f"Startup listing not supported on {system!r}.")
        return []

    # ------------------------------------------------------------------
    # Platform-specific implementations
    # ------------------------------------------------------------------

    def _list_windows(self) -> List[Dict[str, str]]:
        entries: List[Dict[str, str]] = []
        try:
            import winreg  # type: ignore
        except ImportError:
            self._log("winreg not available.")
            return entries

        registry_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        ]
        for hive, key_path in registry_paths:
            try:
                with winreg.OpenKey(hive, key_path) as key:
                    index = 0
                    while True:
                        try:
                            name, value, _value_type = winreg.EnumValue(key, index)
                        except OSError:
                            break
                        entries.append({"name": name, "path": value})
                        index += 1
            except OSError:
                continue

        return entries

    def _list_linux(self) -> List[Dict[str, str]]:
        autostart_dir = os.path.expanduser("~/.config/autostart")
        entries: List[Dict[str, str]] = []
        if os.path.isdir(autostart_dir):
            for filename in os.listdir(autostart_dir):
                if filename.endswith(".desktop"):
                    entries.append(
                        {"name": filename, "path": os.path.join(autostart_dir, filename)}
                    )
        return entries

    def _list_macos(self) -> List[Dict[str, str]]:
        launch_agents = os.path.expanduser("~/Library/LaunchAgents")
        entries: List[Dict[str, str]] = []
        if os.path.isdir(launch_agents):
            for filename in os.listdir(launch_agents):
                entries.append(
                    {"name": filename, "path": os.path.join(launch_agents, filename)}
                )
        return entries

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)
