# codex

This project provides a modular, object-oriented utility that verifies the Playwright Chromium binary, enforces mandatory enterprise policies, and launches the browser in incognito-only mode.

## Project layout

```
├── requirements.txt        # Runtime dependencies
└── src/
    └── enterprise_browser/
        ├── __main__.py     # CLI entrypoint (`python -m enterprise_browser`)
        ├── app.py          # Application composition and wiring
        ├── config.py       # Configuration dataclasses
        ├── installer.py    # Playwright Chromium installation helpers
        ├── launcher.py     # Chromium launch orchestration
        └── policies.py     # Enterprise policy management
```

Each module contains a dedicated class that handles one responsibility so the workflow is easy to test, extend, or replace.

## Prerequisites

Install the dependencies and Playwright's Chromium binary:

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

Execute the high-level workflow via the module entrypoint:

```bash
python -m enterprise_browser
```

The application ensures `/etc/chromium/policies/managed/policy.json` contains the following policies before launching Chromium:

- `DeveloperToolsAvailability` set to `2` to disable DevTools.
- `DisableAutoUpdateChecksCheckboxValue` set to `true` to disable update checks.
- `IncognitoModeAvailability` set to `1` to enforce incognito-only mode.

Chromium starts in headless mode, opens a blank tab, and remains active briefly so the policies can be verified in action.
