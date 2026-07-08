"""Walk-forward historical paper simulation runtime for Production Freeze Pack P5."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .walk_observation import WalkForwardObservation
from .walk_policy import WalkForwardPolicy
from .walk_profile import WalkForwardProfile
from .walk_report import WalkForwardReport
from .walk_repository import WalkForwardRepository


class WalkForwardRuntime:
    """Evaluates no-lookahead historical paper simulations without changing trading decisions."""

    def __init__(self, policy: WalkForwardPolicy | None = None, repository: WalkForwardRepository | None = None) -> None:
        self.policy = policy or WalkForwardPolicy()
        self.repository = repository or WalkForwardRepository()

    def evaluate_one(self, record: Mapping[str, Any]) -> WalkForwardProfile:
        observation = WalkForwardObservation.from_mapping(record)
        reason = self.policy.evaluate_reason(observation)
        status = self.policy.status_for(observation)
        profile = WalkForwardProfile.from_observation(observation, status=status, reason=reason)
        self.repository.append(profile)
        return profile

    def evaluate_many(self, records: Iterable[Mapping[str, Any]]) -> list[WalkForwardProfile]:
        return [self.evaluate_one(record) for record in records]

    def explain_one(self, record: Mapping[str, Any]) -> WalkForwardReport:
        return WalkForwardReport(self.evaluate_one(record))
