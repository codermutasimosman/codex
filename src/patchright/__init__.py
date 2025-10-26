"""Lightweight stealth helpers for Playwright Chromium sessions.

This module emulates the public API of the third-party ``patchright``
package, providing a local implementation that hardens Playwright-driven
Chromium instances against common bot-detection heuristics.  The helper is
kept deliberately small so it can ship with the project without requiring
external downloads during deployment.
"""
from __future__ import annotations

from playwright.sync_api import BrowserContext

__all__ = ["apply_stealth_sync"]


_STEALTH_INIT_SCRIPT = """
// Basic Playwright stealth adjustments derived from the upstream
// patchright project.  The goal is not perfect undetectability, but to
// neutralise the easiest automation fingerprints.
(() => {
  const originalQuery = window.navigator.permissions.query;
  window.navigator.permissions.query = (parameters) => (
    parameters && parameters.name === 'notifications'
      ? Promise.resolve({ state: Notification.permission })
      : originalQuery(parameters)
  );

  // Pretend to be a normal Chrome install by exposing a chrome object.
  if (!window.chrome) {
    window.chrome = {
      runtime: {},
    };
  }

  // Override the languages list to match a typical Chromium install.
  Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en'],
  });

  // Remove the webdriver flag Playwright sets when controlling Chromium.
  Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
  });

  // Fake a standard plugins array.
  Object.defineProperty(navigator, 'plugins', {
    get: () => [
      { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
      { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
    ],
  });
})();
"""


def apply_stealth_sync(context: BrowserContext) -> None:
    """Inject stealth JavaScript for each page created in ``context``."""

    context.add_init_script(_STEALTH_INIT_SCRIPT)
