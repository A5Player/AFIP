"""Compatibility acceptance assessment for AFIP Production Milestone A Pack 13."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


def _ratio(value: float) -> float:
    """Return a bounded ratio for compatibility scoring."""
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class CompatibilityAcceptanceResult:
    """Compatibility acceptance result for additive production modules."""

    acceptance_score: float
    status: str
    action: str
    reason: str


class CompatibilityAcceptanceAssessment:
    """Assess backward compatibility and CI alignment for release acceptance."""

    def assess(self, metrics: Mapping[str, float]) -> CompatibilityAcceptanceResult:
        """Return compatibility acceptance without changing existing runtime behavior."""
        api_stability = _ratio(metrics.get("api_stability", 0.50))
        import_stability = _ratio(metrics.get("import_stability", 0.50))
        ci_alignment = _ratio(metrics.get("ci_alignment", 0.50))
        simulation_continuity = _ratio(metrics.get("simulation_continuity", 0.50))
        additive_design = _ratio(metrics.get("additive_design", 0.50))
        compatibility_pressure = _ratio(metrics.get("compatibility_pressure", 0.50))

        raw_score = (
            api_stability * 0.20
            + import_stability * 0.18
            + ci_alignment * 0.20
            + simulation_continuity * 0.20
            + additive_design * 0.22
        )
        acceptance_score = _ratio(raw_score * (1.0 - compatibility_pressure * 0.28))

        if acceptance_score >= 0.84 and compatibility_pressure <= 0.18:
            status = "COMPATIBILITY_ACCEPTED"
            action = "ACCEPT_RELEASE_COMPATIBILITY"
            reason = "compatibility_acceptance_supports_release"
        elif acceptance_score >= 0.66:
            status = "COMPATIBILITY_REVIEW"
            action = "CONTINUE_COMPATIBILITY_VALIDATION"
            reason = "compatibility_acceptance_requires_review"
        else:
            status = "COMPATIBILITY_NOT_ACCEPTED"
            action = "KEEP_RELEASE_IN_SIMULATION"
            reason = "compatibility_acceptance_below_threshold"

        return CompatibilityAcceptanceResult(
            acceptance_score=round(acceptance_score, 4),
            status=status,
            action=action,
            reason=reason,
        )
