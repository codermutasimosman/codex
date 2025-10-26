"""Chromium installation helpers."""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path


class ChromiumInstaller:
    """Install and verify the Playwright Chromium binary."""

    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = cache_dir

    def is_installed(self) -> bool:
        """Return ``True`` when Chromium binaries already exist."""
        return any(self._cache_dir.glob("chromium-*"))

    def install(self) -> None:
        """Install Chromium using Playwright's bundled installer."""
        logging.info("Installing Playwright Chromium binaries…")
        try:
            subprocess.run(["playwright", "install", "chromium"], check=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            logging.error("Playwright installation failed: %s", exc)
            raise RuntimeError("Unable to install Chromium for Playwright") from exc


__all__ = ["ChromiumInstaller"]
