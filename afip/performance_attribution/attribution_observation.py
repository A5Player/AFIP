"""Production Milestone E Pack 6 performance attribution observation model."""

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
class PerformanceAttributionObservation:
    """Single data-derived attribution observation for a financial capability."""

    market_regime: str
    attribution_source: str
    direction: str
    sample_count: int
    gross_pnl: float
    net_pnl: float
    contribution_score: float
    decision_alignment_rate: float
    execution_quality_score: float
    drawdown_impact: float
    trace_id: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PerformanceAttributionObservation":
        return cls(
            market_regime=_norm(value.get("market_regime") or value.get("regime")),
            attribution_source=_norm(value.get("attribution_source") or value.get("component") or value.get("source")),
            direction=_norm(value.get("direction") or value.get("bias") or "FLAT"),
            sample_count=int(_float(value.get("sample_count") or value.get("samples"))),
            gross_pnl=_float(value.get("gross_pnl") or value.get("gross_profit")),
            net_pnl=_float(value.get("net_pnl") or value.get("net_profit")),
            contribution_score=_float(value.get("contribution_score") or value.get("contribution")),
            decision_alignment_rate=_float(value.get("decision_alignment_rate") or value.get("alignment_rate")),
            execution_quality_score=_float(value.get("execution_quality_score") or value.get("quality_score")),
            drawdown_impact=_float(value.get("drawdown_impact") or value.get("drawdown")),
            trace_id=str(value.get("trace_id") or value.get("trace") or "").strip(),
        )

    @property
    def attribution_key(self) -> str:
        return f"{self.market_regime}:{self.attribution_source}:{self.direction}"

    @property
    def has_market_regime(self) -> bool:
        return self.market_regime not in {"", "UNKNOWN"}

    @property
    def is_usable(self) -> bool:
        return (
            self.has_market_regime
            and self.attribution_source not in {"", "UNKNOWN"}
            and self.sample_count > 0
            and self.gross_pnl != 0
            and self.net_pnl != 0
            and self.contribution_score > 0
            and self.decision_alignment_rate > 0
            and self.execution_quality_score > 0
            and self.drawdown_impact >= 0
            and bool(self.trace_id)
        )
