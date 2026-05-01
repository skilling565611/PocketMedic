"""Text-based terminal user interface for PocketMedic.

Provides an interactive menu-driven CLI so users can run scans, manage
startup items, check network health, and more, all without a graphical
desktop environment.
"""


class TerminalUI:
    """Simple menu-driven CLI interface."""

    MENU = [
        ("1", "System Scan", "scan"),
        ("2", "Hardware Report", "hardware"),
        ("3", "Network Diagnostics", "network"),
        ("4", "Startup Manager", "startup"),
        ("5", "Backup", "backup"),
        ("Q", "Quit", "quit"),
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
        print("        PocketMedic - Portable PC Medic")
        print("=" * 50 + "\n")

    def _print_menu(self) -> None:
        print("\n  Main Menu")
        print("  " + "-" * 30)
        for key, label, _action in self.MENU:
            print(f"  [{key}] {label}")
        print()

    # ------------------------------------------------------------------
    # Action dispatch
    # ------------------------------------------------------------------

    def _handle(self, choice: str) -> bool:
        """Dispatch the selected menu choice.

        Returns False when the UI should exit.
        """
        for key, _label, action in self.MENU:
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
    # Action handlers wired to Core modules
    # ------------------------------------------------------------------

    def _action_scan(self) -> None:
        from Core.Scanner import Scanner

        scanner = Scanner(logger=self._logger)
        report = scanner.run_full_scan()
        print("\n  -- System Scan Report --")
        self._print_report(report)

    def _action_hardware(self) -> None:
        from Core.Hardware import Hardware

        hardware = Hardware(logger=self._logger)
        report = hardware.full_report()
        print("\n  -- Hardware Report --")
        self._print_report(report)

    def _action_network(self) -> None:
        from Core.Network import Network

        network = Network(logger=self._logger)
        print("\n  -- Network Diagnostics --")
        connected = network.check_connectivity()
        print(f"    Internet: {'OK' if connected else 'FAILED'}")
        dns_ok = network.check_dns()
        print(f"    DNS:      {'OK' if dns_ok else 'FAILED'}")

    def _action_startup(self) -> None:
        from Core.Startup import Startup

        startup = Startup(logger=self._logger)
        entries = startup.list_entries()
        print("\n  -- Startup Entries --")
        if entries:
            for entry in entries:
                print(f"    {entry['name']}: {entry['path']}")
        else:
            print("    No startup entries found (or not supported on this OS).")

    def _action_backup(self) -> None:
        from Core.Backup import Backup

        backup = Backup(logger=self._logger)
        archives = backup.list_backups()
        print("\n  -- Backups --")
        if archives:
            for archive in archives:
                print(f"    {archive}")
        else:
            print("    No backups found.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)

    @staticmethod
    def _print_report(report: dict) -> None:
        for section, data in report.items():
            print(f"\n  [{section.upper()}]")
            TerminalUI._print_value(data, indent=4)

    @staticmethod
    def _print_value(value, indent: int) -> None:
        prefix = " " * indent
        if isinstance(value, dict):
            for key, item in value.items():
                if isinstance(item, (dict, list)):
                    print(f"{prefix}{key}:")
                    TerminalUI._print_value(item, indent + 2)
                else:
                    print(f"{prefix}{key}: {item}")
            return

        if isinstance(value, list):
            for item in value:
                if isinstance(item, (dict, list)):
                    print(f"{prefix}-")
                    TerminalUI._print_value(item, indent + 2)
                else:
                    print(f"{prefix}- {item}")
            return

        print(f"{prefix}{value}")
