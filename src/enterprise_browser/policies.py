"""Chromium policy management."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict


class PolicyManager:
    """Ensure Chromium enterprise policies match the required configuration."""

    def __init__(self, policy_path: Path, required_policies: Dict[str, Any]) -> None:
        self._policy_path = policy_path
        self._required_policies = required_policies

    def ensure(self) -> None:
        """Create or update the policy file with the required values."""
        self._policy_path.parent.mkdir(parents=True, exist_ok=True)

        current = self._load_existing()
        updated = False

        for key, value in self._required_policies.items():
            if current.get(key) != value:
                current[key] = value
                updated = True

        if updated or not self._policy_path.exists():
            self._write(current)
            logging.info("Chromium policies updated at %s", self._policy_path)
        else:
            logging.info("Chromium policies already satisfied at %s", self._policy_path)

    def _load_existing(self) -> Dict[str, Any]:
        if not self._policy_path.exists():
            return {}

        try:
            with self._policy_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError:
            logging.warning("Invalid policy JSON detected at %s; recreating file.", self._policy_path)
            return {}

    def _write(self, data: Dict[str, Any]) -> None:
        with self._policy_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")


__all__ = ["PolicyManager"]
