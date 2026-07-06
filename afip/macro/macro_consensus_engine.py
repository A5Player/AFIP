"""Macro consensus scoring for AFIP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class MacroConsensusResult:
    """Final macro intelligence consensus result."""

    status: str
    macro_score: float
    gold_bias: str
    trade_instruction: str
    reason: str


class MacroConsensusEngine:
    """Combine calendar risk, event impact, and market factors."""

    def combine(
        self,
        calendar_state: Mapping[str, object],
        event_assessment: Mapping[str, object],
        market_factor_state: Mapping[str, object],
    ) -> MacroConsensusResult:
        event_confidence = self._to_float(event_assessment.get("confidence_score"))
        factor_score = self._to_float(market_factor_state.get("gold_macro_score"), default=50.0)
        event_risk_state = str(calendar_state.get("event_risk_state", "CLEAR"))
        calendar_instruction = str(calendar_state.get("trade_instruction", "NORMAL_REVIEW"))
        macro_score = (event_confidence * 0.45) + (factor_score * 0.55)
        factor_bias = str(market_factor_state.get("gold_bias", "NEUTRAL"))

        if event_risk_state == "RESTRICTED":
            trade_instruction = "NO_NEW_POSITION"
            gold_bias = "VOLATILITY_RISK"
            reason = "calendar_restricted_window"
        elif factor_bias == "SUPPORTIVE" and macro_score >= 60.0:
            trade_instruction = calendar_instruction if calendar_instruction != "NORMAL_REVIEW" else "ALLOW_WITH_MACRO_SUPPORT"
            gold_bias = "SUPPORTIVE"
            reason = "supportive_market_factors"
        elif factor_bias == "PRESSURE" and macro_score <= 55.0:
            trade_instruction = "REDUCE_BUY_EXPOSURE"
            gold_bias = "PRESSURE"
            reason = "pressuring_market_factors"
        else:
            trade_instruction = calendar_instruction
            gold_bias = "NEUTRAL"
            reason = "mixed_macro_consensus"

        return MacroConsensusResult(
            status="MACRO_CONSENSUS_READY",
            macro_score=round(min(100.0, max(0.0, macro_score)), 2),
            gold_bias=gold_bias,
            trade_instruction=trade_instruction,
            reason=reason,
        )

    def combine_dict(
        self,
        calendar_state: Mapping[str, object],
        event_assessment: Mapping[str, object],
        market_factor_state: Mapping[str, object],
    ) -> dict[str, object]:
        result = self.combine(calendar_state, event_assessment, market_factor_state)
        return {
            "status": result.status,
            "macro_score": result.macro_score,
            "gold_bias": result.gold_bias,
            "trade_instruction": result.trade_instruction,
            "reason": result.reason,
        }

    def _to_float(self, value: object, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
