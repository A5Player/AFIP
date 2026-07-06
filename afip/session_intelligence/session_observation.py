"""Production Milestone E Pack 1 session intelligence observation model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


def _norm(value: Any, default: str = "UNKNOWN") -> str:
    text = str(value or "").strip().upper().replace(" ", "_").replace("-", "_")
    return text or default


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class SessionObservation:
    """Single market-session observation normalized after market regime is known."""

    market_regime: str
    session_key: str
    overlap_key: str
    direction: str
    sample_count: int
    average_range_points: float
    realized_volatility: float
    liquidity_score: float
    execution_cost_score: float
    favorable_outcome_rate: float
    trace_id: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SessionObservation":
        return cls(
            market_regime=_norm(value.get("market_regime") or value.get("regime")),
            session_key=_norm(value.get("session_key") or value.get("session")),
            overlap_key=_norm(value.get("overlap_key") or value.get("overlap") or "NONE"),
            direction=_norm(value.get("direction") or value.get("bias") or "FLAT"),
            sample_count=int(_float(value.get("sample_count") or value.get("samples"))),
            average_range_points=_float(value.get("average_range_points") or value.get("range_points")),
            realized_volatility=_float(value.get("realized_volatility") or value.get("volatility")),
            liquidity_score=_float(value.get("liquidity_score") or value.get("liquidity")),
            execution_cost_score=_float(value.get("execution_cost_score") or value.get("cost_score")),
            favorable_outcome_rate=_float(value.get("favorable_outcome_rate") or value.get("outcome_rate")),
            trace_id=str(value.get("trace_id") or value.get("trace") or "").strip(),
        )

    @property
    def regime_session_key(self) -> str:
        return f"{self.market_regime}:{self.session_key}:{self.overlap_key}:{self.direction}"

    @property
    def has_market_regime(self) -> bool:
        return self.market_regime not in {"", "UNKNOWN"}

    @property
    def is_usable(self) -> bool:
        return (
            self.has_market_regime
            and self.session_key not in {"", "UNKNOWN"}
            and self.sample_count > 0
            and self.average_range_points > 0
            and self.realized_volatility > 0
            and self.liquidity_score > 0
            and self.execution_cost_score > 0
            and self.favorable_outcome_rate > 0
            and bool(self.trace_id)
        )
