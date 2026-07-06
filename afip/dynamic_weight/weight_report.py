"""Production Milestone E Pack 5 dynamic weight report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .weight_policy import DynamicWeightDecision
from .weight_profile import DynamicWeightProfile


@dataclass(frozen=True)
class DynamicWeightReport:
    """Immutable report for dynamic weight runtime."""

    status: str
    action: str
    reason: str
    profile_count: int
    selected_profile_key: str
    active_market_regime: str
    selected_intelligence_name: str
    selected_direction: str
    average_contribution_score: float
    average_accuracy_rate: float
    average_conflict_score: float
    normalized_weight_score: float
    trace_ids: Tuple[str, ...]
    is_ready: bool

    @classmethod
    def from_profiles(
        cls,
        profiles: Tuple[DynamicWeightProfile, ...],
        decision: DynamicWeightDecision,
    ) -> "DynamicWeightReport":
        selected = next((profile for profile in profiles if profile.profile_key == decision.selected_profile_key), None)
        return cls(
            status=decision.status,
            action=decision.action,
            reason=decision.reason,
            profile_count=len(profiles),
            selected_profile_key=decision.selected_profile_key,
            active_market_regime=selected.market_regime if selected else "UNKNOWN",
            selected_intelligence_name=selected.intelligence_name if selected else "UNKNOWN",
            selected_direction=selected.direction if selected else "UNKNOWN",
            average_contribution_score=selected.average_contribution_score if selected else 0.0,
            average_accuracy_rate=selected.average_accuracy_rate if selected else 0.0,
            average_conflict_score=selected.average_conflict_score if selected else 0.0,
            normalized_weight_score=selected.normalized_weight_score if selected else 0.0,
            trace_ids=selected.trace_ids if selected else (),
            is_ready=decision.status == "DYNAMIC_WEIGHT_READY" and selected is not None,
        )
