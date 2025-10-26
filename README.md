# codex

This repository contains a small Playwright-based utility that ensures Chromium is installed with enterprise policies before launching the browser.

## Prerequisites

Install the Python dependencies and the Chromium browser binary used by Playwright:

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

Run the application to verify the Chromium installation, enforce the required policies, and launch the browser:

```bash
python app.py
```

The script ensures the following Chromium enterprise policies exist at `/etc/chromium/policies/managed/policy.json`:

- `DeveloperToolsAvailability` set to `2` to disable DevTools.
- `DisableAutoUpdateChecksCheckboxValue` set to `true` to disable update checks.
- `IncognitoModeAvailability` set to `1` to enforce incognito-only mode.

When the browser starts, it opens a blank tab for a few seconds and then closes automatically.
