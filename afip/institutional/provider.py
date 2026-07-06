"""Provider contracts for institutional positioning data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping, Protocol


@dataclass(frozen=True)
class InstitutionalProviderResult:
    """Normalized institutional data returned by a free or paid provider."""

    status: str
    source: str
    observed_at: datetime
    values: Mapping[str, float] = field(default_factory=dict)
    reason: str = "institutional_provider_ready"

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "source": self.source,
            "observed_at": self.observed_at.isoformat(),
            "values": dict(self.values),
            "reason": self.reason,
        }


class InstitutionalDataProvider(Protocol):
    """Read institutional positioning data from a configured provider."""

    def fetch_values(self, observed_at: datetime | None = None) -> InstitutionalProviderResult:
        """Return normalized institutional positioning values."""


class EmptyInstitutionalDataProvider:
    """Safe fallback when no institutional data source is configured."""

    def fetch_values(self, observed_at: datetime | None = None) -> InstitutionalProviderResult:
        observed_at = observed_at or datetime.now(timezone.utc)
        return InstitutionalProviderResult(
            status="INSTITUTIONAL_PROVIDER_EMPTY",
            source="EMPTY_INSTITUTIONAL_PROVIDER",
            observed_at=observed_at,
            values={},
            reason="no_institutional_provider_configured",
        )


class StaticInstitutionalDataProvider:
    """Deterministic provider used by tests, replay, and offline research."""

    def __init__(self, values: Mapping[str, object] | None = None, source: str = "STATIC_INSTITUTIONAL_DATA") -> None:
        self._values = {str(key): self._to_float(value) for key, value in (values or {}).items()}
        self._source = source

    def fetch_values(self, observed_at: datetime | None = None) -> InstitutionalProviderResult:
        observed_at = observed_at or datetime.now(timezone.utc)
        return InstitutionalProviderResult(
            status="INSTITUTIONAL_PROVIDER_READY",
            source=self._source,
            observed_at=observed_at,
            values=dict(self._values),
            reason="static_institutional_provider_ready",
        )

    @staticmethod
    def _to_float(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
