"""Version, build metadata, and V3.1 prep status."""

import ctypes
import os
import platform
from typing import Any, Dict, List

from Core.ConfigManager import ConfigManager
from Core.Paths import app_path


class BuildInfo:
    """Collect PocketMedic version/build details and prep status."""

    def __init__(self, logger=None):
        self._logger = logger
        self._config = ConfigManager(logger=logger)

    def report(self) -> Dict[str, Any]:
        """Return version, build, and V3.1 prep status."""
        settings = self._config.load_settings()
        metadata_path = settings.get("build_metadata_path", "Config/Build.Metadata.json")
        metadata = self._config._load_internal_json(metadata_path)
        version = metadata.get("version") or settings.get("version", "unknown")

        return {
            "version": version,
            "app_name": settings.get("app_name", "PocketMedic"),
            "build": {
                "channel": metadata.get("channel", "unknown"),
                "build_name": metadata.get("build_name", f"PocketMedic {version}"),
                "icon_path": metadata.get("icon_path"),
                "pyinstaller_spec": metadata.get("pyinstaller_spec", "PocketMedic.spec"),
            },
            "runtime": {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
            },
            "installer_cache": {
                "local_dir": app_path(settings.get("installer_cache", {}).get("local_dir", "Installers")),
                "onedrive_dir": settings.get("installer_cache", {}).get(
                    "onedrive_dir",
                    "PocketMedic/Installers",
                ),
                "usb_dir": settings.get("installer_cache", {}).get("usb_dir", "Installers"),
            },
            "v3_1_prep": {
                "goldenboy_detection": self.detect_goldenboy_usb(),
                "metadata": metadata.get("v3_1_prep", {}),
            },
            "config_sources": self._config.loaded_sources,
        }

    def detect_goldenboy_usb(self) -> Dict[str, Any]:
        """Prepare basic GoldenBoy USB detection using removable drive labels/paths."""
        matches = []
        for drive in self._removable_drives():
            label = self._volume_label(drive)
            has_installer_cache = os.path.isdir(os.path.join(drive, "Installers"))
            is_goldenboy = "goldenboy" in label.casefold() or os.path.exists(
                os.path.join(drive, "GoldenBoy")
            )
            if is_goldenboy or has_installer_cache:
                matches.append(
                    {
                        "drive": drive,
                        "label": label,
                        "has_installers": has_installer_cache,
                        "goldenboy_marker": is_goldenboy,
                    }
                )

        return {
            "prepared": True,
            "matches": matches,
            "status": "detected" if matches else "not_detected",
        }

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
    def _volume_label(root: str) -> str:
        if os.name != "nt":
            return ""

        buffer = ctypes.create_unicode_buffer(261)
        ctypes.windll.kernel32.GetVolumeInformationW(
            root,
            buffer,
            len(buffer),
            None,
            None,
            None,
            None,
            0,
        )
        return buffer.value
