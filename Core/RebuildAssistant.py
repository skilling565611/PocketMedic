"""PocketMedic V2.1 rebuild workflow assistant.

The assistant verifies rebuild readiness and prepares next-step hooks without
making destructive changes to the machine.
"""

import os
import platform
import shutil
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from Core.Installer import Installer
from Core.Network import Network
from Core.OneDrive import OneDrive


DEFAULT_PACKAGES = ["python", "git"]


@dataclass
class RebuildStep:
    """A single rebuild workflow step."""

    key: str
    title: str
    action: Callable[[], Dict[str, Any]]


class RebuildAssistant:
    """Run rebuild readiness checks and package installation planning."""

    def __init__(self, logger=None):
        self._logger = logger
        self._network = Network(logger=logger)
        self._onedrive = OneDrive(logger=logger)
        self._installer = Installer(logger=logger)
        self._steps = self._build_steps()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_workflow(self) -> Dict[str, Any]:
        """Run the rebuild workflow and return a structured report."""
        self._log("Starting Rebuild Assistant workflow...")
        results = [self._run_step(step) for step in self._steps]
        summary = self._summarize(results)
        self._log("Rebuild Assistant workflow complete.")
        return {
            "assistant": {
                "version": "2.1",
                "mode": "readiness_check",
                "safe_mode": True,
            },
            "summary": summary,
            "checklist": results,
        }

    def get_checklist(self) -> List[Dict[str, str]]:
        """Return the static rebuild checklist without running checks."""
        return [{"key": step.key, "title": step.title} for step in self._steps]

    # ------------------------------------------------------------------
    # Step construction
    # ------------------------------------------------------------------

    def _build_steps(self) -> List[RebuildStep]:
        return [
            RebuildStep("windows", "Verify Windows environment", self.verify_windows),
            RebuildStep("onedrive", "Detect OneDrive backup path", self.detect_onedrive),
            RebuildStep("network", "Validate network connectivity", self.validate_network),
            RebuildStep("drivers", "Validate driver tooling", self.validate_drivers),
            RebuildStep("packages", "Prepare package installer hooks", self.prepare_packages),
        ]

    def _run_step(self, step: RebuildStep) -> Dict[str, Any]:
        self._log(f"Rebuild step started: {step.title}")
        try:
            result = step.action()
        except Exception as exc:  # Defensive so one failed check does not stop the workflow.
            result = {
                "status": "error",
                "message": f"{step.title} failed: {exc}",
                "details": {},
            }

        result["key"] = step.key
        result["title"] = step.title
        self._log(f"Rebuild step finished: {step.title} ({result['status']})")
        return result

    # ------------------------------------------------------------------
    # Workflow checks
    # ------------------------------------------------------------------

    def verify_windows(self) -> Dict[str, Any]:
        """Verify whether the current machine is a supported Windows target."""
        system = platform.system()
        release = platform.release()
        is_windows = system == "Windows"
        supported_release = release in {"10", "11"}
        status = "pass" if is_windows and supported_release else "warning"
        message = (
            f"Windows {release} rebuild target verified."
            if status == "pass"
            else f"Expected Windows 10/11, found {system} {release}."
        )
        return {
            "status": status,
            "message": message,
            "details": {
                "system": system,
                "release": release,
                "version": platform.version(),
                "machine": platform.machine(),
                "computer_name": platform.node(),
            },
        }

    def detect_onedrive(self) -> Dict[str, Any]:
        """Detect whether a local OneDrive path is ready for rebuild backups."""
        detected = self._onedrive.detect()
        root = self._onedrive.root
        return {
            "status": "pass" if detected else "warning",
            "message": "OneDrive backup path detected." if detected else "OneDrive path not detected.",
            "details": {
                "detected": detected,
                "root": root,
                "recommended_backup_folder": (
                    os.path.join(root, "PocketMedic", "RebuildBackups") if root else None
                ),
            },
        }

    def validate_network(self) -> Dict[str, Any]:
        """Validate connectivity and DNS readiness."""
        connectivity = self._network.check_connectivity()
        dns = self._network.check_dns()
        status = "pass" if connectivity and dns else "warning"
        return {
            "status": status,
            "message": (
                "Network and DNS checks passed."
                if status == "pass"
                else "Network or DNS needs attention before rebuild."
            ),
            "details": {
                "internet_connectivity": connectivity,
                "dns_resolution": dns,
            },
        }

    def validate_drivers(self) -> Dict[str, Any]:
        """Validate driver tooling and provide safe next-step commands."""
        system = platform.system()
        if system != "Windows":
            return {
                "status": "warning",
                "message": "Driver validation is currently Windows-focused.",
                "details": {"system": system, "driver_tool": None, "recommended_commands": []},
            }

        pnputil = shutil.which("pnputil")
        status = "pass" if pnputil else "warning"
        commands = [
            "pnputil /enum-drivers",
            "pnputil /scan-devices",
        ]
        return {
            "status": status,
            "message": (
                "Windows driver tooling is available."
                if pnputil
                else "pnputil was not found on PATH; driver validation is limited."
            ),
            "details": {
                "driver_tool": pnputil,
                "recommended_commands": commands,
                "device_manager_hint": "Review Device Manager for warning icons after rebuild.",
            },
        }

    def prepare_packages(self) -> Dict[str, Any]:
        """Prepare package installer hooks without installing packages."""
        manager = self._detect_package_manager()
        package_hooks = []
        for package in DEFAULT_PACKAGES:
            package_hooks.append(
                {
                    "package": package,
                    "installed": self._installer.is_installed(package),
                    "install_command": self._build_install_preview(manager, package),
                }
            )

        return {
            "status": "pass" if manager else "warning",
            "message": (
                f"Package manager hook ready: {manager}."
                if manager
                else "No supported package manager found for installer hooks."
            ),
            "details": {
                "manager": manager,
                "safe_mode": "Commands are prepared only; no packages were installed.",
                "packages": package_hooks,
            },
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_package_manager() -> str:
        for manager in ("winget", "choco", "apt", "brew"):
            if shutil.which(manager):
                return manager
        return ""

    @staticmethod
    def _build_install_preview(manager: str, package: str) -> str:
        if not manager:
            return ""

        mapping = {
            "winget": f"winget install --silent {package}",
            "choco": f"choco install -y {package}",
            "apt": f"apt-get install -y {package}",
            "brew": f"brew install {package}",
        }
        return mapping.get(manager, f"{manager} install {package}")

    @staticmethod
    def _summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(results)
        passed = sum(1 for result in results if result.get("status") == "pass")
        warnings = sum(1 for result in results if result.get("status") == "warning")
        errors = sum(1 for result in results if result.get("status") == "error")
        ready = errors == 0 and warnings == 0
        return {
            "ready": ready,
            "total_steps": total,
            "passed": passed,
            "warnings": warnings,
            "errors": errors,
        }

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)
