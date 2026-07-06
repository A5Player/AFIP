"""Macro intelligence snapshot."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MacroSnapshot:
    """Integrated macro intelligence snapshot for runtime reports."""

    status: str
    next_event: str | None
    event_risk_state: str
    macro_score: float
    gold_bias: str
    trade_instruction: str
    reason: str
