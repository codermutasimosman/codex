"""Configuration objects for the enterprise browser utility."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class PolicyConfig:
    """Runtime configuration describing Chromium policies and launch options."""

    policy_path: Path = Path("/etc/chromium/policies/managed/policy.json")
    required_policies: Dict[str, Any] = field(
        default_factory=lambda: {
            "DeveloperToolsAvailability": 2,
            "DisableAutoUpdateChecksCheckboxValue": True,
            "IncognitoModeAvailability": 1,
        }
    )
    playwright_cache: Path = Path.home() / ".cache" / "ms-playwright"
    launch_url: str = "about:blank"
    launch_timeout_ms: int = 3_000
    headless: bool = True
    launch_args: Tuple[str, ...] = ("--incognito",)


__all__ = ["PolicyConfig"]
