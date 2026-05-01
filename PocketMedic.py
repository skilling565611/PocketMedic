"""
PocketMedic - Portable PC Maintenance & Repair Toolkit
Entry Point
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Core.Logger import Logger
from GUI.TerminalUI import TerminalUI


def main():
    logger = Logger()
    logger.log("PocketMedic starting...")

    ui = TerminalUI(logger=logger)
    ui.run()


if __name__ == "__main__":
    main()
