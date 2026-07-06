"""Production Milestone E Pack 8 macro context observation model."""

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
class MacroObservation:
    """Single data-derived macro observation for financial market context."""

    market_regime: str
    macro_theme: str
    direction: str
    sample_count: int
    dxy_alignment_score: float
    yield_alignment_score: float
    inflation_surprise_score: float
    labor_market_pressure: float
    policy_rate_bias_score: float
    news_risk_score: float
    macro_consensus_score: float
    execution_cost_score: float
    trace_id: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "MacroObservation":
        return cls(
            market_regime=_norm(value.get("market_regime") or value.get("regime")),
            macro_theme=_norm(value.get("macro_theme") or value.get("theme") or value.get("macro_context")),
            direction=_norm(value.get("direction") or value.get("bias") or "FLAT"),
            sample_count=int(_float(value.get("sample_count") or value.get("samples"))),
            dxy_alignment_score=_float(value.get("dxy_alignment_score") or value.get("dxy_alignment")),
            yield_alignment_score=_float(value.get("yield_alignment_score") or value.get("yield_alignment")),
            inflation_surprise_score=_float(value.get("inflation_surprise_score") or value.get("inflation_surprise")),
            labor_market_pressure=_float(value.get("labor_market_pressure") or value.get("labor_pressure")),
            policy_rate_bias_score=_float(value.get("policy_rate_bias_score") or value.get("policy_rate_bias")),
            news_risk_score=_float(value.get("news_risk_score") or value.get("news_risk")),
            macro_consensus_score=_float(value.get("macro_consensus_score") or value.get("macro_consensus")),
            execution_cost_score=_float(value.get("execution_cost_score") or value.get("cost_score")),
            trace_id=str(value.get("trace_id") or value.get("trace") or "").strip(),
        )

    @property
    def macro_key(self) -> str:
        return f"{self.market_regime}:{self.macro_theme}:{self.direction}"

    @property
    def has_market_regime(self) -> bool:
        return self.market_regime not in {"", "UNKNOWN"}

    @property
    def is_usable(self) -> bool:
        return (
            self.has_market_regime
            and self.macro_theme not in {"", "UNKNOWN"}
            and self.sample_count > 0
            and self.dxy_alignment_score > 0
            and self.yield_alignment_score > 0
            and self.inflation_surprise_score >= 0
            and self.labor_market_pressure >= 0
            and self.policy_rate_bias_score > 0
            and self.news_risk_score >= 0
            and self.macro_consensus_score > 0
            and self.execution_cost_score >= 0
            and bool(self.trace_id)
        )
