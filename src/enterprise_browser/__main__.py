"""Command-line entrypoint for the enterprise browser utility."""
from __future__ import annotations

import logging

from .app import build_app

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main() -> None:
    """Execute the enterprise Chromium policy workflow."""
    app = build_app()
    app.run()


if __name__ == "__main__":
    main()
