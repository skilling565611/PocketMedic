"""System scanner module for PocketMedic."""

import ctypes
import json
import os
import platform
import shutil
from datetime import datetime
from typing import Any, Dict, Optional

from Core.Paths import app_path, resource_path


CONFIG_DIR = resource_path("Config")
LOG_DIR = app_path("Logs")
DEFAULT_LOW_STORAGE_FREE_GB = 20
DEFAULT_LOW_STORAGE_FREE_PERCENT = 10


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
            "scan": self.scan_metadata(),
            "profile": self.detect_machine_profile(),
            "os": self.scan_os(),
            "ram": self.scan_ram(),
            "disk": self.scan_disk(),
            "battery": self.scan_battery(),
            "temperature": self.scan_temperature(),
        }
        report["scan_report"] = {"saved_to": self.save_report(report)}
        self._log("Full system scan complete.")
        return report

    def scan_metadata(self) -> Dict[str, str]:
        """Return metadata for this scan run."""
        return {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "machine_name": platform.node(),
        }

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

    def scan_ram(self) -> Dict[str, Any]:
        """Return RAM usage details."""
        try:
            import psutil  # type: ignore

            memory = psutil.virtual_memory()
            return {
                "total_gb": self._bytes_to_gb(memory.total),
                "available_gb": self._bytes_to_gb(memory.available),
                "used_gb": self._bytes_to_gb(memory.used),
                "percent_used": memory.percent,
                "source": "psutil",
            }
        except ImportError:
            if platform.system() == "Windows":
                return self._scan_windows_ram()

        return {"status": "unavailable", "note": "Install psutil for RAM details."}

    def scan_disk(self) -> Dict[str, Any]:
        """Return disk usage for the filesystem containing this script."""
        root = os.path.abspath(os.sep)
        total, used, free = shutil.disk_usage(root)
        free_percent = round((free / total) * 100, 2) if total else 0
        warning = self._get_storage_warning(total, free, free_percent)
        return {
            "root": root,
            "total_gb": self._bytes_to_gb(total),
            "used_gb": self._bytes_to_gb(used),
            "free_gb": self._bytes_to_gb(free),
            "free_percent": free_percent,
            "low_storage_warning": warning,
        }

    def scan_battery(self) -> Dict[str, Any]:
        """Return battery status when available."""
        try:
            import psutil  # type: ignore

            battery = psutil.sensors_battery()
            if battery is None:
                return {"present": False, "status": "not_detected"}

            return {
                "present": True,
                "percent": battery.percent,
                "plugged_in": battery.power_plugged,
                "seconds_left": battery.secsleft,
                "source": "psutil",
            }
        except ImportError:
            if platform.system() == "Windows":
                return self._scan_windows_battery()

        return {"present": None, "status": "unavailable", "note": "Install psutil for battery details."}

    def scan_temperature(self) -> Dict[str, Any]:
        """Return a reserved temperature scan block for future hardware sensors."""
        return {
            "status": "placeholder",
            "note": "Temperature sensor support is reserved for a future scanner update.",
        }

    def detect_machine_profile(self) -> Dict[str, Any]:
        """Detect the active and likely matching machine profile."""
        settings = self._load_json(os.path.join(CONFIG_DIR, "Global.Settings.json"))
        active_profile = settings.get("active_profile")
        machine_name = platform.node()
        profiles = self._load_profiles()

        detected_profile = None
        for profile in profiles.values():
            profile_name = profile.get("profile_name", "")
            target = profile.get("hardware", {}).get("target", "")
            if self._matches_machine(machine_name, profile_name, target):
                detected_profile = profile_name
                break

        selected_profile = detected_profile or active_profile
        selected_data = profiles.get(selected_profile, {})
        return {
            "machine_name": machine_name,
            "active_profile": active_profile,
            "detected_profile": detected_profile,
            "selected_profile": selected_profile,
            "description": selected_data.get("description"),
            "hardware": selected_data.get("hardware", {}),
            "match_source": "machine_name" if detected_profile else "active_settings",
        }

    def save_report(self, report: Dict[str, Any]) -> str:
        """Save a scan report JSON file to Logs and return its path."""
        os.makedirs(LOG_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        machine_name = self._safe_filename(platform.node() or "machine")
        report_path = os.path.join(LOG_DIR, f"scan_{machine_name}_{timestamp}.json")

        with open(report_path, "w", encoding="utf-8") as file_handle:
            json.dump(report, file_handle, indent=4)

        self._log(f"Scan report saved: {report_path}")
        return report_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _bytes_to_gb(value: int) -> float:
        return round(value / 1024**3, 2)

    def _get_storage_warning(self, total: int, free: int, free_percent: float) -> Dict[str, Any]:
        settings = self._load_json(os.path.join(CONFIG_DIR, "Global.Settings.json"))
        min_free_gb = settings.get("low_storage_warning_free_gb", DEFAULT_LOW_STORAGE_FREE_GB)
        min_free_percent = settings.get(
            "low_storage_warning_free_percent",
            DEFAULT_LOW_STORAGE_FREE_PERCENT,
        )
        free_gb = self._bytes_to_gb(free)
        triggered = free_gb <= min_free_gb or free_percent <= min_free_percent
        return {
            "triggered": triggered,
            "free_gb_threshold": min_free_gb,
            "free_percent_threshold": min_free_percent,
            "message": self._storage_warning_message(total, free_gb, free_percent, triggered),
        }

    @staticmethod
    def _storage_warning_message(
        total: int,
        free_gb: float,
        free_percent: float,
        triggered: bool,
    ) -> str:
        if total == 0:
            return "Disk capacity could not be measured."
        if triggered:
            return f"Low storage warning: {free_gb} GB free ({free_percent}%)."
        return f"Storage OK: {free_gb} GB free ({free_percent}%)."

    def _load_profiles(self) -> Dict[str, Dict[str, Any]]:
        profiles: Dict[str, Dict[str, Any]] = {}
        if not os.path.isdir(CONFIG_DIR):
            return profiles

        for filename in os.listdir(CONFIG_DIR):
            if not filename.endswith(".Profile.json"):
                continue

            profile = self._load_json(os.path.join(CONFIG_DIR, filename))
            profile_name = profile.get("profile_name")
            if profile_name:
                profiles[profile_name] = profile
        return profiles

    @staticmethod
    def _load_json(path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as file_handle:
                return json.load(file_handle)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _matches_machine(machine_name: str, profile_name: str, target: str) -> bool:
        normalized_machine = machine_name.casefold()
        return any(
            value and value.casefold() in normalized_machine
            for value in (profile_name, target)
        )

    @staticmethod
    def _safe_filename(value: str) -> str:
        return "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in value)

    @staticmethod
    def _scan_windows_ram() -> Dict[str, Any]:
        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.dwLength = ctypes.sizeof(MemoryStatus)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return {"status": "unavailable", "note": "Windows RAM API call failed."}

        used = status.ullTotalPhys - status.ullAvailPhys
        return {
            "total_gb": Scanner._bytes_to_gb(status.ullTotalPhys),
            "available_gb": Scanner._bytes_to_gb(status.ullAvailPhys),
            "used_gb": Scanner._bytes_to_gb(used),
            "percent_used": status.dwMemoryLoad,
            "source": "windows_api",
        }

    @staticmethod
    def _scan_windows_battery() -> Dict[str, Any]:
        class SystemPowerStatus(ctypes.Structure):
            _fields_ = [
                ("ACLineStatus", ctypes.c_ubyte),
                ("BatteryFlag", ctypes.c_ubyte),
                ("BatteryLifePercent", ctypes.c_ubyte),
                ("SystemStatusFlag", ctypes.c_ubyte),
                ("BatteryLifeTime", ctypes.c_ulong),
                ("BatteryFullLifeTime", ctypes.c_ulong),
            ]

        status = SystemPowerStatus()
        if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
            return {"present": None, "status": "unavailable", "note": "Windows battery API call failed."}

        present = status.BatteryFlag != 128
        percent: Optional[int] = None if status.BatteryLifePercent == 255 else status.BatteryLifePercent
        return {
            "present": present,
            "percent": percent,
            "plugged_in": status.ACLineStatus == 1,
            "seconds_left": None if status.BatteryLifeTime == 0xFFFFFFFF else status.BatteryLifeTime,
            "source": "windows_api",
        }

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)
