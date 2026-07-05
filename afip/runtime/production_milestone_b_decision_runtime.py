"""Production Milestone B decision runtime compatibility layer.

This runtime preserves the Pack 5 public ``run`` interface while supporting
Pack 10 decision intelligence evaluation with market and risk context inputs.
It is deterministic, simulation-safe, and does not alter live execution state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ProductionDecisionRuntimeResult:
    """Structured runtime result for backward-compatible decision evaluation."""

    status: str
    action: str
    confidence: float
    consensus: str
    risk_status: str
    reason: str

    @property
    def confidence_level(self) -> str:
        """Backward-compatible confidence level expected by Pack 5 tests."""

        if self.consensus in {"HIGH", "MODERATE", "LOW"}:
            return self.consensus
        if self.confidence >= 0.80:
            return "HIGH"
        if self.confidence >= 0.65:
            return "MODERATE"
        return "LOW"


class ProductionMilestoneBDecisionRuntime:
    """Integrates decision intelligence while preserving legacy runtime behavior."""

    def __init__(self, minimum_confidence: float = 0.70) -> None:
        self.minimum_confidence = float(minimum_confidence)

    def run(
        self,
        intelligence_profiles: Iterable[Mapping[str, Any]] | None = None,
        risk_profile: Mapping[str, Any] | None = None,
    ) -> ProductionDecisionRuntimeResult:
        """Run decision evaluation with default profiles when inputs are omitted."""

        profiles = list(intelligence_profiles or self._default_profiles())
        risk = dict(risk_profile or {"risk_status": "ACCEPTABLE"})
        risk_status = str(risk.get("risk_status", "ACCEPTABLE")).upper()
        buy_score = self._weighted_direction_score(profiles, "BUY")
        sell_score = self._weighted_direction_score(profiles, "SELL")
        confidence = max(buy_score, sell_score)

        if risk_status not in {"ACCEPTABLE", "PASS", "READY"}:
            return ProductionDecisionRuntimeResult(
                status="MILESTONE_B_DECISION_RUNTIME_READY",
                action="WAIT",
                confidence=round(confidence, 4),
                consensus="RISK_REVIEW",
                risk_status=risk_status,
                reason="risk_profile_not_acceptable",
            )

        if buy_score >= sell_score and buy_score >= self.minimum_confidence:
            return ProductionDecisionRuntimeResult(
                status="MILESTONE_B_DECISION_RUNTIME_READY",
                action="BUY",
                confidence=round(buy_score, 4),
                consensus="HIGH" if buy_score >= 0.80 else "MODERATE",
                risk_status="ACCEPTABLE",
                reason="weighted_buy_decision_consensus",
            )

        if sell_score > buy_score and sell_score >= self.minimum_confidence:
            return ProductionDecisionRuntimeResult(
                status="MILESTONE_B_DECISION_RUNTIME_READY",
                action="SELL",
                confidence=round(sell_score, 4),
                consensus="HIGH" if sell_score >= 0.80 else "MODERATE",
                risk_status="ACCEPTABLE",
                reason="weighted_sell_decision_consensus",
            )

        return ProductionDecisionRuntimeResult(
            status="MILESTONE_B_DECISION_RUNTIME_READY",
            action="WAIT",
            confidence=round(confidence, 4),
            consensus="LOW",
            risk_status="ACCEPTABLE",
            reason="decision_confidence_below_threshold",
        )

    def evaluate(
        self,
        candidates: Iterable[Mapping[str, Any]] | None = None,
        market_context: Mapping[str, Any] | None = None,
        risk_context: Mapping[str, Any] | None = None,
        risk_profile: Mapping[str, Any] | None = None,
        **_: Any,
    ) -> dict[str, Any] | ProductionDecisionRuntimeResult:
        """Evaluate Pack 10 decision inputs while keeping Pack 5 compatibility.

        Pack 10 passes ``market_context`` and ``risk_context`` keyword arguments
        and expects a dictionary. Earlier integrations may call ``evaluate`` as a
        simple alias to ``run`` and expect the structured result object.
        """

        if market_context is None and risk_context is None:
            return self.run(intelligence_profiles=candidates, risk_profile=risk_profile)

        market = dict(market_context or {})
        risk = dict(risk_context or risk_profile or {})
        profiles = list(candidates or self._default_profiles())
        base = self.run(
            intelligence_profiles=self._normalize_candidate_profiles(profiles),
            risk_profile=self._risk_profile_from_context(risk),
        )
        context_score = self._clamp_percent(float(market.get("context_score", 70.0)))
        execution_score = self._clamp_percent(float(market.get("execution_score", 70.0)))
        learning_score = self._clamp_percent(float(market.get("learning_score", 60.0)))
        memory_score = self._clamp_percent(float(market.get("memory_score", 60.0)))
        liquidity_score = self._clamp_percent(float(market.get("liquidity_score", 70.0)))
        context_adjustment = (context_score + execution_score + learning_score + memory_score + liquidity_score) / 500.0
        confidence_percent = self._clamp_percent((base.confidence * 100.0 * 0.70) + (context_adjustment * 100.0 * 0.30))
        action = self._risk_adjusted_action(base.action, confidence_percent, risk)
        trace_action = action if action in {"BUY", "SELL", "WAIT", "REDUCE", "NO_ACTION"} else "WAIT"

        return {
            "status": "PRODUCTION_MILESTONE_B_DECISION_READY",
            "action": action,
            "confidence": round(confidence_percent, 4),
            "consensus_status": base.consensus,
            "priority": "HIGH" if confidence_percent >= 80 else "MODERATE" if confidence_percent >= 65 else "LOW",
            "risk_status": "ACCEPTABLE" if action not in {"REDUCE", "NO_ACTION"} else "CAUTION",
            "trace_id": f"AFIP-DECISION-000001-{trace_action}",
            "reason": base.reason,
        }

    def _default_profiles(self) -> list[dict[str, Any]]:
        return [
            {"direction": "BUY", "confidence": 0.88, "weight": 0.34},
            {"direction": "BUY", "confidence": 0.84, "weight": 0.28},
            {"direction": "BUY", "confidence": 0.79, "weight": 0.20},
            {"direction": "SELL", "confidence": 0.42, "weight": 0.10},
            {"direction": "FLAT", "confidence": 0.30, "weight": 0.08},
        ]

    def _normalize_candidate_profiles(self, candidates: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for candidate in candidates:
            direction = str(candidate.get("direction", candidate.get("action", "FLAT"))).upper()
            confidence = float(candidate.get("confidence", 0.0))
            if confidence > 1.0:
                confidence = confidence / 100.0
            normalized.append(
                {
                    "direction": direction,
                    "confidence": self._clamp_ratio(confidence),
                    "weight": max(float(candidate.get("weight", 0.0)), 0.0),
                }
            )
        return normalized

    def _risk_profile_from_context(self, risk_context: Mapping[str, Any]) -> dict[str, Any]:
        drawdown_ratio = float(risk_context.get("drawdown_ratio", 0.0))
        exposure_ratio = float(risk_context.get("exposure_ratio", 0.0))
        if drawdown_ratio >= 0.25:
            return {"risk_status": "RESTRICTED"}
        if exposure_ratio >= 0.80:
            return {"risk_status": "REVIEW"}
        return {"risk_status": "ACCEPTABLE"}

    def _risk_adjusted_action(self, action: str, confidence: float, risk_context: Mapping[str, Any]) -> str:
        drawdown_ratio = float(risk_context.get("drawdown_ratio", 0.0))
        exposure_ratio = float(risk_context.get("exposure_ratio", 0.0))
        if drawdown_ratio >= 0.25:
            return "NO_ACTION"
        if exposure_ratio >= 0.75 and action in {"BUY", "SELL"}:
            return "REDUCE"
        if confidence < 55:
            return "WAIT"
        return action

    def _weighted_direction_score(self, profiles: Iterable[Mapping[str, Any]], direction: str) -> float:
        score = 0.0
        active_weight = 0.0
        direction = direction.upper()
        for profile in profiles:
            profile_direction = str(profile.get("direction", profile.get("action", "FLAT"))).upper()
            confidence = float(profile.get("confidence", 0.0))
            if confidence > 1.0:
                confidence = confidence / 100.0
            confidence = self._clamp_ratio(confidence)
            weight = max(float(profile.get("weight", 0.0)), 0.0)
            if profile_direction == direction:
                score += confidence * weight
                active_weight += weight
        if active_weight <= 0:
            return 0.0
        return self._clamp_ratio(score / active_weight)

    @staticmethod
    def _clamp_ratio(value: float) -> float:
        return max(0.0, min(1.0, value))

    @staticmethod
    def _clamp_percent(value: float) -> float:
        return max(0.0, min(100.0, value))
