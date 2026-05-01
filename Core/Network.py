"""
Core/Network.py — Network diagnostics for PocketMedic.

Checks internet connectivity, DNS resolution, and basic ping reachability.
"""

import socket
import subprocess
import platform
from typing import Dict, List


class Network:
    """Network connectivity and diagnostics."""

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
            socket.setdefaulttimeout(3)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            self._log("Internet connectivity: OK")
            return True
        except OSError:
            self._log("Internet connectivity: FAILED")
            return False

    def check_dns(self, hostname: str = DNS_TEST_HOST) -> bool:
        """Return True if DNS resolution for *hostname* succeeds."""
        try:
            socket.gethostbyname(hostname)
            self._log(f"DNS resolution of {hostname!r}: OK")
            return True
        except socket.gaierror:
            self._log(f"DNS resolution of {hostname!r}: FAILED")
            return False

    def ping(self, host: str, count: int = 4) -> Dict[str, object]:
        """Ping *host* and return a result dict with 'success' and 'output' keys."""
        system = platform.system()
        if system == "Windows":
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

    def full_report(self, hosts: List[str] = None) -> Dict[str, object]:
        """Run all checks and return a combined report."""
        hosts = hosts or self.DEFAULT_HOSTS
        return {
            "connectivity": self.check_connectivity(),
            "dns": self.check_dns(),
            "ping_results": {h: self.ping(h) for h in hosts},
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)
