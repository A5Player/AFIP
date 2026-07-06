"""Runtime integration for provider management and data quality."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping, Sequence

from afip.provider_management.data_quality_assessment import DataQualityAssessment
from afip.provider_management.provider_health import ProviderHealthRecord
from afip.provider_management.provider_registry import ProviderRegistry
from afip.provider_management.provider_router import ProviderRouter


@dataclass
class ProviderManagementRuntime:
    """Build a provider route, ranking, and data quality state."""

    records: Sequence[ProviderHealthRecord] = field(default_factory=tuple)
    required_fields: tuple[str, ...] = ()
    max_age_seconds: float = 900.0

    def run_dict(
        self,
        values: Mapping[str, object] | None = None,
        observed_at: datetime | None = None,
        preferred_provider: str | None = None,
        now: datetime | None = None,
    ) -> dict[str, object]:
        registry = ProviderRegistry()
        registry.extend(self.records)
        route = ProviderRouter(registry).route(preferred_provider=preferred_provider)
        quality = DataQualityAssessment(
            required_fields=self.required_fields,
            max_age_seconds=self.max_age_seconds,
        ).assess(values or {}, observed_at=observed_at, now=now)

        if route.decision == "UNAVAILABLE" or quality.decision == "BLOCKED":
            status = "PROVIDER_MANAGEMENT_REVIEW"
            decision = "REVIEW_ONLY"
            reason = "provider_or_data_quality_review_required"
        elif route.decision == "REVIEW" or quality.decision == "REVIEW":
            status = "PROVIDER_MANAGEMENT_REVIEW"
            decision = "REVIEW_ONLY"
            reason = "provider_management_review_only"
        else:
            status = "PROVIDER_MANAGEMENT_READY"
            decision = "READY"
            reason = "provider_management_ready"

        return {
            "status": status,
            "decision": decision,
            "route": route.as_dict(),
            "registry": registry.as_dict(),
            "data_quality": quality.as_dict(),
            "reason": reason,
        }
