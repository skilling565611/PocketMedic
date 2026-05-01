"""
Core/OneDrive.py — OneDrive integration for PocketMedic.

Provides helpers to detect, authenticate, and sync files with a user's
OneDrive account.  On Windows this wraps the OneDrive CLI / known folder
paths; on other platforms it falls back to graceful no-ops.
"""

import os
import platform
import shutil
from typing import Optional


class OneDrive:
    """OneDrive sync and offload helper."""

    # Common OneDrive root locations
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

    def detect(self) -> bool:
        """Try to locate the local OneDrive folder.

        Returns True if found and sets *self._root*.
        """
        if platform.system() == "Windows":
            # Check environment variable first (most reliable)
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
        """The local OneDrive root path, or None if not detected."""
        return self._root

    def is_available(self) -> bool:
        """Return True if OneDrive has been detected."""
        return self._root is not None

    def copy_to_onedrive(self, src: str, relative_dest: str) -> bool:
        """Copy *src* into OneDrive at *relative_dest* (relative to OneDrive root).

        Returns True on success.
        """
        if not self.is_available():
            self._log("OneDrive not available — skipping copy.")
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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)
