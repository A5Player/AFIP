"""A16 research-only exit-policy contract; never sends or changes orders."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Mapping

POLICY_IDS = ("FIXED_TP", "BREAK_EVEN_FIXED_TP", "R_STEP", "MFE_PERCENT", "ATR", "STRUCTURE", "HYBRID_R_STRUCTURE", "PARTIAL_RUNNER")

@dataclass(frozen=True)
class A16ResearchContext:
    pattern_id: str
    pattern_family: str
    plan_id: str
    decision_timestamp_utc: str
    market_regime: str
    session_name: str
    session_phase: str
    event_window: str
    calendar_context: str
    execution_cost_evidence: str
    future_data_used: bool = False
    outcome_evaluation_uses_subsequent_closed_bars: bool = True
    decision_future_data_allowed: bool = False
    outcome_evaluation_requires_subsequent_closed_bars: bool = True
    outcome_evaluation_method: str = "BLIND_FORWARD_CLOSED_BAR_LABEL_AFTER_DECISION_TIME"
    decision_score_percent: float | None = None

    def __post_init__(self) -> None:
        if not all(str(getattr(self, n)).strip() for n in ("pattern_id", "pattern_family", "plan_id", "decision_timestamp_utc", "market_regime", "session_name", "session_phase", "event_window", "calendar_context", "execution_cost_evidence")):
            raise ValueError("A16 research context is incomplete")
        if self.future_data_used or self.decision_future_data_allowed:
            raise ValueError("A16 decision context must not use future data")
        if not self.outcome_evaluation_uses_subsequent_closed_bars or not self.outcome_evaluation_requires_subsequent_closed_bars:
            raise ValueError("A16 outcome must be blind-forward closed-bar labelled")
        if self.decision_score_percent is not None and not 0 <= self.decision_score_percent <= 100:
            raise ValueError("A16 decision score must be a percentage from 0 to 100")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

def candidate_policy_ids() -> tuple[str, ...]:
    """Return comparison candidates only; this does not select or promote a winner."""
    return POLICY_IDS

def validate_advisory_record(value: Mapping[str, Any]) -> None:
    if bool(value.get("live_execution_enabled")) or bool(value.get("direct_execution")):
        raise ValueError("A16 research/advisory records cannot request execution")
