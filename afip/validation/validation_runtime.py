"""Validation runtime."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .validation_observation import ValidationObservation
from .validation_policy import ValidationPolicy
from .validation_report import ValidationReport
from .validation_repository import ValidationRepository


class ValidationRuntime:
    """Validate AI integration plans before production readiness review."""

    def __init__(
        self,
        repository: ValidationRepository | None = None,
        policy: ValidationPolicy | None = None,
    ) -> None:
        self._repository = repository or ValidationRepository()
        self._policy = policy or ValidationPolicy()

    def run(self, records: Sequence[Mapping[str, Any]]) -> ValidationReport:
        observations = tuple(ValidationObservation.from_mapping(item) for item in records)
        valid = tuple(item for item in observations if item.has_market_regime)
        invalid_market_regime_count = len(observations) - len(valid)
        profiles = self._repository.build_profiles(valid)
        decision = self._policy.decide(profiles, invalid_market_regime_count=invalid_market_regime_count)
        return ValidationReport(decision=decision, profiles=profiles)
