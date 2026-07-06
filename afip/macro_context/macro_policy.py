"""Production Milestone E Pack 8 macro context policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .macro_profile import MacroProfile


@dataclass(frozen=True)
class MacroDecision:
    """Deterministic decision describing macro context readiness."""

    status: str
    action: str
    reason: str
    selected_profile_key: str


class MacroPolicy:
    """Select the strongest data-derived macro context profile."""

    def decide(self, profiles: Tuple[MacroProfile, ...]) -> MacroDecision:
        if not profiles:
            return MacroDecision(
                status="MACRO_CONTEXT_WAIT",
                action="WAIT",
                reason="no_usable_macro_observations",
                selected_profile_key="",
            )
        ready_profiles = tuple(profile for profile in profiles if profile.is_ready)
        if not ready_profiles:
            return MacroDecision(
                status="MACRO_CONTEXT_WAIT",
                action="WAIT",
                reason="insufficient_macro_evidence",
                selected_profile_key=profiles[0].profile_key,
            )
        selected = sorted(
            ready_profiles,
            key=lambda item: (
                -item.macro_context_score,
                item.average_news_risk_score,
                item.average_execution_cost_score,
                -item.sample_count,
                item.profile_key,
            ),
        )[0]
        return MacroDecision(
            status="MACRO_CONTEXT_READY",
            action="APPLY_MACRO_CONTEXT",
            reason="macro_profile_ready",
            selected_profile_key=selected.profile_key,
        )
