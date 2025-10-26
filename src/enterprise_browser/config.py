"""Configuration objects for the enterprise browser utility."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Tuple


def _local_app_data() -> Path:
    """Return the best-effort LOCALAPPDATA directory for Windows."""

    override = os.environ.get("LOCALAPPDATA")
    if override:
        return Path(override)
    # Fall back to the standard Windows user directory layout.
    return Path.home() / "AppData" / "Local"


def _default_playwright_cache() -> Path:
    """Return the standard ms-playwright cache directory on Windows."""

    return _local_app_data() / "ms-playwright"


@dataclass(frozen=True)
class PolicyConfig:
    """Runtime configuration describing Chromium policies and launch options."""

    registry_hive: str = "HKEY_LOCAL_MACHINE"
    registry_path: str = r"Software\Policies\Chromium"
    required_policies: Dict[str, Any] = field(
        default_factory=lambda: {
            "DeveloperToolsAvailability": 2,
            "DisableAutoUpdateChecksCheckboxValue": True,
            "IncognitoModeAvailability": 2,
        }
    )
    playwright_cache: Path = field(default_factory=_default_playwright_cache)
    launch_url: str = "about:blank"
    launch_timeout_ms: int = 3_000
    headless: bool = False
    launch_args: Tuple[str, ...] = ("--incognito",)
    stealth_enabled: bool = True


__all__ = ["PolicyConfig"]
