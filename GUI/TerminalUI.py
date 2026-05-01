"""Text-based terminal user interface for PocketMedic.

Provides an interactive menu-driven CLI so users can run scans, manage
startup items, check network health, and more, all without a graphical
desktop environment.
"""

import os


class TerminalUI:
    """Simple menu-driven CLI interface."""

    MENU = [
        ("1", "System Scan", "scan"),
        ("2", "Hardware Report", "hardware"),
        ("3", "Network Diagnostics", "network"),
        ("4", "Startup Manager", "startup"),
        ("5", "Backup", "backup"),
        ("6", "Rebuild Assistant", "rebuild"),
        ("7", "Maintenance Utilities", "utilities"),
        ("8", "App Installer", "app_installer"),
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

    def _action_rebuild(self) -> None:
        from Core.RebuildAssistant import RebuildAssistant

        assistant = RebuildAssistant(logger=self._logger)
        report = assistant.run_workflow()
        print("\n  -- PocketMedic V2.1 Rebuild Assistant --")
        self._print_rebuild_summary(report)

    def _action_utilities(self) -> None:
        from Core.Installer import Installer
        from Core.Network import Network
        from Core.OneDrive import OneDrive
        from Core.Startup import Startup
        from Core.Storage import Storage

        storage = Storage(logger=self._logger)
        settings = storage.load_json("Config/Global.Settings.json")
        definitions_path = settings.get(
            "package_definitions_path",
            "Config/Package.Definitions.json",
        )
        startup_delay = settings.get("startup_delay_seconds", 30)
        offload_relative = settings.get("storage_offload", {}).get(
            "default_relative_path",
            "PocketMedic/Offload",
        )

        installer = Installer(logger=self._logger)
        onedrive = OneDrive(logger=self._logger)
        network = Network(logger=self._logger)
        startup = Startup(logger=self._logger)

        onedrive_status = onedrive.status()
        offload_destination = None
        if onedrive_status.get("root"):
            offload_destination = os.path.normpath(
                os.path.join(onedrive_status["root"], offload_relative)
            )

        report = {
            "installer_engine": {
                "install_plan": installer.build_install_plan(
                    installer.load_package_definitions(definitions_path)
                ),
            },
            "onedrive_integration": onedrive_status,
            "storage_offload_system": {
                "default_destination": offload_destination,
                "existing_items": (
                    storage.list_offloads(offload_destination)
                    if offload_destination and os.path.isdir(offload_destination)
                    else []
                ),
                "safe_mode": "Path is previewed only; offload methods create folders when called.",
            },
            "network_drive_reconnect": {
                "mapped_drives": network.list_network_drives(),
                "configured_drives": settings.get("network_drives", []),
                "safe_mode": "Reconnect commands are previewed until dry_run is disabled.",
            },
            "startup_delay_manager": {
                "delay_seconds": startup_delay,
                "planned_entries": startup.build_delay_plan(delay_seconds=startup_delay),
                "safe_mode": "Scheduled tasks are previewed until dry_run is disabled.",
            },
        }

        print("\n  -- Maintenance Utilities --")
        self._print_report(report)

    def _action_app_installer(self) -> None:
        from Core.Installer import Installer
        from Core.Storage import Storage

        storage = Storage(logger=self._logger)
        settings = storage.load_json("Config/Global.Settings.json")
        definitions_path = settings.get(
            "package_definitions_path",
            "Config/Package.Definitions.json",
        )

        installer = Installer(logger=self._logger)
        definitions = installer.load_package_definitions(definitions_path)
        plan = installer.build_install_plan(definitions)

        print("\n  -- App Installer Framework --")
        self._print_install_plan(plan)

        if plan.get("missing_count", 0) == 0:
            print("\n  All enabled packages are already detected.")
            return

        print("\n  Type INSTALL to install missing enabled packages.")
        print("  Press Enter to cancel without changes.")
        confirmation = input("  Confirm install: ").strip()
        if confirmation != "INSTALL":
            results = installer.install_missing_from_plan(plan, confirmed=False)
            print("\n  Install canceled.")
            self._print_value(results, indent=4)
            return

        results = installer.install_missing_from_plan(plan, confirmed=True)
        print("\n  Install Results")
        self._print_value(results, indent=4)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)

    @staticmethod
    def _print_rebuild_summary(report: dict) -> None:
        summary = report.get("summary", {})
        checklist = report.get("checklist", [])
        ready_label = "READY" if summary.get("ready") else "NEEDS REVIEW"

        print(f"\n  Status: {ready_label}")
        print(
            "  "
            f"Passed: {summary.get('passed', 0)} | "
            f"Warnings: {summary.get('warnings', 0)} | "
            f"Errors: {summary.get('errors', 0)}"
        )

        for index, step in enumerate(checklist, start=1):
            status = str(step.get("status", "unknown")).upper()
            print(f"\n  {index}. [{status}] {step.get('title', 'Untitled step')}")
            print(f"     {step.get('message', '')}")
            details = step.get("details", {})
            if details:
                TerminalUI._print_value(details, indent=5)

    @staticmethod
    def _print_report(report: dict) -> None:
        for section, data in report.items():
            print(f"\n  [{section.upper()}]")
            TerminalUI._print_value(data, indent=4)

    @staticmethod
    def _print_install_plan(plan: dict) -> None:
        manager = plan.get("manager_status", {}).get("active_manager")
        print(f"\n  Package manager: {manager or 'not detected'}")
        print(f"  Missing packages: {plan.get('missing_count', 0)}")
        print("  Manual confirmation required: yes")

        for package in plan.get("packages", []):
            status = "INSTALLED" if package.get("installed") else "MISSING"
            print(f"\n  [{status}] {package.get('display_name')}")
            print(f"    key: {package.get('key')}")
            print(f"    category: {package.get('category')}")
            print(f"    winget_id: {package.get('winget_id')}")
            print(f"    command: {package.get('install_command') or '(none)'}")

    @staticmethod
    def _print_value(value, indent: int) -> None:
        prefix = " " * indent
        if isinstance(value, dict):
            if not value:
                print(f"{prefix}(none)")
                return
            for key, item in value.items():
                if isinstance(item, (dict, list)):
                    print(f"{prefix}{key}:")
                    TerminalUI._print_value(item, indent + 2)
                else:
                    print(f"{prefix}{key}: {item}")
            return

        if isinstance(value, list):
            if not value:
                print(f"{prefix}(none)")
                return
            for item in value:
                if isinstance(item, (dict, list)):
                    print(f"{prefix}-")
                    TerminalUI._print_value(item, indent + 2)
                else:
                    print(f"{prefix}- {item}")
            return

        print(f"{prefix}{value}")
