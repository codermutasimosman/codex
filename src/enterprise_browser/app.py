"""Application composition for the enterprise Chromium utility."""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator, TYPE_CHECKING

from playwright.sync_api import sync_playwright

from .config import PolicyConfig
from .installer import ChromiumInstaller
from .launcher import ChromiumLauncher
from .policies import PolicyManager


if TYPE_CHECKING:
    from playwright.sync_api import Playwright


class ChromiumPolicyApp:
    """Coordinate Chromium installation, policy enforcement, and launch."""

    def __init__(
        self,
        installer: ChromiumInstaller,
        policy_manager: PolicyManager,
        launcher: ChromiumLauncher,
    ) -> None:
        self._installer = installer
        self._policy_manager = policy_manager
        self._launcher = launcher

    def run(self) -> None:
        """Execute the full application workflow."""
        if not self._installer.is_installed():
            self._installer.install()
        else:
            logging.info("Playwright Chromium already installed.")

        self._policy_manager.ensure()

        with self._playwright() as playwright:
            self._launcher.launch(playwright)

    @staticmethod
    @contextmanager
    def _playwright() -> Iterator["Playwright"]:
        with sync_playwright() as playwright:
            yield playwright


def build_app(config: PolicyConfig | None = None) -> ChromiumPolicyApp:
    """Factory for a preconfigured :class:`ChromiumPolicyApp`."""
    config = config or PolicyConfig()
    installer = ChromiumInstaller(cache_dir=config.playwright_cache)
    policy_manager = PolicyManager(
        registry_hive=config.registry_hive,
        registry_path=config.registry_path,
        required_policies=dict(config.required_policies),
    )
    launcher = ChromiumLauncher(
        headless=config.headless,
        launch_args=config.launch_args,
        launch_url=config.launch_url,
        timeout_ms=config.launch_timeout_ms,
    )
    return ChromiumPolicyApp(installer, policy_manager, launcher)


__all__ = ["ChromiumPolicyApp", "build_app"]
