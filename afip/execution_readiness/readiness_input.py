"""Execution readiness input contract for Production Milestone C Pack 18."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


def _action(value: str) -> str:
    normalized = str(value or "WAIT").strip().upper()
    if normalized in {"BUY", "SELL"}:
        return normalized
    return "WAIT"


@dataclass(frozen=True)
class ExecutionReadinessInput:
    action: str
    decision_confidence: float
    decision_score: float
    regime_first_key: str
    spread_points: float
    maximum_spread_points: float
    liquidity_score: float
    risk_score: float
    available_margin_ratio: float
    open_position_count: int
    maximum_position_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "action", _action(self.action))
        object.__setattr__(self, "decision_confidence", round(max(0.0, min(100.0, float(self.decision_confidence))), 4))
        object.__setattr__(self, "decision_score", round(max(0.0, float(self.decision_score)), 4))
        object.__setattr__(self, "regime_first_key", str(self.regime_first_key or "UNKNOWN").strip().upper())
        object.__setattr__(self, "spread_points", round(max(0.0, float(self.spread_points)), 4))
        object.__setattr__(self, "maximum_spread_points", round(max(0.0, float(self.maximum_spread_points)), 4))
        object.__setattr__(self, "liquidity_score", round(max(0.0, min(100.0, float(self.liquidity_score))), 4))
        object.__setattr__(self, "risk_score", round(max(0.0, min(100.0, float(self.risk_score))), 4))
        object.__setattr__(self, "available_margin_ratio", round(max(0.0, float(self.available_margin_ratio)), 4))
        object.__setattr__(self, "open_position_count", max(0, int(self.open_position_count)))
        object.__setattr__(self, "maximum_position_count", max(0, int(self.maximum_position_count)))

    @property
    def has_action(self) -> bool:
        return self.action in {"BUY", "SELL"}

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ExecutionReadinessInput":
        decision = value.get("decision", {})
        decision_map = decision if isinstance(decision, Mapping) else {}
        return cls(
            action=str(value.get("action", decision_map.get("action", "WAIT"))),
            decision_confidence=float(value.get("decision_confidence", decision_map.get("confidence", 0.0))),
            decision_score=float(value.get("decision_score", decision_map.get("score", 0.0))),
            regime_first_key=str(value.get("regime_first_key", decision_map.get("regime_first_key", "UNKNOWN"))),
            spread_points=float(value.get("spread_points", 0.0)),
            maximum_spread_points=float(value.get("maximum_spread_points", value.get("spread_limit_points", 0.0))),
            liquidity_score=float(value.get("liquidity_score", 0.0)),
            risk_score=float(value.get("risk_score", 0.0)),
            available_margin_ratio=float(value.get("available_margin_ratio", 0.0)),
            open_position_count=int(value.get("open_position_count", 0)),
            maximum_position_count=int(value.get("maximum_position_count", 0)),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "decision_confidence": self.decision_confidence,
            "decision_score": self.decision_score,
            "regime_first_key": self.regime_first_key,
            "spread_points": self.spread_points,
            "maximum_spread_points": self.maximum_spread_points,
            "liquidity_score": self.liquidity_score,
            "risk_score": self.risk_score,
            "available_margin_ratio": self.available_margin_ratio,
            "open_position_count": self.open_position_count,
            "maximum_position_count": self.maximum_position_count,
        }
