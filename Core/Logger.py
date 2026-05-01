"""
Core/Logger.py — Centralised logging for PocketMedic.
"""

import os
import logging
from datetime import datetime


LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Logs")


class Logger:
    """Wrapper around Python's logging module that writes to a dated log file
    inside the Logs/ directory as well as to the console."""

    def __init__(self, name: str = "PocketMedic", level: str = "INFO"):
        os.makedirs(LOG_DIR, exist_ok=True)

        log_filename = datetime.now().strftime("%Y-%m-%d") + ".log"
        log_path = os.path.join(LOG_DIR, log_filename)

        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        if not self._logger.handlers:
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] %(message)s",
                datefmt="%H:%M:%S",
            )

            # File handler
            fh = logging.FileHandler(log_path, encoding="utf-8")
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)

            # Console handler
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)
            self._logger.addHandler(ch)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def log(self, message: str) -> None:
        """Alias for info()."""
        self._logger.info(message)

    def info(self, message: str) -> None:
        self._logger.info(message)

    def warning(self, message: str) -> None:
        self._logger.warning(message)

    def error(self, message: str) -> None:
        self._logger.error(message)

    def debug(self, message: str) -> None:
        self._logger.debug(message)
