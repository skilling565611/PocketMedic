"""Graphical dashboard for PocketMedic.

Provides a Tkinter-based GUI dashboard that surfaces the same features as the
terminal UI.
"""


def _tkinter_available() -> bool:
    try:
        import tkinter  # noqa: F401
        return True
    except ImportError:
        return False


class Dashboard:
    """Tkinter GUI dashboard with a graceful no-Tkinter fallback."""

    def __init__(self, logger=None):
        self._logger = logger
        self._root = None
        self._output = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Launch the GUI dashboard."""
        if not _tkinter_available():
            self._log("Tkinter is not available; cannot launch Dashboard.")
            print("Dashboard requires Tkinter. Please use the terminal UI instead.")
            return

        self._build()
        self._root.mainloop()

    # ------------------------------------------------------------------
    # GUI construction
    # ------------------------------------------------------------------

    def _build(self) -> None:
        import tkinter as tk
        from tkinter import ttk

        self._root = tk.Tk()
        self._root.title("PocketMedic Dashboard")
        self._root.geometry("640x480")
        self._root.resizable(True, True)

        header = tk.Label(
            self._root,
            text="PocketMedic",
            font=("Helvetica", 20, "bold"),
            pady=10,
        )
        header.pack(fill=tk.X)

        subtitle = tk.Label(
            self._root,
            text="Portable PC Maintenance & Repair Toolkit",
            font=("Helvetica", 10),
        )
        subtitle.pack()

        ttk.Separator(self._root, orient="horizontal").pack(fill=tk.X, pady=8)

        button_frame = tk.Frame(self._root)
        button_frame.pack(pady=10)

        buttons = [
            ("System Scan", self._on_scan),
            ("Hardware Report", self._on_hardware),
            ("Network Diagnostics", self._on_network),
            ("Startup Manager", self._on_startup),
            ("Backup", self._on_backup),
        ]

        for text, command in buttons:
            button = ttk.Button(button_frame, text=text, command=command, width=24)
            button.pack(pady=4)

        ttk.Separator(self._root, orient="horizontal").pack(fill=tk.X, pady=8)
        self._output = tk.Text(self._root, height=12, state=tk.DISABLED, wrap=tk.WORD)
        self._output.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    # ------------------------------------------------------------------
    # Button callbacks
    # ------------------------------------------------------------------

    def _on_scan(self) -> None:
        from Core.Scanner import Scanner

        scanner = Scanner(logger=self._logger)
        report = scanner.run_full_scan()
        self._show(self._format_report("System Scan", report))

    def _on_hardware(self) -> None:
        from Core.Hardware import Hardware

        hardware = Hardware(logger=self._logger)
        report = hardware.full_report()
        self._show(self._format_report("Hardware Report", report))

    def _on_network(self) -> None:
        from Core.Network import Network

        network = Network(logger=self._logger)
        lines = [
            f"Internet: {'OK' if network.check_connectivity() else 'FAILED'}",
            f"DNS:      {'OK' if network.check_dns() else 'FAILED'}",
        ]
        self._show("Network Diagnostics\n" + "-" * 30 + "\n" + "\n".join(lines))

    def _on_startup(self) -> None:
        from Core.Startup import Startup

        entries = Startup(logger=self._logger).list_entries()
        lines = [f"{entry['name']}: {entry['path']}" for entry in entries]
        self._show(
            "Startup Manager\n"
            + "-" * 30
            + "\n"
            + "\n".join(lines or ["No startup entries found."])
        )

    def _on_backup(self) -> None:
        from Core.Backup import Backup

        archives = Backup(logger=self._logger).list_backups()
        self._show(
            "Backup Archives\n"
            + "-" * 30
            + "\n"
            + "\n".join(archives or ["No backups found."])
        )

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------

    def _show(self, text: str) -> None:
        import tkinter as tk

        self._output.config(state=tk.NORMAL)
        self._output.delete("1.0", tk.END)
        self._output.insert(tk.END, text)
        self._output.config(state=tk.DISABLED)

    @staticmethod
    def _format_report(title: str, report: dict) -> str:
        lines = [title, "-" * 30]
        for section, data in report.items():
            lines.append(f"\n[{section.upper()}]")
            if isinstance(data, dict):
                for key, value in data.items():
                    lines.append(f"  {key}: {value}")
            else:
                lines.append(f"  {data}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)
