"""Risk-adjusted return calculation for production performance review."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class RiskAdjustedReturnResult:
    """Risk-adjusted return output."""

    status: str
    ready: bool
    return_ratio: float
    maximum_drawdown_ratio: float
    risk_adjusted_ratio: float
    reason: str


class RiskAdjustedReturn:
    """Calculate a conservative return-to-drawdown ratio."""

    def calculate(self, portfolio_return: Mapping[str, object] | object, risk_snapshot: Mapping[str, object] | object) -> RiskAdjustedReturnResult:
        return_status = str(_read_value(portfolio_return, "status", ""))
        risk_status = str(_read_value(risk_snapshot, "status", ""))
        return_ratio = float(_read_value(portfolio_return, "return_ratio", 0.0) or 0.0)
        maximum_drawdown_ratio = float(_read_value(risk_snapshot, "maximum_drawdown_ratio", 0.0) or 0.0)
        if return_status != "PORTFOLIO_RETURN_READY":
            return RiskAdjustedReturnResult("RISK_ADJUSTED_RETURN_REVIEW", False, return_ratio, maximum_drawdown_ratio, 0.0, "portfolio_return_not_ready")
        if risk_status not in {"PORTFOLIO_RISK_READY", "RISK_SNAPSHOT_READY"}:
            return RiskAdjustedReturnResult("RISK_ADJUSTED_RETURN_REVIEW", False, return_ratio, maximum_drawdown_ratio, 0.0, "risk_snapshot_not_ready")
        if maximum_drawdown_ratio <= 0.0:
            return RiskAdjustedReturnResult("RISK_ADJUSTED_RETURN_REVIEW", False, return_ratio, maximum_drawdown_ratio, 0.0, "drawdown_ratio_not_positive")
        ratio = return_ratio / maximum_drawdown_ratio
        return RiskAdjustedReturnResult("RISK_ADJUSTED_RETURN_READY", True, return_ratio, maximum_drawdown_ratio, round(ratio, 6), "risk_adjusted_return_calculated")


def _read_value(source: Mapping[str, object] | object, name: str, default: object = None) -> object:
    if isinstance(source, Mapping):
        return source.get(name, default)
    return getattr(source, name, default)
