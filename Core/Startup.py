"""
Core/Startup.py — Startup program manager for PocketMedic.

Lists, enables, and disables startup entries.  On Windows this queries the
Run registry keys and the Startup folder; on other platforms it falls back
to available equivalents or graceful no-ops.
"""

import os
import platform
import subprocess
from typing import List, Dict


class Startup:
    """Manages OS startup entries."""

    def __init__(self, logger=None):
        self._logger = logger

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_entries(self) -> List[Dict[str, str]]:
        """Return a list of startup entry dicts with keys 'name' and 'path'."""
        system = platform.system()
        if system == "Windows":
            return self._list_windows()
        elif system == "Linux":
            return self._list_linux()
        elif system == "Darwin":
            return self._list_macos()
        self._log(f"Startup listing not supported on {system!r}.")
        return []

    # ------------------------------------------------------------------
    # Platform-specific implementations
    # ------------------------------------------------------------------

    def _list_windows(self) -> List[Dict[str, str]]:
        entries = []
        try:
            import winreg  # type: ignore
            for hive, key_path in [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            ]:
                try:
                    with winreg.OpenKey(hive, key_path) as key:
                        i = 0
                        while True:
                            try:
                                name, value, _ = winreg.EnumValue(key, i)
                                entries.append({"name": name, "path": value})
                                i += 1
                            except OSError:
                                break
                except OSError:
                    pass
        except ImportError:
            self._log("winreg not available.")
        return entries

    def _list_linux(self) -> List[Dict[str, str]]:
        autostart_dir = os.path.expanduser("~/.config/autostart")
        entries = []
        if os.path.isdir(autostart_dir):
            for fname in os.listdir(autostart_dir):
                if fname.endswith(".desktop"):
                    entries.append({"name": fname, "path": os.path.join(autostart_dir, fname)})
        return entries

    def _list_macos(self) -> List[Dict[str, str]]:
        launch_agents = os.path.expanduser("~/Library/LaunchAgents")
        entries = []
        if os.path.isdir(launch_agents):
            for fname in os.listdir(launch_agents):
                entries.append({"name": fname, "path": os.path.join(launch_agents, fname)})
        return entries

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)
