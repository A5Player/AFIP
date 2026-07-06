"""Production Milestone E Pack 5 dynamic weight policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .weight_profile import DynamicWeightProfile


@dataclass(frozen=True)
class DynamicWeightDecision:
    """Deterministic decision describing adaptive weight readiness."""

    status: str
    action: str
    reason: str
    selected_profile_key: str


class DynamicWeightPolicy:
    """Select the strongest data-derived intelligence weight profile."""

    def decide(self, profiles: Tuple[DynamicWeightProfile, ...]) -> DynamicWeightDecision:
        if not profiles:
            return DynamicWeightDecision(
                status="DYNAMIC_WEIGHT_WAIT",
                action="WAIT",
                reason="no_usable_dynamic_weight_observations",
                selected_profile_key="",
            )
        ready_profiles = tuple(profile for profile in profiles if profile.is_ready)
        if not ready_profiles:
            return DynamicWeightDecision(
                status="DYNAMIC_WEIGHT_WAIT",
                action="WAIT",
                reason="insufficient_dynamic_weight_evidence",
                selected_profile_key=profiles[0].profile_key,
            )
        selected = sorted(
            ready_profiles,
            key=lambda item: (
                -item.normalized_weight_score,
                item.average_conflict_score,
                -item.sample_count,
                item.profile_key,
            ),
        )[0]
        return DynamicWeightDecision(
            status="DYNAMIC_WEIGHT_READY",
            action="APPLY_DYNAMIC_WEIGHT",
            reason="dynamic_weight_profile_ready",
            selected_profile_key=selected.profile_key,
        )
