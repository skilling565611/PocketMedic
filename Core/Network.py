"""Network diagnostics for PocketMedic.

Checks internet connectivity, DNS resolution, and basic ping reachability.
"""

import platform
import socket
import subprocess
from typing import Dict, List, Optional


class Network:
    """Run network connectivity and diagnostics checks."""

    DEFAULT_HOSTS = ["8.8.8.8", "1.1.1.1"]
    DNS_TEST_HOST = "google.com"

    def __init__(self, logger=None):
        self._logger = logger

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_connectivity(self) -> bool:
        """Return True if basic internet connectivity is detected."""
        try:
            with socket.create_connection(("8.8.8.8", 53), timeout=3):
                self._log("Internet connectivity: OK")
                return True
        except OSError:
            self._log("Internet connectivity: FAILED")
            return False

    def check_dns(self, hostname: str = DNS_TEST_HOST) -> bool:
        """Return True if DNS resolution for the hostname succeeds."""
        try:
            socket.gethostbyname(hostname)
            self._log(f"DNS resolution of {hostname!r}: OK")
            return True
        except socket.gaierror:
            self._log(f"DNS resolution of {hostname!r}: FAILED")
            return False

    def ping(self, host: str, count: int = 4) -> Dict[str, object]:
        """Ping a host and return a result dict with success and output keys."""
        if platform.system() == "Windows":
            cmd = ["ping", "-n", str(count), host]
        else:
            cmd = ["ping", "-c", str(count), host]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            success = result.returncode == 0
            self._log(f"Ping {host!r}: {'OK' if success else 'FAILED'}")
            return {"success": success, "output": result.stdout}
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            self._log(f"Ping {host!r} error: {exc}")
            return {"success": False, "output": str(exc)}

    def full_report(self, hosts: Optional[List[str]] = None) -> Dict[str, object]:
        """Run all network checks and return a combined report."""
        target_hosts = hosts or self.DEFAULT_HOSTS
        return {
            "connectivity": self.check_connectivity(),
            "dns": self.check_dns(),
            "ping_results": {host: self.ping(host) for host in target_hosts},
            "network_drives": self.list_network_drives(),
        }

    def list_network_drives(self) -> List[Dict[str, str]]:
        """List mapped network drives on Windows."""
        if platform.system() != "Windows":
            return []

        try:
            result = subprocess.run(
                ["net", "use"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            self._log(f"Network drive listing failed: {exc}")
            return []

        drives = []
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[1].endswith(":"):
                drives.append(
                    {
                        "status": parts[0],
                        "drive": parts[1],
                        "remote": parts[2],
                    }
                )
        return drives

    def reconnect_network_drive(
        self,
        drive_letter: str,
        remote_path: str,
        persistent: bool = True,
        dry_run: bool = True,
    ) -> Dict[str, object]:
        """Reconnect a Windows network drive, or preview the command in dry-run mode."""
        drive = drive_letter.rstrip(":") + ":"
        command = [
            "net",
            "use",
            drive,
            remote_path,
            f"/persistent:{'yes' if persistent else 'no'}",
        ]
        if platform.system() != "Windows":
            return {
                "success": False,
                "dry_run": dry_run,
                "command": " ".join(command),
                "message": "Network drive reconnect is Windows-only.",
            }
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "command": " ".join(command),
                "message": "Reconnect command prepared.",
            }

        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=20)
            success = result.returncode == 0
            return {
                "success": success,
                "dry_run": False,
                "command": " ".join(command),
                "message": result.stdout.strip() if success else result.stderr.strip(),
            }
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            return {
                "success": False,
                "dry_run": False,
                "command": " ".join(command),
                "message": str(exc),
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)
