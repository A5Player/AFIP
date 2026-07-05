"""Risk efficiency analytics for portfolio production controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class RiskEfficiencyResult:
    """Risk efficiency analytics output."""

    status: str
    ready: bool
    return_percent: float
    maximum_drawdown_percent: float
    efficiency_ratio: float
    reason: str


class RiskEfficiency:
    """Compare portfolio return with drawdown consumption."""

    def calculate(self, performance_summary: Mapping[str, object] | object, risk_snapshot: Mapping[str, object] | object) -> RiskEfficiencyResult:
        performance_status = str(_read_value(performance_summary, "status", ""))
        risk_status = str(_read_value(risk_snapshot, "status", ""))
        return_percent = float(_read_value(performance_summary, "return_percent", 0.0) or 0.0)
        drawdown_ratio = float(_read_value(risk_snapshot, "maximum_drawdown_ratio", 0.0) or 0.0)
        if performance_status not in {"PERFORMANCE_ATTRIBUTION_READY", "PERFORMANCE_SUMMARY_READY"}:
            return RiskEfficiencyResult("RISK_EFFICIENCY_REVIEW", False, return_percent, round(drawdown_ratio * 100.0, 4), 0.0, "performance_summary_not_ready")
        if risk_status != "PORTFOLIO_RISK_READY":
            return RiskEfficiencyResult("RISK_EFFICIENCY_REVIEW", False, return_percent, round(drawdown_ratio * 100.0, 4), 0.0, "portfolio_risk_not_ready")
        if drawdown_ratio <= 0:
            return RiskEfficiencyResult("RISK_EFFICIENCY_REVIEW", False, return_percent, 0.0, 0.0, "drawdown_ratio_not_positive")
        drawdown_percent = round(drawdown_ratio * 100.0, 4)
        ratio = round(return_percent / drawdown_percent, 4)
        return RiskEfficiencyResult("RISK_EFFICIENCY_READY", True, return_percent, drawdown_percent, ratio, "risk_efficiency_ready")


def _read_value(source: Mapping[str, object] | object, name: str, default: object = None) -> object:
    if isinstance(source, Mapping):
        return source.get(name, default)
    return getattr(source, name, default)
