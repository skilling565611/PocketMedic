"""Local storage management for PocketMedic.

Handles JSON config/data files, the PortableTools directory, and general
filesystem helpers.
"""

import json
import os
import shutil
from typing import Any, Dict, Optional


class Storage:
    """Manage persistent configuration and data files."""

    def __init__(self, base_dir: Optional[str] = None, logger=None):
        self._logger = logger
        self.base_dir = base_dir or os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

    # ------------------------------------------------------------------
    # JSON helpers
    # ------------------------------------------------------------------

    def load_json(self, path: str) -> Dict[str, Any]:
        """Load and return a JSON file, or an empty dict on error."""
        full_path = self._resolve(path)
        try:
            with open(full_path, "r", encoding="utf-8") as file_handle:
                data = json.load(file_handle)
            self._log(f"Loaded JSON: {full_path}")
            return data
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            self._log(f"Failed to load JSON {full_path!r}: {exc}")
            return {}

    def save_json(self, path: str, data: Dict[str, Any]) -> bool:
        """Serialize data to a JSON file."""
        full_path = self._resolve(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        try:
            with open(full_path, "w", encoding="utf-8") as file_handle:
                json.dump(data, file_handle, indent=4)
            self._log(f"Saved JSON: {full_path}")
            return True
        except OSError as exc:
            self._log(f"Failed to save JSON {full_path!r}: {exc}")
            return False

    # ------------------------------------------------------------------
    # Filesystem helpers
    # ------------------------------------------------------------------

    def ensure_dir(self, path: str) -> str:
        """Create a directory if needed and return its full path."""
        full_path = self._resolve(path)
        os.makedirs(full_path, exist_ok=True)
        return full_path

    def copy_file(self, src: str, dst: str) -> bool:
        """Copy a file and return True on success."""
        try:
            shutil.copy2(src, dst)
            self._log(f"Copied {src!r} -> {dst!r}")
            return True
        except OSError as exc:
            self._log(f"Copy failed: {exc}")
            return False

    def delete_file(self, path: str) -> bool:
        """Delete a file and return True on success."""
        full_path = self._resolve(path)
        try:
            os.remove(full_path)
            self._log(f"Deleted: {full_path}")
            return True
        except OSError as exc:
            self._log(f"Delete failed: {exc}")
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve(self, path: str) -> str:
        """Return an absolute path, resolving relative paths against base_dir."""
        if os.path.isabs(path):
            return path
        return os.path.join(self.base_dir, path)

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)
