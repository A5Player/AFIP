"""Macro dashboard report builder."""

from __future__ import annotations

from typing import Mapping


class MacroDashboardReport:
    """Create a compact macro report line for AFIP runtime output."""

    def build(self, macro_state: Mapping[str, object]) -> str:
        next_event = macro_state.get("next_event") or "No scheduled event"
        score = macro_state.get("macro_score", 0.0)
        bias = macro_state.get("gold_bias", "NEUTRAL")
        instruction = macro_state.get("trade_instruction", "NORMAL_REVIEW")
        return f"Macro: {next_event} | Score {score} | Bias {bias} | Instruction {instruction}"
