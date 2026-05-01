"""System scanner module for PocketMedic.

Gathers information about the host system. Results are returned as plain
Python dicts so they can be displayed in the UI or persisted to a log.
"""

import os
import platform
import shutil
from typing import Any, Dict


class Scanner:
    """Collect system health and configuration data."""

    def __init__(self, logger=None):
        self._logger = logger

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_full_scan(self) -> Dict[str, Any]:
        """Execute all sub-scans and return a combined report dict."""
        self._log("Starting full system scan...")
        report = {
            "os": self.scan_os(),
            "disk": self.scan_disk(),
        }
        self._log("Full system scan complete.")
        return report

    def scan_os(self) -> Dict[str, str]:
        """Return basic OS and platform information."""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }

    def scan_disk(self) -> Dict[str, Any]:
        """Return disk usage for the filesystem containing this script."""
        root = os.path.abspath(os.sep)
        total, used, free = shutil.disk_usage(root)
        return {
            "root": root,
            "total_gb": round(total / 1024**3, 2),
            "used_gb": round(used / 1024**3, 2),
            "free_gb": round(free / 1024**3, 2),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)
