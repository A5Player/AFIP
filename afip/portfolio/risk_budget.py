"""Portfolio risk budget model for production portfolio controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class RiskBudgetResult:
    """Risk budget evaluation against portfolio equity."""

    status: str
    equity: float
    risk_amount: float
    risk_ratio: float
    maximum_risk_ratio: float
    within_budget: bool
    reason: str


class RiskBudget:
    """Evaluate planned portfolio risk against available equity."""

    def evaluate(
        self,
        portfolio_equity: Mapping[str, object] | object,
        proposed_risk_amount: float,
        limits: Mapping[str, object] | None = None,
    ) -> RiskBudgetResult:
        limits = limits or {}
        status = self._text(portfolio_equity, "status")
        equity = self._number(portfolio_equity, "total_equity", self._number(portfolio_equity, "equity"))
        maximum_ratio = self._number(limits, "maximum_risk_ratio", 0.02)
        risk_amount = round(max(0.0, float(proposed_risk_amount or 0.0)), 8)

        if status not in {"PORTFOLIO_EQUITY_READY", "EQUITY_READY"}:
            return RiskBudgetResult("RISK_BUDGET_REVIEW", equity, risk_amount, 0.0, maximum_ratio, False, "portfolio_equity_not_ready")
        if equity <= 0:
            return RiskBudgetResult("RISK_BUDGET_REVIEW", equity, risk_amount, 0.0, maximum_ratio, False, "equity_not_positive")
        risk_ratio = round(risk_amount / equity, 8)
        if risk_ratio > maximum_ratio:
            return RiskBudgetResult("RISK_BUDGET_REVIEW", equity, risk_amount, risk_ratio, maximum_ratio, False, "risk_ratio_above_limit")
        return RiskBudgetResult("RISK_BUDGET_READY", equity, risk_amount, risk_ratio, maximum_ratio, True, "risk_budget_ready")

    @staticmethod
    def _number(value: Mapping[str, object] | object, key: str, default: float = 0.0) -> float:
        raw = value.get(key, default) if isinstance(value, Mapping) else getattr(value, key, default)
        try:
            return float(raw)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _text(value: Mapping[str, object] | object, key: str) -> str:
        raw = value.get(key, "") if isinstance(value, Mapping) else getattr(value, key, "")
        return str(raw)
