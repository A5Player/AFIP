"""Production Milestone E Pack 8 macro context report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .macro_policy import MacroDecision
from .macro_profile import MacroProfile


@dataclass(frozen=True)
class MacroReport:
    """Immutable report for macro context runtime."""

    status: str
    action: str
    reason: str
    profile_count: int
    selected_profile_key: str
    active_market_regime: str
    selected_macro_theme: str
    selected_direction: str
    average_dxy_alignment_score: float
    average_yield_alignment_score: float
    average_inflation_surprise_score: float
    average_labor_market_pressure: float
    average_policy_rate_bias_score: float
    average_news_risk_score: float
    average_macro_consensus_score: float
    average_execution_cost_score: float
    macro_context_score: float
    trace_ids: Tuple[str, ...]
    is_ready: bool

    @classmethod
    def from_profiles(cls, profiles: Tuple[MacroProfile, ...], decision: MacroDecision) -> "MacroReport":
        selected = next((profile for profile in profiles if profile.profile_key == decision.selected_profile_key), None)
        return cls(
            status=decision.status,
            action=decision.action,
            reason=decision.reason,
            profile_count=len(profiles),
            selected_profile_key=decision.selected_profile_key,
            active_market_regime=selected.market_regime if selected else "UNKNOWN",
            selected_macro_theme=selected.macro_theme if selected else "UNKNOWN",
            selected_direction=selected.direction if selected else "UNKNOWN",
            average_dxy_alignment_score=selected.average_dxy_alignment_score if selected else 0.0,
            average_yield_alignment_score=selected.average_yield_alignment_score if selected else 0.0,
            average_inflation_surprise_score=selected.average_inflation_surprise_score if selected else 0.0,
            average_labor_market_pressure=selected.average_labor_market_pressure if selected else 0.0,
            average_policy_rate_bias_score=selected.average_policy_rate_bias_score if selected else 0.0,
            average_news_risk_score=selected.average_news_risk_score if selected else 0.0,
            average_macro_consensus_score=selected.average_macro_consensus_score if selected else 0.0,
            average_execution_cost_score=selected.average_execution_cost_score if selected else 0.0,
            macro_context_score=selected.macro_context_score if selected else 0.0,
            trace_ids=selected.trace_ids if selected else (),
            is_ready=decision.status == "MACRO_CONTEXT_READY" and selected is not None,
        )
