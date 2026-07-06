"""Production Milestone E Pack 2 volatility intelligence observation model."""

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
class VolatilityObservation:
    """Single volatility observation normalized after market regime is known."""

    market_regime: str
    volatility_state: str
    direction: str
    sample_count: int
    atr_points: float
    realized_volatility: float
    expected_volatility: float
    expansion_score: float
    compression_score: float
    execution_cost_score: float
    favorable_outcome_rate: float
    trace_id: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "VolatilityObservation":
        return cls(
            market_regime=_norm(value.get("market_regime") or value.get("regime")),
            volatility_state=_norm(value.get("volatility_state") or value.get("state")),
            direction=_norm(value.get("direction") or value.get("bias") or "FLAT"),
            sample_count=int(_float(value.get("sample_count") or value.get("samples"))),
            atr_points=_float(value.get("atr_points") or value.get("atr")),
            realized_volatility=_float(value.get("realized_volatility") or value.get("realized")),
            expected_volatility=_float(value.get("expected_volatility") or value.get("expected")),
            expansion_score=_float(value.get("expansion_score") or value.get("expansion")),
            compression_score=_float(value.get("compression_score") or value.get("compression")),
            execution_cost_score=_float(value.get("execution_cost_score") or value.get("cost_score")),
            favorable_outcome_rate=_float(value.get("favorable_outcome_rate") or value.get("outcome_rate")),
            trace_id=str(value.get("trace_id") or value.get("trace") or "").strip(),
        )

    @property
    def regime_volatility_key(self) -> str:
        return f"{self.market_regime}:{self.volatility_state}:{self.direction}"

    @property
    def has_market_regime(self) -> bool:
        return self.market_regime not in {"", "UNKNOWN"}

    @property
    def is_usable(self) -> bool:
        return (
            self.has_market_regime
            and self.volatility_state not in {"", "UNKNOWN"}
            and self.sample_count > 0
            and self.atr_points > 0
            and self.realized_volatility > 0
            and self.expected_volatility > 0
            and self.expansion_score >= 0
            and self.compression_score >= 0
            and self.execution_cost_score > 0
            and self.favorable_outcome_rate > 0
            and bool(self.trace_id)
        )
