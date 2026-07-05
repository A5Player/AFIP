"""Runtime health assessment for AFIP Production Milestone A Pack 12."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


def _ratio(value: float) -> float:
    """Return a bounded ratio for production-safe calculations."""
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class RuntimeHealthResult:
    """Runtime operating quality for adaptive intelligence integration."""

    health_score: float
    status: str
    action: str
    reason: str


class RuntimeHealthAssessment:
    """Assess runtime quality without modifying existing AFIP execution flow."""

    def assess(self, metrics: Mapping[str, float]) -> RuntimeHealthResult:
        """Return runtime health for production readiness evaluation."""
        data_availability = _ratio(metrics.get("data_availability", 0.50))
        latency_quality = _ratio(metrics.get("latency_quality", 0.50))
        execution_continuity = _ratio(metrics.get("execution_continuity", 0.50))
        cost_stability = _ratio(metrics.get("cost_stability", 0.50))
        error_pressure = _ratio(metrics.get("error_pressure", 0.50))

        base_score = (
            data_availability * 0.28
            + latency_quality * 0.18
            + execution_continuity * 0.26
            + cost_stability * 0.18
            + (1.0 - error_pressure) * 0.10
        )
        health_score = _ratio(base_score)

        if health_score >= 0.80 and error_pressure <= 0.20:
            status = "RUNTIME_HEALTHY"
            action = "ALLOW_PRODUCTION_READINESS_REVIEW"
            reason = "runtime_inputs_support_readiness_review"
        elif health_score >= 0.60:
            status = "RUNTIME_STABLE"
            action = "CONTINUE_SIMULATION_VALIDATION"
            reason = "runtime_inputs_are_stable_but_not_complete"
        else:
            status = "RUNTIME_REVIEW_REQUIRED"
            action = "PAUSE_PRODUCTION_READINESS"
            reason = "runtime_inputs_require_quality_review"

        return RuntimeHealthResult(
            health_score=round(health_score, 4),
            status=status,
            action=action,
            reason=reason,
        )
