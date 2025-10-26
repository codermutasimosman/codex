"""Chromium policy management."""
from __future__ import annotations

import logging
from contextlib import closing
from typing import Any, Dict, Tuple


try:  # pragma: no cover - exercised via runtime availability
    import winreg  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - running on non-Windows
    winreg = None  # type: ignore[assignment]


class PolicyManager:
    """Ensure Chromium enterprise policies match the required configuration."""

    def __init__(self, registry_hive: str, registry_path: str, required_policies: Dict[str, Any]) -> None:
        self._registry_hive_name = registry_hive
        self._registry_path = registry_path
        self._required_policies = required_policies

    def ensure(self) -> None:
        """Create or update the Windows registry with the required values."""

        module = self._require_winreg()
        hive = self._resolve_hive(module)
        access = module.KEY_READ | module.KEY_WRITE | module.KEY_SET_VALUE

        try:
            with closing(module.ConnectRegistry(None, hive)) as registry:
                with closing(module.CreateKeyEx(registry, self._registry_path, 0, access)) as key:
                    updated = self._apply_required_values(module, key)
        except PermissionError as exc:  # pragma: no cover - depends on OS permissions
            raise RuntimeError(
                "Administrator privileges are required to configure Chromium policies in the "
                f"{self._registry_hive_name}\\{self._registry_path} registry key."
            ) from exc
        except OSError as exc:  # pragma: no cover - defensive for unexpected registry errors
            raise RuntimeError(
                "Unable to update Chromium policies in the Windows registry."
            ) from exc

        location = f"{self._registry_hive_name}\\{self._registry_path}"
        if updated:
            logging.info("Chromium policies updated at %s", location)
        else:
            logging.info("Chromium policies already satisfied at %s", location)

    def _apply_required_values(self, module: Any, key: Any) -> bool:
        updated = False
        for name, value in self._required_policies.items():
            desired, value_type = self._coerce_value(module, value)
            current = self._read_current_value(module, key, name)
            if current != (desired, value_type):
                module.SetValueEx(key, name, 0, value_type, desired)
                updated = True
        return updated

    def _read_current_value(self, module: Any, key: Any, name: str) -> Tuple[Any, int] | None:
        try:
            value, value_type = module.QueryValueEx(key, name)
        except FileNotFoundError:
            return None
        return value, value_type

    def _coerce_value(self, module: Any, value: Any) -> Tuple[Any, int]:
        if isinstance(value, bool):
            return int(value), module.REG_DWORD
        if isinstance(value, int):
            return value, module.REG_DWORD
        if isinstance(value, str):
            return value, module.REG_SZ
        raise TypeError(
            f"Unsupported policy value type for registry enforcement: {type(value).__name__}"
        )

    def _resolve_hive(self, module: Any) -> Any:
        try:
            return getattr(module, self._registry_hive_name)
        except AttributeError as exc:  # pragma: no cover - defensive configuration guard
            raise ValueError(
                f"Unknown Windows registry hive '{self._registry_hive_name}'."
            ) from exc

    def _require_winreg(self) -> Any:
        if winreg is None:  # pragma: no cover - running on non-Windows
            raise RuntimeError("Windows registry access is only available on Windows platforms.")
        return winreg


__all__ = ["PolicyManager"]
