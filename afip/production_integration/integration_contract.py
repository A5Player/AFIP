"""Production integration contract for Production Milestone C Pack 19."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


def _status(value: object) -> str:
    return str(value or "UNKNOWN").strip().upper()


def _float(value: object) -> float:
    return round(float(value or 0.0), 4)


@dataclass(frozen=True)
class ProductionIntegrationContract:
    regime_status: str
    decision_status: str
    execution_status: str
    action: str
    regime_first_key: str
    decision_confidence: float
    readiness_score: float
    spread_points: float
    maximum_spread_points: float
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        action = str(self.action or "WAIT").strip().upper()
        object.__setattr__(self, "regime_status", _status(self.regime_status))
        object.__setattr__(self, "decision_status", _status(self.decision_status))
        object.__setattr__(self, "execution_status", _status(self.execution_status))
        object.__setattr__(self, "action", action if action in {"BUY", "SELL"} else "WAIT")
        object.__setattr__(self, "regime_first_key", str(self.regime_first_key or "UNKNOWN").strip().upper())
        object.__setattr__(self, "decision_confidence", round(max(0.0, min(100.0, float(self.decision_confidence))), 4))
        object.__setattr__(self, "readiness_score", round(max(0.0, min(100.0, float(self.readiness_score))), 4))
        object.__setattr__(self, "spread_points", round(max(0.0, float(self.spread_points)), 4))
        object.__setattr__(self, "maximum_spread_points", round(max(0.0, float(self.maximum_spread_points)), 4))
        object.__setattr__(self, "reasons", tuple(str(reason) for reason in self.reasons if str(reason)))

    @property
    def is_ready(self) -> bool:
        return (
            self.regime_status == "MARKET_REGIME_INTELLIGENCE_READY"
            and self.decision_status == "DECISION_INTELLIGENCE_READY"
            and self.execution_status == "EXECUTION_READY"
            and self.action in {"BUY", "SELL"}
        )

    @classmethod
    def from_states(
        cls,
        regime_state: Mapping[str, Any],
        decision_state: Mapping[str, Any],
        execution_state: Mapping[str, Any],
    ) -> "ProductionIntegrationContract":
        decision = decision_state.get("decision", {})
        decision_map = decision if isinstance(decision, Mapping) else {}
        execution_decision = execution_state.get("decision", {})
        execution_map = execution_decision if isinstance(execution_decision, Mapping) else {}
        execution_input = execution_state.get("input", {})
        input_map = execution_input if isinstance(execution_input, Mapping) else {}
        reasons: list[str] = []
        for source in (regime_state, decision_state, execution_state, decision_map, execution_map):
            reason = source.get("reason") if isinstance(source, Mapping) else None
            if reason:
                reasons.append(str(reason))
        return cls(
            regime_status=_status(regime_state.get("status")),
            decision_status=_status(decision_state.get("status")),
            execution_status=_status(execution_state.get("status")),
            action=str(execution_map.get("action", decision_map.get("action", "WAIT"))),
            regime_first_key=str(decision_map.get("regime_first_key", input_map.get("regime_first_key", "UNKNOWN"))),
            decision_confidence=_float(decision_map.get("confidence", input_map.get("decision_confidence", 0.0))),
            readiness_score=_float(execution_map.get("readiness_score", 0.0)),
            spread_points=_float(input_map.get("spread_points", 0.0)),
            maximum_spread_points=_float(input_map.get("maximum_spread_points", 0.0)),
            reasons=tuple(reasons),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "regime_status": self.regime_status,
            "decision_status": self.decision_status,
            "execution_status": self.execution_status,
            "action": self.action,
            "regime_first_key": self.regime_first_key,
            "decision_confidence": self.decision_confidence,
            "readiness_score": self.readiness_score,
            "spread_points": self.spread_points,
            "maximum_spread_points": self.maximum_spread_points,
            "reasons": list(self.reasons),
            "is_ready": self.is_ready,
        }
