"""Runtime path helpers for source and PyInstaller builds."""

import os
import sys


def is_frozen() -> bool:
    """Return True when running from a bundled executable."""
    return bool(getattr(sys, "frozen", False))


def project_root() -> str:
    """Return the source checkout root."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_root() -> str:
    """Return the root used for bundled read-only resources."""
    if is_frozen():
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return project_root()


def app_root() -> str:
    """Return the root used for writable runtime files."""
    if is_frozen():
        return os.path.dirname(sys.executable)
    return project_root()


def resource_path(*parts: str) -> str:
    """Build a path under the bundled/source resource root."""
    return os.path.join(resource_root(), *parts)


def app_path(*parts: str) -> str:
    """Build a path under the writable application root."""
    return os.path.join(app_root(), *parts)


def resolve_resource(path: str) -> str:
    """Resolve relative paths against bundled/source resources."""
    if os.path.isabs(path):
        return path
    return resource_path(path)


def resolve_app(path: str) -> str:
    """Resolve relative paths against the writable application root."""
    if os.path.isabs(path):
        return path
    return app_path(path)
