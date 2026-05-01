"""OneDrive integration helpers for PocketMedic.

Detects the local OneDrive folder and copies files into it when available.
"""

import os
import platform
import shutil
from typing import Dict, Optional


class OneDrive:
    """OneDrive sync and offload helper."""

    _WINDOWS_ROOTS = [
        os.path.expanduser("~/OneDrive"),
        os.path.expanduser("~/OneDrive - Personal"),
    ]

    def __init__(self, logger=None):
        self._logger = logger
        self._root: Optional[str] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def status(self) -> Dict[str, object]:
        """Return OneDrive detection status and useful PocketMedic paths."""
        detected = self.detect()
        return {
            "detected": detected,
            "root": self._root,
            "offload_root": (
                os.path.join(self._root, "PocketMedic", "Offload") if self._root else None
            ),
            "rebuild_backup_root": (
                os.path.join(self._root, "PocketMedic", "RebuildBackups")
                if self._root
                else None
            ),
        }

    def detect(self) -> bool:
        """Try to locate the local OneDrive folder."""
        if platform.system() != "Windows":
            self._log("OneDrive detection is only supported on Windows.")
            return False

        env_root = os.environ.get("OneDrive") or os.environ.get("OneDriveConsumer")
        if env_root and os.path.isdir(env_root):
            self._root = env_root
            self._log(f"OneDrive detected at: {self._root}")
            return True

        for candidate in self._WINDOWS_ROOTS:
            if os.path.isdir(candidate):
                self._root = candidate
                self._log(f"OneDrive detected at: {self._root}")
                return True

        self._log("OneDrive not detected on this system.")
        return False

    @property
    def root(self) -> Optional[str]:
        """Return the local OneDrive root path, or None if not detected."""
        return self._root

    def is_available(self) -> bool:
        """Return True if OneDrive has been detected."""
        return self._root is not None

    def copy_to_onedrive(self, src: str, relative_dest: str) -> bool:
        """Copy a file into OneDrive at a path relative to the OneDrive root."""
        if not self.is_available():
            self._log("OneDrive not available; skipping copy.")
            return False

        dest = os.path.join(self._root, relative_dest)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        try:
            shutil.copy2(src, dest)
            self._log(f"Copied to OneDrive: {src!r} -> {dest!r}")
            return True
        except OSError as exc:
            self._log(f"Failed to copy to OneDrive: {exc}")
            return False

    def ensure_folder(self, relative_path: str) -> Optional[str]:
        """Create and return a folder inside OneDrive when available."""
        if not self.is_available() and not self.detect():
            return None

        folder_path = os.path.normpath(os.path.join(self._root, relative_path))
        os.makedirs(folder_path, exist_ok=True)
        self._log(f"OneDrive folder ready: {folder_path}")
        return folder_path

    def offload_file(self, src: str, relative_folder: str = "PocketMedic/Offload") -> bool:
        """Copy a file into the configured OneDrive offload folder."""
        if not os.path.isfile(src):
            self._log(f"Offload source file not found: {src!r}")
            return False

        filename = os.path.basename(src)
        relative_dest = os.path.join(relative_folder, filename)
        return self.copy_to_onedrive(src, relative_dest)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)
