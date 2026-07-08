"""Paper trading runtime for Production Milestone G Pack 6."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .paper_observation import PaperTradingObservation
from .paper_policy import PaperTradingPolicy
from .paper_profile import PaperTradingProfile
from .paper_report import PaperTradingReport
from .paper_repository import PaperTradingRepository


class PaperTradingRuntime:
    """Evaluates paper trading readiness without creating live orders."""

    def __init__(self, policy: PaperTradingPolicy | None = None, repository: PaperTradingRepository | None = None) -> None:
        self.policy = policy or PaperTradingPolicy()
        self.repository = repository or PaperTradingRepository()

    def evaluate_one(self, record: Mapping[str, Any]) -> PaperTradingProfile:
        observation = PaperTradingObservation.from_mapping(record)
        reason = self.policy.evaluate_reason(observation)
        status = self.policy.status_for(observation)
        profile = PaperTradingProfile.from_observation(observation, status=status, reason=reason)
        self.repository.append(profile)
        return profile

    def evaluate_many(self, records: Iterable[Mapping[str, Any]]) -> list[PaperTradingProfile]:
        return [self.evaluate_one(record) for record in records]

    def explain_one(self, record: Mapping[str, Any]) -> PaperTradingReport:
        return PaperTradingReport(self.evaluate_one(record))

    def explain_many(self, records: Iterable[Mapping[str, Any]]) -> list[PaperTradingReport]:
        return [self.explain_one(record) for record in records]
