"""Backup and restore engine for PocketMedic.

Creates timestamped ZIP archives of target directories and can restore them.
"""

import os
import zipfile
from datetime import datetime
from typing import List, Optional


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Backup:
    """Create and restore ZIP-based backups."""

    def __init__(self, backup_dir: Optional[str] = None, logger=None):
        self._logger = logger
        self.backup_dir = backup_dir or os.path.join(PROJECT_ROOT, "Backups")
        os.makedirs(self.backup_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_backup(self, source_dir: str, label: str = "") -> Optional[str]:
        """Zip a source directory into a timestamped archive.

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
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
                for root, _dirs, files in os.walk(source_dir):
                    for filename in files:
                        absolute_path = os.path.join(root, filename)
                        relative_path = os.path.relpath(absolute_path, start=source_dir)
                        archive.write(absolute_path, relative_path)
            self._log(f"Backup created: {archive_path}")
            return archive_path
        except OSError as exc:
            self._log(f"Backup failed: {exc}")
            return None

    def restore_backup(self, archive_path: str, dest_dir: str) -> bool:
        """Extract an archive into a destination directory."""
        if not os.path.isfile(archive_path):
            self._log(f"Archive not found: {archive_path!r}")
            return False

        os.makedirs(dest_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(archive_path, "r") as archive:
                archive.extractall(dest_dir)
            self._log(f"Restored {archive_path!r} -> {dest_dir!r}")
            return True
        except (OSError, zipfile.BadZipFile) as exc:
            self._log(f"Restore failed: {exc}")
            return False

    def list_backups(self) -> List[str]:
        """Return a sorted list of archive paths in the backup directory."""
        if not os.path.isdir(self.backup_dir):
            return []

        archives = [
            os.path.join(self.backup_dir, filename)
            for filename in os.listdir(self.backup_dir)
            if filename.endswith(".zip")
        ]
        return sorted(archives)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)
