"""Browser launch utilities."""
from __future__ import annotations

import logging
from typing import Iterable

from playwright.sync_api import Browser, BrowserContext, Playwright

from patchright import apply_stealth_sync


class ChromiumLauncher:
    """Launch Chromium via Playwright with enterprise policies applied."""

    def __init__(
        self,
        headless: bool,
        launch_args: Iterable[str],
        launch_url: str,
        timeout_ms: int,
        *,
        enable_stealth: bool,
    ) -> None:
        self._headless = headless
        self._launch_args = tuple(launch_args)
        self._launch_url = launch_url
        self._timeout_ms = timeout_ms
        self._enable_stealth = enable_stealth

    def launch(self, playwright: Playwright) -> None:
        """Launch Chromium and visit the configured URL."""
        logging.info("Launching Chromium with policies enforced.")
        browser = playwright.chromium.launch(headless=self._headless, args=list(self._launch_args))
        context: BrowserContext | None = None
        try:
            context = self._open_initial_page(browser)
            logging.info("Chromium launched successfully; close the window to exit.")
            browser.wait_for_event("disconnected")
        except Exception:
            if context is not None:
                context.close()
            browser.close()
            raise

    def _open_initial_page(self, browser: Browser) -> BrowserContext:
        context = browser.new_context()
        if self._enable_stealth:
            apply_stealth_sync(context)
        page = context.new_page()
        page.goto(self._launch_url)
        if self._timeout_ms:
            logging.info("Initial wait %sms before handing over control.", self._timeout_ms)
            page.wait_for_timeout(self._timeout_ms)
        return context


__all__ = ["ChromiumLauncher"]
