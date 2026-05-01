"""
GUI/TerminalUI.py — Text-based terminal user interface for PocketMedic.

Provides an interactive menu-driven CLI so users can run scans, manage
startup items, check network health, and more — all without a graphical
desktop environment.
"""

import sys
from typing import Optional


class TerminalUI:
    """Simple menu-driven CLI interface."""

    MENU = [
        ("1", "System Scan",          "scan"),
        ("2", "Hardware Report",      "hardware"),
        ("3", "Network Diagnostics",  "network"),
        ("4", "Startup Manager",      "startup"),
        ("5", "Backup",               "backup"),
        ("Q", "Quit",                 "quit"),
    ]

    def __init__(self, logger=None):
        self._logger = logger

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the interactive terminal UI loop."""
        self._print_banner()
        while True:
            self._print_menu()
            choice = input("  Select option: ").strip().upper()
            if not self._handle(choice):
                break

    # ------------------------------------------------------------------
    # Menu rendering
    # ------------------------------------------------------------------

    def _print_banner(self) -> None:
        print("\n" + "=" * 50)
        print("        PocketMedic — Portable PC Medic")
        print("=" * 50 + "\n")

    def _print_menu(self) -> None:
        print("\n  Main Menu")
        print("  " + "-" * 30)
        for key, label, _ in self.MENU:
            print(f"  [{key}] {label}")
        print()

    # ------------------------------------------------------------------
    # Action dispatch
    # ------------------------------------------------------------------

    def _handle(self, choice: str) -> bool:
        """Dispatch *choice* to the appropriate action.

        Returns False when the UI should exit.
        """
        for key, label, action in self.MENU:
            if choice == key:
                if action == "quit":
                    self._log("User quit.")
                    print("\nGoodbye!\n")
                    return False
                handler = getattr(self, f"_action_{action}", None)
                if handler:
                    handler()
                return True
        print(f"  Unknown option: {choice!r}")
        return True

    # ------------------------------------------------------------------
    # Action handlers (stubs — wired to Core modules)
    # ------------------------------------------------------------------

    def _action_scan(self) -> None:
        from Core.Scanner import Scanner
        scanner = Scanner(logger=self._logger)
        report = scanner.run_full_scan()
        print("\n  -- System Scan Report --")
        for section, data in report.items():
            print(f"\n  [{section.upper()}]")
            if isinstance(data, dict):
                for k, v in data.items():
                    print(f"    {k}: {v}")
            else:
                print(f"    {data}")

    def _action_hardware(self) -> None:
        from Core.Hardware import Hardware
        hw = Hardware(logger=self._logger)
        report = hw.full_report()
        print("\n  -- Hardware Report --")
        for section, data in report.items():
            print(f"\n  [{section.upper()}]")
            if isinstance(data, dict):
                for k, v in data.items():
                    print(f"    {k}: {v}")
            else:
                print(f"    {data}")

    def _action_network(self) -> None:
        from Core.Network import Network
        net = Network(logger=self._logger)
        print("\n  -- Network Diagnostics --")
        connected = net.check_connectivity()
        print(f"    Internet: {'OK' if connected else 'FAILED'}")
        dns_ok = net.check_dns()
        print(f"    DNS:      {'OK' if dns_ok else 'FAILED'}")

    def _action_startup(self) -> None:
        from Core.Startup import Startup
        st = Startup(logger=self._logger)
        entries = st.list_entries()
        print("\n  -- Startup Entries --")
        if entries:
            for e in entries:
                print(f"    {e['name']}: {e['path']}")
        else:
            print("    No startup entries found (or not supported on this OS).")

    def _action_backup(self) -> None:
        from Core.Backup import Backup
        bk = Backup(logger=self._logger)
        archives = bk.list_backups()
        print("\n  -- Backups --")
        if archives:
            for a in archives:
                print(f"    {a}")
        else:
            print("    No backups found.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)
