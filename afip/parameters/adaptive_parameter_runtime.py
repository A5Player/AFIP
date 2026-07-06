"""Production Milestone C Pack 13 adaptive parameter runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from afip.parameters.parameter_observation import ParameterObservation
from afip.parameters.parameter_quality import ParameterQualityAssessment
from afip.parameters.parameter_repository import ParameterRepository


@dataclass(frozen=True)
class AdaptiveParameterRuntimeState:
    status: str
    repository: dict[str, Any]
    selected_profile: dict[str, Any] | None
    quality: dict[str, Any]
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "repository": self.repository,
            "selected_profile": self.selected_profile,
            "quality": self.quality,
            "reason": self.reason,
        }


class AdaptiveParameterRuntime:
    """Build deterministic adaptive parameter state from observed outcomes."""

    def __init__(self, quality: ParameterQualityAssessment | None = None) -> None:
        self.quality = quality or ParameterQualityAssessment()

    def run(self, observations: Iterable[ParameterObservation]) -> AdaptiveParameterRuntimeState:
        repository = ParameterRepository()
        for observation in observations:
            repository.observe(observation)

        data = repository.as_dict()
        best = repository.ranked()[0] if repository.ranked() else None
        quality = self.quality.assess(best)
        selected = best.as_dict() if best is not None else None
        if best is None:
            status = "ADAPTIVE_PARAMETER_REVIEW"
            reason = "no_parameter_observations"
        elif quality.approved:
            status = "ADAPTIVE_PARAMETER_READY"
            reason = "adaptive_parameter_profile_research_ready"
        else:
            status = "ADAPTIVE_PARAMETER_REVIEW"
            reason = "adaptive_parameter_profile_observe_only"
        return AdaptiveParameterRuntimeState(status, data, selected, quality.as_dict(), reason)
