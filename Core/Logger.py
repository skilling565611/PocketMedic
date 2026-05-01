"""Centralized logging for PocketMedic."""

import logging
import os
from datetime import datetime


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(PROJECT_ROOT, "Logs")


class Logger:
    """Write PocketMedic messages to a dated log file and the console."""

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

            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def log(self, message: str) -> None:
        """Log an informational message."""
        self._logger.info(message)

    def info(self, message: str) -> None:
        self._logger.info(message)

    def warning(self, message: str) -> None:
        self._logger.warning(message)

    def error(self, message: str) -> None:
        self._logger.error(message)

    def debug(self, message: str) -> None:
        self._logger.debug(message)
