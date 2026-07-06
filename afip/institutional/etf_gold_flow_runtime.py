"""Gold ETF flow assessment for institutional allocation context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class EtfGoldFlowAssessment:
    """ETF allocation flow assessment for gold demand context."""

    status: str
    flow_bias: str
    confidence_score: float
    net_tonnes_change: float
    value_change_usd: float
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "flow_bias": self.flow_bias,
            "confidence_score": self.confidence_score,
            "net_tonnes_change": self.net_tonnes_change,
            "value_change_usd": self.value_change_usd,
            "reason": self.reason,
        }


class EtfGoldFlowRuntime:
    """Score ETF gold allocation flow as supportive, pressure, or neutral."""

    def assess(self, values: Mapping[str, object]) -> EtfGoldFlowAssessment:
        tonnes = self._to_float(values.get("etf_gold_tonnes_change"))
        value_change = self._to_float(values.get("etf_value_change_usd"))
        confidence = min(92.0, 45.0 + abs(tonnes) * 3.5)

        if tonnes >= 3.0:
            bias = "GOLD_SUPPORTIVE"
            reason = "gold_etf_allocation_inflow"
        elif tonnes <= -3.0:
            bias = "GOLD_PRESSURE"
            reason = "gold_etf_allocation_outflow"
        else:
            bias = "NEUTRAL"
            confidence = 42.0
            reason = "gold_etf_flow_neutral"

        return EtfGoldFlowAssessment(
            status="ETF_GOLD_FLOW_READY",
            flow_bias=bias,
            confidence_score=round(confidence, 2),
            net_tonnes_change=round(tonnes, 2),
            value_change_usd=round(value_change, 2),
            reason=reason,
        )

    def assess_dict(self, values: Mapping[str, object]) -> dict[str, object]:
        return self.assess(values).as_dict()

    @staticmethod
    def _to_float(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
