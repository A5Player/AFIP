"""Integrated macro market consensus for gold exposure decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class MacroMarketConsensus:
    """Integrated consensus across calendar, news, and macro market factors."""

    status: str
    macro_score: float
    decision_confidence: float
    gold_market_bias: str
    event_risk_state: str
    news_impact_score: float
    market_factor_score: float
    conflict_level: str
    component_scores: Mapping[str, float]
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "macro_score": self.macro_score,
            "decision_confidence": self.decision_confidence,
            "gold_market_bias": self.gold_market_bias,
            "event_risk_state": self.event_risk_state,
            "news_impact_score": self.news_impact_score,
            "market_factor_score": self.market_factor_score,
            "conflict_level": self.conflict_level,
            "component_scores": dict(self.component_scores),
            "reason": self.reason,
        }


class MacroMarketConsensusEngine:
    """Combine macro calendar, macro news, and market factor states into one view."""

    def combine(
        self,
        calendar_state: Mapping[str, object],
        event_assessment: Mapping[str, object],
        news_state: Mapping[str, object],
        market_factor_state: Mapping[str, object],
    ) -> MacroMarketConsensus:
        event_risk_state = str(calendar_state.get("event_risk_state", "CLEAR"))
        event_confidence = self._to_float(event_assessment.get("confidence_score"), 0.0)
        event_score = self._event_score(event_risk_state, event_confidence)
        news_score = self._news_score(news_state)
        market_score = self._market_factor_score(market_factor_state)
        news_impact = self._to_float(news_state.get("impact_score"), 0.0)
        market_bias = self._market_factor_bias(market_factor_state)
        news_bias = self._news_bias(news_state)
        conflict_level = self._conflict_level(news_bias, market_bias, event_risk_state)

        macro_score = (event_score * 0.22) + (news_score * 0.28) + (market_score * 0.50)
        macro_score = round(min(100.0, max(0.0, macro_score)), 2)
        decision_confidence = self._confidence(event_score, news_score, market_score, conflict_level, event_risk_state)
        gold_market_bias = self._bias(macro_score, news_bias, market_bias, conflict_level, event_risk_state)
        reason = self._reason(gold_market_bias, conflict_level, event_risk_state)

        return MacroMarketConsensus(
            status="MACRO_MARKET_CONSENSUS_READY",
            macro_score=macro_score,
            decision_confidence=decision_confidence,
            gold_market_bias=gold_market_bias,
            event_risk_state=event_risk_state,
            news_impact_score=round(news_impact, 2),
            market_factor_score=round(market_score, 2),
            conflict_level=conflict_level,
            component_scores={
                "calendar": round(event_score, 2),
                "news": round(news_score, 2),
                "market_factors": round(market_score, 2),
            },
            reason=reason,
        )

    def combine_dict(
        self,
        calendar_state: Mapping[str, object],
        event_assessment: Mapping[str, object],
        news_state: Mapping[str, object],
        market_factor_state: Mapping[str, object],
    ) -> dict[str, object]:
        return self.combine(calendar_state, event_assessment, news_state, market_factor_state).as_dict()

    def _event_score(self, event_risk_state: str, event_confidence: float) -> float:
        if event_risk_state == "RESTRICTED":
            return 50.0
        if event_risk_state == "ELEVATED":
            return max(42.0, 70.0 - (event_confidence * 0.20))
        return max(50.0, min(72.0, 50.0 + ((100.0 - event_confidence) * 0.12)))

    def _news_score(self, news_state: Mapping[str, object]) -> float:
        bias = self._news_bias(news_state)
        confidence = self._to_float(news_state.get("confidence_score"), 0.0)
        if bias == "GOLD_SUPPORTIVE":
            return min(100.0, 50.0 + confidence * 0.45)
        if bias == "GOLD_PRESSURE":
            return max(0.0, 50.0 - confidence * 0.45)
        if bias == "MIXED":
            return 50.0
        return 50.0

    def _market_factor_score(self, market_factor_state: Mapping[str, object]) -> float:
        bias_state = market_factor_state.get("gold_market_bias")
        if isinstance(bias_state, Mapping):
            return self._to_float(bias_state.get("score"), 50.0)
        return self._to_float(market_factor_state.get("gold_macro_score"), 50.0)

    def _market_factor_bias(self, market_factor_state: Mapping[str, object]) -> str:
        bias_state = market_factor_state.get("gold_market_bias")
        if isinstance(bias_state, Mapping):
            value = str(bias_state.get("bias", "NEUTRAL"))
        else:
            value = str(market_factor_state.get("gold_bias", "NEUTRAL"))
        if value in {"SUPPORTIVE", "GOLD_SUPPORTIVE"}:
            return "GOLD_SUPPORTIVE"
        if value in {"PRESSURE", "GOLD_PRESSURE"}:
            return "GOLD_PRESSURE"
        if value in {"REVIEW", "MIXED"}:
            return "MIXED"
        return "NEUTRAL"

    def _news_bias(self, news_state: Mapping[str, object]) -> str:
        value = str(news_state.get("gold_bias", "NEUTRAL"))
        if value in {"SUPPORTIVE", "GOLD_SUPPORTIVE"}:
            return "GOLD_SUPPORTIVE"
        if value in {"PRESSURE", "GOLD_PRESSURE"}:
            return "GOLD_PRESSURE"
        if value == "MIXED":
            return "MIXED"
        return "NEUTRAL"

    def _conflict_level(self, news_bias: str, market_bias: str, event_risk_state: str) -> str:
        if event_risk_state == "RESTRICTED":
            return "CALENDAR_RESTRICTED"
        if news_bias == "MIXED" or market_bias == "MIXED":
            return "HIGH"
        if {news_bias, market_bias} == {"GOLD_SUPPORTIVE", "GOLD_PRESSURE"}:
            return "HIGH"
        if "NEUTRAL" in {news_bias, market_bias}:
            return "MEDIUM"
        return "LOW"

    def _confidence(self, event_score: float, news_score: float, market_score: float, conflict_level: str, event_risk_state: str) -> float:
        dispersion = max(event_score, news_score, market_score) - min(event_score, news_score, market_score)
        confidence = 88.0 - (dispersion * 0.35)
        if conflict_level == "HIGH":
            confidence -= 18.0
        elif conflict_level == "MEDIUM":
            confidence -= 7.0
        if event_risk_state == "RESTRICTED":
            confidence = min(confidence, 65.0)
        return round(min(100.0, max(0.0, confidence)), 2)

    def _bias(self, macro_score: float, news_bias: str, market_bias: str, conflict_level: str, event_risk_state: str) -> str:
        if event_risk_state == "RESTRICTED":
            return "VOLATILITY_RISK"
        if conflict_level == "HIGH":
            return "MIXED"
        if macro_score >= 62.0 and "GOLD_PRESSURE" not in {news_bias, market_bias}:
            return "GOLD_SUPPORTIVE"
        if macro_score <= 38.0 and "GOLD_SUPPORTIVE" not in {news_bias, market_bias}:
            return "GOLD_PRESSURE"
        return "NEUTRAL"

    def _reason(self, bias: str, conflict_level: str, event_risk_state: str) -> str:
        if event_risk_state == "RESTRICTED":
            return "calendar_window_limits_new_exposure"
        if conflict_level == "HIGH":
            return "macro_inputs_are_conflicted"
        if bias == "GOLD_SUPPORTIVE":
            return "macro_inputs_support_gold"
        if bias == "GOLD_PRESSURE":
            return "macro_inputs_pressure_gold"
        return "macro_inputs_balanced"

    @staticmethod
    def _to_float(value: object, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
