"""Runtime metrics integration for Production Milestone G Pack 4."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .metrics_observation import RuntimeMetricsObservation
from .metrics_policy import RuntimeMetricsPolicy
from .metrics_profile import RuntimeMetricsProfile
from .metrics_report import RuntimeMetricsReport
from .metrics_repository import RuntimeMetricsRepository


class RuntimeMetricsIntegrationRuntime:
    """Reviews runtime metrics without changing trading decisions or runtime configuration."""

    def __init__(self, policy: RuntimeMetricsPolicy | None = None, repository: RuntimeMetricsRepository | None = None) -> None:
        self.policy = policy or RuntimeMetricsPolicy()
        self.repository = repository or RuntimeMetricsRepository()

    def evaluate_one(self, record: Mapping[str, Any]) -> RuntimeMetricsProfile:
        observation = RuntimeMetricsObservation.from_mapping(record)
        reason = self.policy.evaluate_reason(observation)
        status = self.policy.status_for(observation)
        profile = RuntimeMetricsProfile.from_observation(observation, status=status, reason=reason)
        self.repository.append(profile)
        return profile

    def evaluate_many(self, records: Iterable[Mapping[str, Any]]) -> list[RuntimeMetricsProfile]:
        return [self.evaluate_one(record) for record in records]

    def explain_one(self, record: Mapping[str, Any]) -> RuntimeMetricsReport:
        return RuntimeMetricsReport(self.evaluate_one(record))

    def explain_many(self, records: Iterable[Mapping[str, Any]]) -> list[RuntimeMetricsReport]:
        return [self.explain_one(record) for record in records]
