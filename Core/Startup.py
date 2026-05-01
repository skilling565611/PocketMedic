"""Startup program manager for PocketMedic.

Lists startup entries. On Windows this queries Run registry keys; on macOS and
Linux it checks common per-user startup folders.
"""

import os
import platform
import subprocess
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

    def build_delay_plan(self, delay_seconds: int = 30) -> List[Dict[str, object]]:
        """Return a safe startup-delay plan for detected startup entries."""
        return [
            {
                "name": entry["name"],
                "path": entry["path"],
                "delay_seconds": delay_seconds,
                "status": "planned",
            }
            for entry in self.list_entries()
        ]

    def create_delayed_task(
        self,
        name: str,
        command: str,
        delay_seconds: int = 30,
        dry_run: bool = True,
    ) -> Dict[str, object]:
        """Create or preview a delayed Windows startup scheduled task."""
        task_name = f"PocketMedic_Delayed_{name}"
        schtasks_command = [
            "schtasks",
            "/Create",
            "/F",
            "/SC",
            "ONLOGON",
            "/TN",
            task_name,
            "/TR",
            f'powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds {delay_seconds}; {command}"',
        ]
        if platform.system() != "Windows":
            return {
                "success": False,
                "dry_run": dry_run,
                "command": " ".join(schtasks_command),
                "message": "Startup delay tasks are Windows-only.",
            }
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "command": " ".join(schtasks_command),
                "message": "Delayed startup task command prepared.",
            }

        try:
            result = subprocess.run(schtasks_command, capture_output=True, text=True, timeout=20)
            success = result.returncode == 0
            return {
                "success": success,
                "dry_run": False,
                "command": " ".join(schtasks_command),
                "message": result.stdout.strip() if success else result.stderr.strip(),
            }
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            return {
                "success": False,
                "dry_run": False,
                "command": " ".join(schtasks_command),
                "message": str(exc),
            }

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
