"""Runtime observability execution facade."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Tuple

from .explainability_report import RuntimeExplainabilityReport
from .metrics_observation import RuntimeObservabilityObservation
from .metrics_profile import RuntimeObservabilityProfile
from .observability_policy import RuntimeObservabilityPolicy
from .observability_repository import RuntimeObservabilityRepository


class RuntimeObservabilityRuntime:
    """Evaluate runtime metrics and build deterministic explainability reports."""

    def __init__(self, policy: RuntimeObservabilityPolicy | None = None) -> None:
        self.policy = policy or RuntimeObservabilityPolicy()

    def evaluate_one(self, value: Mapping[str, Any]) -> RuntimeObservabilityProfile:
        observation = RuntimeObservabilityObservation.from_mapping(value)
        return self.policy.evaluate(observation)

    def evaluate_many(self, values: Iterable[Mapping[str, Any]]) -> RuntimeObservabilityRepository:
        repository = RuntimeObservabilityRepository()
        for value in values:
            repository.add(self.evaluate_one(value))
        return repository

    def explain_one(self, value: Mapping[str, Any]) -> RuntimeExplainabilityReport:
        return RuntimeExplainabilityReport.from_profile(self.evaluate_one(value))

    def explain_many(self, values: Iterable[Mapping[str, Any]]) -> Tuple[RuntimeExplainabilityReport, ...]:
        return tuple(RuntimeExplainabilityReport.from_profile(profile) for profile in self.evaluate_many(values).all())
