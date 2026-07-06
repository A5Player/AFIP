"""Production Milestone E Pack 7 portfolio intelligence observation model."""

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
class PortfolioObservation:
    """Single data-derived portfolio observation for financial exposure context."""

    market_regime: str
    portfolio_scope: str
    direction: str
    sample_count: int
    exposure_score: float
    correlation_score: float
    risk_budget_utilization: float
    diversification_score: float
    portfolio_return_score: float
    drawdown_pressure: float
    execution_cost_score: float
    trace_id: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PortfolioObservation":
        return cls(
            market_regime=_norm(value.get("market_regime") or value.get("regime")),
            portfolio_scope=_norm(value.get("portfolio_scope") or value.get("scope") or value.get("account_group")),
            direction=_norm(value.get("direction") or value.get("bias") or "FLAT"),
            sample_count=int(_float(value.get("sample_count") or value.get("samples"))),
            exposure_score=_float(value.get("exposure_score") or value.get("exposure")),
            correlation_score=_float(value.get("correlation_score") or value.get("correlation")),
            risk_budget_utilization=_float(value.get("risk_budget_utilization") or value.get("risk_budget")),
            diversification_score=_float(value.get("diversification_score") or value.get("diversification")),
            portfolio_return_score=_float(value.get("portfolio_return_score") or value.get("return_score")),
            drawdown_pressure=_float(value.get("drawdown_pressure") or value.get("drawdown")),
            execution_cost_score=_float(value.get("execution_cost_score") or value.get("cost_score")),
            trace_id=str(value.get("trace_id") or value.get("trace") or "").strip(),
        )

    @property
    def portfolio_key(self) -> str:
        return f"{self.market_regime}:{self.portfolio_scope}:{self.direction}"

    @property
    def has_market_regime(self) -> bool:
        return self.market_regime not in {"", "UNKNOWN"}

    @property
    def is_usable(self) -> bool:
        return (
            self.has_market_regime
            and self.portfolio_scope not in {"", "UNKNOWN"}
            and self.sample_count > 0
            and self.exposure_score > 0
            and self.correlation_score >= 0
            and self.risk_budget_utilization > 0
            and self.diversification_score > 0
            and self.portfolio_return_score > 0
            and self.drawdown_pressure >= 0
            and self.execution_cost_score >= 0
            and bool(self.trace_id)
        )
