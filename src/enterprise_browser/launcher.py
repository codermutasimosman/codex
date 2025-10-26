"""Browser launch utilities."""
from __future__ import annotations

import logging
from typing import Iterable

from playwright.sync_api import Browser, Playwright


class ChromiumLauncher:
    """Launch Chromium via Playwright with enterprise policies applied."""

    def __init__(
        self,
        headless: bool,
        launch_args: Iterable[str],
        launch_url: str,
        timeout_ms: int,
    ) -> None:
        self._headless = headless
        self._launch_args = tuple(launch_args)
        self._launch_url = launch_url
        self._timeout_ms = timeout_ms

    def launch(self, playwright: Playwright) -> None:
        """Launch Chromium and visit the configured URL."""
        logging.info("Launching Chromium with policies enforced.")
        browser = playwright.chromium.launch(headless=self._headless, args=list(self._launch_args))
        try:
            self._open_initial_page(browser)
        finally:
            browser.close()

    def _open_initial_page(self, browser: Browser) -> None:
        context = browser.new_context()
        try:
            page = context.new_page()
            page.goto(self._launch_url)
            logging.info("Chromium launched successfully; waiting %sms before exit.", self._timeout_ms)
            page.wait_for_timeout(self._timeout_ms)
        finally:
            context.close()


__all__ = ["ChromiumLauncher"]
