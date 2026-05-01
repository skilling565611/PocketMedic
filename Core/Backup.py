"""
Core/Backup.py — Backup and restore engine for PocketMedic.

Creates timestamped ZIP archives of target directories and can restore
them.  Supports local and OneDrive destinations.
"""

import os
import shutil
import zipfile
from datetime import datetime
from typing import List, Optional


class Backup:
    """Creates and restores ZIP-based backups."""

    def __init__(self, backup_dir: Optional[str] = None, logger=None):
        self._logger = logger
        self.backup_dir = backup_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Backups"
        )
        os.makedirs(self.backup_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_backup(self, source_dir: str, label: str = "") -> Optional[str]:
        """Zip *source_dir* into a timestamped archive in *self.backup_dir*.

        Returns the path to the created archive, or None on failure.
        """
        if not os.path.isdir(source_dir):
            self._log(f"Source directory not found: {source_dir!r}")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_label = label.replace(" ", "_") if label else os.path.basename(source_dir)
        archive_name = f"{safe_label}_{timestamp}.zip"
        archive_path = os.path.join(self.backup_dir, archive_name)

        try:
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, _dirs, files in os.walk(source_dir):
                    for file in files:
                        abs_path = os.path.join(root, file)
                        arcname = os.path.relpath(abs_path, start=source_dir)
                        zf.write(abs_path, arcname)
            self._log(f"Backup created: {archive_path}")
            return archive_path
        except OSError as exc:
            self._log(f"Backup failed: {exc}")
            return None

    def restore_backup(self, archive_path: str, dest_dir: str) -> bool:
        """Extract *archive_path* into *dest_dir*.  Returns True on success."""
        if not os.path.isfile(archive_path):
            self._log(f"Archive not found: {archive_path!r}")
            return False

        os.makedirs(dest_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(dest_dir)
            self._log(f"Restored {archive_path!r} -> {dest_dir!r}")
            return True
        except (OSError, zipfile.BadZipFile) as exc:
            self._log(f"Restore failed: {exc}")
            return False

    def list_backups(self) -> List[str]:
        """Return a sorted list of archive paths in *self.backup_dir*."""
        if not os.path.isdir(self.backup_dir):
            return []
        archives = [
            os.path.join(self.backup_dir, f)
            for f in os.listdir(self.backup_dir)
            if f.endswith(".zip")
        ]
        return sorted(archives)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)
