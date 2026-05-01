"""Hybrid internal/external configuration loading for PocketMedic."""

import json
import os
import platform
from copy import deepcopy
from typing import Any, Dict, List, Optional

from Core.Paths import app_path, find_resource


EXTERNAL_DATA_DIR = "PocketMedic_Data"
EXTRA_PACKAGES = "ExtraPackages.json"
USER_SETTINGS = "UserSettings.json"
MACHINE_OVERRIDES = "MachineOverrides.json"


class ConfigManager:
    """Load bundled defaults and optional user-editable external config."""

    def __init__(self, logger=None):
        self._logger = logger
        self.loaded_sources: List[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_settings(self) -> Dict[str, Any]:
        """Load Global.Settings plus external user and machine overrides."""
        settings = self._load_internal_json("Config/Global.Settings.json")
        settings = self._merge_dicts(settings, self._load_external_json(USER_SETTINGS))
        settings = self._merge_dicts(settings, self._load_machine_overrides())
        return settings

    def load_package_definitions(self, path: str = "Config/Package.Definitions.json") -> List[Dict[str, Any]]:
        """Load bundled package definitions and external package additions."""
        base_data = self._load_internal_json(path)
        base_packages = base_data.get("packages", [])
        if not isinstance(base_packages, list):
            self._warning(f"Warning: package definitions must be a list in {path!r}.")
            base_packages = []

        extra_data = self._load_external_json(EXTRA_PACKAGES)
        extra_packages = extra_data.get("packages", [])
        if extra_data and not isinstance(extra_packages, list):
            self._warning(f"Warning: external package definitions must be a list in {EXTRA_PACKAGES}.")
            extra_packages = []

        return self._merge_packages(base_packages, extra_packages)

    def external_data_dir(self) -> str:
        """Return the external user-editable data directory beside the app."""
        return app_path(EXTERNAL_DATA_DIR)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_internal_json(self, relative_path: str) -> Dict[str, Any]:
        path = find_resource(relative_path)
        data = self._read_json(path)
        if data is None:
            self._warning(f"Warning: internal config missing or invalid: {path}")
            return {}

        self._record_source("internal", path)
        return data

    def _load_external_json(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.external_data_dir(), filename)
        if not os.path.exists(path):
            self._log(f"External config not found, using defaults: {path}")
            return {}

        data = self._read_json(path)
        if data is None:
            self._warning(f"Warning: external config invalid: {path}")
            return {}

        self._record_source("external", path)
        return data

    def _load_machine_overrides(self) -> Dict[str, Any]:
        data = self._load_external_json(MACHINE_OVERRIDES)
        if not data:
            return {}

        machine_name = platform.node()
        machines = data.get("machines", {})
        if isinstance(machines, dict) and machine_name in machines:
            overrides = machines[machine_name]
            return overrides if isinstance(overrides, dict) else {}

        default_overrides = data.get("defaults", {})
        return default_overrides if isinstance(default_overrides, dict) else {}

    def _read_json(self, path: str) -> Optional[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8") as file_handle:
                data = json.load(file_handle)
            return data if isinstance(data, dict) else None
        except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
            self._warning(f"Warning: failed to load config {path!r}: {exc}")
            return None

    def _record_source(self, source_type: str, path: str) -> None:
        label = f"{source_type}: {path}"
        self.loaded_sources.append(label)
        self._log(f"Loaded config source: {label}")

    @staticmethod
    def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        merged = deepcopy(base)
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = ConfigManager._merge_dicts(merged[key], value)
            else:
                merged[key] = deepcopy(value)
        return merged

    @staticmethod
    def _merge_packages(base: List[Dict[str, Any]], extra: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        by_key: Dict[str, Dict[str, Any]] = {}
        order: List[str] = []

        for package in base + extra:
            key = package.get("key")
            if not key:
                continue
            if key not in by_key:
                order.append(key)
                by_key[key] = deepcopy(package)
            else:
                by_key[key] = ConfigManager._merge_dicts(by_key[key], package)

        return [by_key[key] for key in order]

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)

    def _warning(self, message: str) -> None:
        if self._logger:
            self._logger.warning(message)
