"""PocketMedic entry point."""

import os
import sys

if getattr(sys, "frozen", False):
    RUNTIME_ROOT = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    RUNTIME_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RUNTIME_ROOT)

from Core.Logger import Logger
from GUI.TerminalUI import TerminalUI


def main() -> None:
    """Launch PocketMedic in terminal mode."""
    logger = Logger()
    logger.log("PocketMedic starting...")

    ui = TerminalUI(logger=logger)
    ui.run()


if __name__ == "__main__":
    main()
