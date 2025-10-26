import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict

from playwright.sync_api import Playwright, sync_playwright

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

BROWSER_CACHE = Path.home() / ".cache" / "ms-playwright"
POLICY_PATH = Path("/etc/chromium/policies/managed/policy.json")
REQUIRED_POLICIES: Dict[str, Any] = {
    "DeveloperToolsAvailability": 2,  # Disable developer tools
    "DisableAutoUpdateChecksCheckboxValue": True,  # Disable update checks
    "IncognitoModeAvailability": 1,  # Force incognito mode
}


def is_chromium_installed() -> bool:
    return any(BROWSER_CACHE.glob("chromium-*"))


def install_chromium() -> None:
    logging.info("Chromium binaries for Playwright were not found. Installing...")
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except subprocess.CalledProcessError as exc:
        logging.error("Failed to install Chromium via Playwright: %s", exc)
        raise RuntimeError("Unable to install Chromium for Playwright") from exc


def load_existing_policies(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.warning("Existing policy file is not valid JSON. It will be replaced.")
        return {}


def ensure_policies(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    policies = load_existing_policies(path)
    updated = False

    for key, value in REQUIRED_POLICIES.items():
        if policies.get(key) != value:
            policies[key] = value
            updated = True

    if updated or not path.exists():
        with path.open("w", encoding="utf-8") as f:
            json.dump(policies, f, indent=2, sort_keys=True)
            f.write("\n")
        logging.info("Policies have been updated at %s", path)
    else:
        logging.info("Required policies are already configured at %s", path)


def launch_browser(playwright: Playwright) -> None:
    logging.info("Launching Chromium with enforced policies.")
    browser = playwright.chromium.launch(headless=True, args=["--incognito"])
    context = browser.new_context()
    page = context.new_page()
    page.goto("about:blank")
    logging.info("Chromium launched successfully. Closing after a short delay.")
    page.wait_for_timeout(3000)
    browser.close()


def main() -> None:
    if not is_chromium_installed():
        install_chromium()
    else:
        logging.info("Chromium binaries are already installed for Playwright.")

    ensure_policies(POLICY_PATH)

    with sync_playwright() as playwright:
        launch_browser(playwright)


if __name__ == "__main__":
    main()
