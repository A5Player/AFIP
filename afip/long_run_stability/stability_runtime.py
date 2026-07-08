"""Long-run stability runtime for Production Milestone G Pack 7."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .stability_observation import LongRunStabilityObservation
from .stability_policy import LongRunStabilityPolicy
from .stability_profile import LongRunStabilityProfile
from .stability_report import LongRunStabilityReport
from .stability_repository import LongRunStabilityRepository


class LongRunStabilityRuntime:
    """Evaluates long-run stability without changing trading decisions or live execution."""

    def __init__(self, policy: LongRunStabilityPolicy | None = None, repository: LongRunStabilityRepository | None = None) -> None:
        self.policy = policy or LongRunStabilityPolicy()
        self.repository = repository or LongRunStabilityRepository()

    def evaluate_one(self, record: Mapping[str, Any]) -> LongRunStabilityProfile:
        observation = LongRunStabilityObservation.from_mapping(record)
        reason = self.policy.evaluate_reason(observation)
        status = self.policy.status_for(observation)
        profile = LongRunStabilityProfile.from_observation(observation, status=status, reason=reason)
        self.repository.append(profile)
        return profile

    def evaluate_many(self, records: Iterable[Mapping[str, Any]]) -> list[LongRunStabilityProfile]:
        return [self.evaluate_one(record) for record in records]

    def explain_one(self, record: Mapping[str, Any]) -> LongRunStabilityReport:
        return LongRunStabilityReport(self.evaluate_one(record))

    def explain_many(self, records: Iterable[Mapping[str, Any]]) -> list[LongRunStabilityReport]:
        return [self.explain_one(record) for record in records]
