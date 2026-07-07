"""Configuration version evidence helper for Production Milestone G Pack 2."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfigurationVersionRecord:
    """Small immutable configuration version record for rollback-aware reporting."""

    current_version: str
    previous_version: str
    rollback_available: bool

    @property
    def changed(self) -> bool:
        return self.current_version != self.previous_version

    @property
    def rollback_status(self) -> str:
        if not self.changed:
            return "ROLLBACK_NOT_REQUIRED"
        if self.rollback_available:
            return "ROLLBACK_READY"
        return "ROLLBACK_REVIEW_REQUIRED"
