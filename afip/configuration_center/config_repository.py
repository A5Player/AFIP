"""Deterministic in-memory configuration repository for dashboard settings."""

from __future__ import annotations

from typing import Any, Mapping


class ConfigurationRepository:
    """Simple repository used by dashboard settings and tests.

    This repository intentionally avoids file writes in Pack H2. A later UI pack can
    wire persistence after the schema is stable.
    """

    def __init__(self, initial: Mapping[str, Any] | None = None) -> None:
        self._snapshot: dict[str, Any] = dict(initial or {})

    def load(self) -> dict[str, Any]:
        return dict(self._snapshot)

    def save(self, config: Mapping[str, Any]) -> dict[str, Any]:
        self._snapshot = dict(config)
        return self.load()
