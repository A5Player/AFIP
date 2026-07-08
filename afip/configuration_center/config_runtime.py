"""Configuration Center runtime for Milestone H Pack 2."""

from __future__ import annotations

from typing import Any, Mapping

from .config_policy import build_configuration_report
from .config_report import ConfigurationCenterReport
from .config_repository import ConfigurationRepository


class ConfigurationCenterRuntime:
    """Evaluate account and dashboard settings without changing trading logic."""

    def __init__(self, repository: ConfigurationRepository | None = None) -> None:
        self.repository = repository or ConfigurationRepository()

    def evaluate_one(self, record: Mapping[str, Any]) -> ConfigurationCenterReport:
        saved = self.repository.load()
        merged = {**saved, **dict(record)}
        return build_configuration_report(merged)

    def explain_one(self, record: Mapping[str, Any]) -> ConfigurationCenterReport:
        return self.evaluate_one(record)

    def preview_save(self, config: Mapping[str, Any]) -> ConfigurationCenterReport:
        """Preview a config save deterministically without persisting it."""
        return build_configuration_report(config)
