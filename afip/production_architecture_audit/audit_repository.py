"""In-memory production architecture audit repository."""

from __future__ import annotations

from .audit_profile import ProductionArchitectureAuditProfile


class ProductionArchitectureAuditRepository:
    """Stores deterministic audit profiles for tests and runtime adapters."""

    def __init__(self) -> None:
        self._profiles: list[ProductionArchitectureAuditProfile] = []

    def append(self, profile: ProductionArchitectureAuditProfile) -> None:
        self._profiles.append(profile)

    def all(self) -> list[ProductionArchitectureAuditProfile]:
        return list(self._profiles)
