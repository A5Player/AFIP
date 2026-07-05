"""Production Milestone B Pack 16 runtime for portfolio risk controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from afip.portfolio.portfolio_risk import PortfolioRisk


@dataclass(frozen=True)
class ProductionMilestoneBRiskRuntimeResult:
    """Integrated Pack 16 runtime result."""

    status: str
    portfolio_risk_status: str
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


class ProductionMilestoneBRiskRuntime:
    """Run portfolio risk controls against equity and open positions."""

    def __init__(self) -> None:
        self.portfolio_risk = PortfolioRisk()

    def run(
        self,
        portfolio_equity: Mapping[str, object] | object,
        proposed_risk_amount: float,
        positions: Iterable[Mapping[str, object]],
        risk_limits: Mapping[str, object] | None = None,
    ) -> ProductionMilestoneBRiskRuntimeResult:
        summary = self.portfolio_risk.evaluate(portfolio_equity, proposed_risk_amount, positions, risk_limits)
        return ProductionMilestoneBRiskRuntimeResult(
            status="PRODUCTION_MILESTONE_B_RISK_READY" if summary.approved else "PRODUCTION_MILESTONE_B_RISK_REVIEW",
            portfolio_risk_status=summary.status,
            risk_budget_status=summary.risk_budget_status,
            exposure_status=summary.exposure_status,
            concentration_status=summary.concentration_status,
            approved=summary.approved,
            total_equity=summary.total_equity,
            proposed_risk_amount=summary.proposed_risk_amount,
            gross_exposure=summary.gross_exposure,
            risk_ratio=summary.risk_ratio,
            exposure_ratio=summary.exposure_ratio,
            concentration_ratio=summary.concentration_ratio,
            failed_rules=summary.failed_rules,
        )
