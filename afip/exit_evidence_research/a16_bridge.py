"""Bridge chronological exit outcomes into A16 research evidence only."""
from __future__ import annotations
from typing import Any, Mapping

from afip.exit_outcome_research import A16ResearchContext
from .a16_evidence import A16ExitObservation


def outcome_to_a16_evidence(*, outcome: Mapping[str, Any], context: A16ResearchContext,
                            execution_cost_r: float) -> A16ExitObservation:
    """Map a completed blind-forward outcome; no order or promotion action occurs."""
    if execution_cost_r < 0:
        raise ValueError("execution cost cannot be negative")
    if bool(outcome.get("production_usable")) or outcome.get("research_state") != "EXPERIMENTAL":
        raise ValueError("only experimental research outcomes may enter A16 evidence")
    required = ("policy_id", "realized_r", "maximum_favorable_excursion_r", "maximum_adverse_excursion_r")
    if any(name not in outcome for name in required):
        raise ValueError("outcome is incomplete")
    realized = float(outcome["realized_r"])
    mfe = max(0.0, float(outcome["maximum_favorable_excursion_r"]))
    return A16ExitObservation(
        policy_id=str(outcome["policy_id"]), realized_r=realized, mfe_r=mfe,
        mae_r=max(0.0, float(outcome["maximum_adverse_excursion_r"])),
        giveback_r=max(0.0, mfe - max(0.0, realized)), pattern_id=context.pattern_id,
        plan_id=context.plan_id, market_regime=context.market_regime,
        session_name=context.session_name, event_window=context.event_window,
        calendar_context=context.calendar_context, execution_cost_r=execution_cost_r,
        future_data_used=context.future_data_used,
        outcome_evaluation_uses_subsequent_closed_bars=context.outcome_evaluation_uses_subsequent_closed_bars,
    )
