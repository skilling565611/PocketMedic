"""Hardware information gathering for PocketMedic.

Collects CPU, RAM, and disk details from the host system using cross-platform
stdlib calls where possible, with optional psutil support for richer metrics.
"""

import os
import platform
import shutil
from typing import Any, Dict


class Hardware:
    """Gather hardware information from the host system."""

    def __init__(self, logger=None):
        self._logger = logger

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def full_report(self) -> Dict[str, Any]:
        """Return a combined hardware report dict."""
        report = {
            "cpu": self.get_cpu_info(),
            "disk": self.get_disk_info(),
            "platform": self.get_platform_info(),
        }
        try:
            import psutil  # type: ignore

            report["ram"] = self.get_ram_info(psutil)
        except ImportError:
            report["ram"] = {"note": "psutil not installed; RAM info unavailable"}
        return report

    def get_platform_info(self) -> Dict[str, str]:
        """Return operating system and machine details."""
        return {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }

    def get_cpu_info(self) -> Dict[str, Any]:
        """Return CPU details, using psutil when available."""
        info: Dict[str, Any] = {"processor": platform.processor()}
        try:
            import psutil  # type: ignore

            cpu_freq = psutil.cpu_freq()
            info["physical_cores"] = psutil.cpu_count(logical=False)
            info["logical_cores"] = psutil.cpu_count(logical=True)
            info["freq_mhz"] = getattr(cpu_freq, "current", None)
            info["usage_percent"] = psutil.cpu_percent(interval=0.5)
        except ImportError:
            info["note"] = "psutil not installed; detailed CPU info unavailable"
        return info

    def get_ram_info(self, psutil=None) -> Dict[str, Any]:
        """Return RAM usage details, using a provided or imported psutil module."""
        if psutil is None:
            try:
                import psutil  # type: ignore
            except ImportError:
                return {"note": "psutil not installed"}

        memory = psutil.virtual_memory()
        return {
            "total_gb": round(memory.total / 1024**3, 2),
            "available_gb": round(memory.available / 1024**3, 2),
            "used_gb": round(memory.used / 1024**3, 2),
            "percent_used": memory.percent,
        }

    def get_disk_info(self) -> Dict[str, Any]:
        """Return disk usage for the root filesystem."""
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
