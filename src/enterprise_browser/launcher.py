"""Browser launch utilities."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

from playwright.sync_api import BrowserContext, Playwright

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
        profile_dir: Path,
        browser_channel: str,
        no_viewport: bool,
        ignore_default_args: Iterable[str],
    ) -> None:
        self._headless = headless
        self._launch_args = tuple(launch_args)
        self._launch_url = launch_url
        self._timeout_ms = timeout_ms
        self._enable_stealth = enable_stealth
        self._profile_dir = profile_dir
        self._browser_channel = browser_channel
        self._no_viewport = no_viewport
        self._ignore_default_args = tuple(ignore_default_args)

    def launch(self, playwright: Playwright) -> None:
        """Launch Chromium and visit the configured URL."""
        logging.info("Launching Chromium with policies enforced.")
        user_data_dir = self._profile_dir.resolve()
        user_data_dir.mkdir(parents=True, exist_ok=True)
        context: BrowserContext | None = None
        try:
            context = playwright.chromium.launch_persistent_context(
                str(user_data_dir),
                channel=self._browser_channel,
                headless=self._headless,
                no_viewport=self._no_viewport,
                args=list(self._launch_args),
                ignore_default_args=list(self._ignore_default_args),
            )
            self._prepare_context(context)
            logging.info("Chromium launched successfully; close the window to exit.")
            browser = context.browser
            if browser is not None:
                browser.wait_for_event("disconnected")
            else:
                context.wait_for_event("close")
        except Exception:
            if context is not None:
                context.close()
            raise

    def _prepare_context(self, context: BrowserContext) -> None:
        if self._enable_stealth:
            apply_stealth_sync(context)
        page = context.new_page()
        page.goto(self._launch_url)
        if self._timeout_ms:
            logging.info("Initial wait %sms before handing over control.", self._timeout_ms)
            page.wait_for_timeout(self._timeout_ms)
        page.bring_to_front()


__all__ = ["ChromiumLauncher"]
