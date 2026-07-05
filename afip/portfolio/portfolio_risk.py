"""Portfolio risk summary builder for AFIP production controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from afip.portfolio.concentration_risk import ConcentrationRisk
from afip.portfolio.exposure_limit import ExposureLimit
from afip.portfolio.risk_budget import RiskBudget


@dataclass(frozen=True)
class PortfolioRiskSummary:
    """Aggregated portfolio risk control result."""

    status: str
    risk_budget_status: str
    exposure_status: str
    concentration_status: str
    approved: bool
    total_equity: float
    proposed_risk_amount: float
    gross_exposure: float
    risk_ratio: float
    exposure_ratio: float
    concentration_ratio: float
    failed_rules: tuple[str, ...]


class PortfolioRisk:
    """Combine risk budget, exposure, and concentration evaluations."""

    def __init__(self) -> None:
        self.risk_budget = RiskBudget()
        self.exposure_limit = ExposureLimit()
        self.concentration_risk = ConcentrationRisk()

    def evaluate(
        self,
        portfolio_equity: Mapping[str, object] | object,
        proposed_risk_amount: float,
        positions: Iterable[Mapping[str, object]],
        limits: Mapping[str, object] | None = None,
    ) -> PortfolioRiskSummary:
        limits = limits or {}
        equity = self._number(portfolio_equity, "total_equity", self._number(portfolio_equity, "equity"))
        position_list = list(positions)
        gross_exposure = sum(abs(self._number(position, "market_value", self._number(position, "value"))) for position in position_list)
        budget = self.risk_budget.evaluate(portfolio_equity, proposed_risk_amount, limits)
        exposure = self.exposure_limit.evaluate(gross_exposure, equity, limits)
        concentration = self.concentration_risk.evaluate(position_list, limits)
        failed: list[str] = []
        if not budget.within_budget:
            failed.append(budget.reason)
        if not exposure.within_limit:
            failed.append(exposure.reason)
        if not concentration.within_limit:
            failed.append(concentration.reason)
        approved = not failed
        return PortfolioRiskSummary(
            status="PORTFOLIO_RISK_READY" if approved else "PORTFOLIO_RISK_REVIEW",
            risk_budget_status=budget.status,
            exposure_status=exposure.status,
            concentration_status=concentration.status,
            approved=approved,
            total_equity=round(equity, 8),
            proposed_risk_amount=budget.risk_amount,
            gross_exposure=round(gross_exposure, 8),
            risk_ratio=budget.risk_ratio,
            exposure_ratio=exposure.exposure_ratio,
            concentration_ratio=concentration.largest_position_ratio,
            failed_rules=tuple(failed),
        )

    @staticmethod
    def _number(value: Mapping[str, object] | object, key: str, default: float = 0.0) -> float:
        raw = value.get(key, default) if isinstance(value, Mapping) else getattr(value, key, default)
        try:
            return float(raw)
        except (TypeError, ValueError):
            return default
