"""Production Milestone E Pack 9 adaptive learning policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .learning_profile import AdaptiveLearningProfile


@dataclass(frozen=True)
class AdaptiveLearningDecision:
    """Deterministic decision describing adaptive learning readiness."""

    status: str
    action: str
    reason: str
    selected_profile_key: str


class AdaptiveLearningPolicy:
    """Select the strongest data-derived adaptive learning profile."""

    def decide(self, profiles: Tuple[AdaptiveLearningProfile, ...]) -> AdaptiveLearningDecision:
        if not profiles:
            return AdaptiveLearningDecision(
                status="ADAPTIVE_LEARNING_WAIT",
                action="WAIT",
                reason="no_usable_learning_observations",
                selected_profile_key="",
            )
        ready_profiles = tuple(profile for profile in profiles if profile.is_ready)
        if not ready_profiles:
            return AdaptiveLearningDecision(
                status="ADAPTIVE_LEARNING_WAIT",
                action="WAIT",
                reason="insufficient_learning_evidence",
                selected_profile_key=profiles[0].profile_key,
            )
        selected = sorted(
            ready_profiles,
            key=lambda item: (
                -item.adaptive_learning_score,
                item.average_drift_risk_score,
                item.average_execution_cost_score,
                -item.sample_count,
                item.profile_key,
            ),
        )[0]
        return AdaptiveLearningDecision(
            status="ADAPTIVE_LEARNING_READY",
            action="APPLY_ADAPTIVE_LEARNING",
            reason="adaptive_learning_profile_ready",
            selected_profile_key=selected.profile_key,
        )
