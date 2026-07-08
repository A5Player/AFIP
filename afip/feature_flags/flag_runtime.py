"""Feature flag runtime for Production Milestone G Pack 3."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .flag_observation import FeatureFlagObservation
from .flag_policy import FeatureFlagPolicy
from .flag_profile import FeatureFlagProfile
from .flag_report import FeatureFlagReport
from .flag_repository import FeatureFlagRepository


class FeatureFlagRuntime:
    """Reviews feature flag records without writing configuration or changing trading decisions."""

    def __init__(self, policy: FeatureFlagPolicy | None = None, repository: FeatureFlagRepository | None = None) -> None:
        self.policy = policy or FeatureFlagPolicy()
        self.repository = repository or FeatureFlagRepository()

    def evaluate_one(self, record: Mapping[str, Any]) -> FeatureFlagProfile:
        observation = FeatureFlagObservation.from_mapping(record)
        reason = self.policy.evaluate_reason(observation)
        status = self.policy.status_for(observation)
        profile = FeatureFlagProfile.from_observation(observation, status=status, reason=reason)
        self.repository.append(profile)
        return profile

    def evaluate_many(self, records: Iterable[Mapping[str, Any]]) -> list[FeatureFlagProfile]:
        return [self.evaluate_one(record) for record in records]

    def explain_one(self, record: Mapping[str, Any]) -> FeatureFlagReport:
        return FeatureFlagReport(self.evaluate_one(record))

    def explain_many(self, records: Iterable[Mapping[str, Any]]) -> list[FeatureFlagReport]:
        return [self.explain_one(record) for record in records]
