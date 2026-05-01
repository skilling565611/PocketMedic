"""Local storage management for PocketMedic.

Handles JSON config/data files, the PortableTools directory, and general
filesystem helpers.
"""

import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional

from Core.Paths import app_root, find_resource, resolve_app


class Storage:
    """Manage persistent configuration and data files."""

    def __init__(self, base_dir: Optional[str] = None, logger=None):
        self._logger = logger
        self.base_dir = base_dir or app_root()

    # ------------------------------------------------------------------
    # JSON helpers
    # ------------------------------------------------------------------

    def load_json(self, path: str) -> Dict[str, Any]:
        """Load and return a JSON file, or an empty dict on error."""
        full_path = self._resolve_read(path)
        try:
            with open(full_path, "r", encoding="utf-8") as file_handle:
                data = json.load(file_handle)
            self._log(f"Loaded JSON: {full_path}")
            return data
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            self._warning(f"Warning: failed to load JSON {full_path!r}: {exc}")
            return {}

    def save_json(self, path: str, data: Dict[str, Any]) -> bool:
        """Serialize data to a JSON file."""
        full_path = self._resolve(path)
        destination_dir = os.path.dirname(full_path)
        if destination_dir:
            os.makedirs(destination_dir, exist_ok=True)
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
            destination_dir = os.path.dirname(dst)
            if destination_dir:
                os.makedirs(destination_dir, exist_ok=True)
            shutil.copy2(src, dst)
            self._log(f"Copied {src!r} -> {dst!r}")
            return True
        except OSError as exc:
            self._log(f"Copy failed: {exc}")
            return False

    def offload_path(self, src: str, destination_dir: str) -> Dict[str, Any]:
        """Copy a file or directory to a destination and write a manifest."""
        source_path = self._resolve(src)
        destination_path = self._resolve(destination_dir)
        if not os.path.exists(source_path):
            return {
                "success": False,
                "source": source_path,
                "destination": destination_path,
                "message": "Source path not found.",
            }

        os.makedirs(destination_path, exist_ok=True)
        target_path = os.path.join(destination_path, os.path.basename(source_path))
        try:
            if os.path.isdir(source_path):
                shutil.copytree(source_path, target_path, dirs_exist_ok=True)
            else:
                shutil.copy2(source_path, target_path)

            manifest = self._write_offload_manifest(source_path, target_path)
            self._log(f"Offloaded {source_path!r} -> {target_path!r}")
            return {
                "success": True,
                "source": source_path,
                "destination": target_path,
                "manifest": manifest,
                "message": "Offload complete.",
            }
        except OSError as exc:
            self._log(f"Offload failed: {exc}")
            return {
                "success": False,
                "source": source_path,
                "destination": target_path,
                "message": str(exc),
            }

    def list_offloads(self, destination_dir: str) -> List[str]:
        """Return files and folders currently present in an offload destination."""
        destination_path = self._resolve(destination_dir)
        if not os.path.isdir(destination_path):
            return []
        return sorted(os.path.join(destination_path, item) for item in os.listdir(destination_path))

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

    def _resolve_read(self, path: str) -> str:
        """Resolve read paths against bundled resources before writable app files."""
        if os.path.isabs(path):
            return path

        resource_candidate = find_resource(path)
        if os.path.exists(resource_candidate):
            return resource_candidate
        return resolve_app(path)

    def _write_offload_manifest(self, source_path: str, target_path: str) -> str:
        manifest_path = os.path.join(os.path.dirname(target_path), "offload_manifest.json")
        manifest = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "source": source_path,
            "destination": target_path,
            "source_type": "directory" if os.path.isdir(source_path) else "file",
        }
        with open(manifest_path, "w", encoding="utf-8") as file_handle:
            json.dump(manifest, file_handle, indent=4)
        return manifest_path

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)

    def _warning(self, message: str) -> None:
        if self._logger:
            self._logger.warning(message)
