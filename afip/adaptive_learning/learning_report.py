"""Production Milestone E Pack 9 adaptive learning report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .learning_policy import AdaptiveLearningDecision
from .learning_profile import AdaptiveLearningProfile


@dataclass(frozen=True)
class AdaptiveLearningReport:
    """Immutable report for adaptive learning runtime."""

    status: str
    action: str
    reason: str
    profile_count: int
    selected_profile_key: str
    active_market_regime: str
    selected_learning_context: str
    selected_direction: str
    average_reinforcement_score: float
    average_adaptation_score: float
    average_forgetting_score: float
    average_validation_score: float
    average_stability_score: float
    average_drift_risk_score: float
    average_execution_cost_score: float
    adaptive_learning_score: float
    trace_ids: Tuple[str, ...]
    is_ready: bool

    @classmethod
    def from_profiles(
        cls, profiles: Tuple[AdaptiveLearningProfile, ...], decision: AdaptiveLearningDecision
    ) -> "AdaptiveLearningReport":
        selected = next((profile for profile in profiles if profile.profile_key == decision.selected_profile_key), None)
        return cls(
            status=decision.status,
            action=decision.action,
            reason=decision.reason,
            profile_count=len(profiles),
            selected_profile_key=decision.selected_profile_key,
            active_market_regime=selected.market_regime if selected else "UNKNOWN",
            selected_learning_context=selected.learning_context if selected else "UNKNOWN",
            selected_direction=selected.direction if selected else "UNKNOWN",
            average_reinforcement_score=selected.average_reinforcement_score if selected else 0.0,
            average_adaptation_score=selected.average_adaptation_score if selected else 0.0,
            average_forgetting_score=selected.average_forgetting_score if selected else 0.0,
            average_validation_score=selected.average_validation_score if selected else 0.0,
            average_stability_score=selected.average_stability_score if selected else 0.0,
            average_drift_risk_score=selected.average_drift_risk_score if selected else 0.0,
            average_execution_cost_score=selected.average_execution_cost_score if selected else 0.0,
            adaptive_learning_score=selected.adaptive_learning_score if selected else 0.0,
            trace_ids=selected.trace_ids if selected else (),
            is_ready=decision.status == "ADAPTIVE_LEARNING_READY" and selected is not None,
        )
