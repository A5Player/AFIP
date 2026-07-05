"""Production Milestone B Pack 20 portfolio runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Mapping

from afip.portfolio.production_portfolio import ProductionPortfolio


@dataclass(frozen=True)
class ProductionMilestoneBPortfolioRuntimeResult:
    """Integrated Pack 20 runtime result."""

    status: str
    portfolio_status: str
    ready: bool
    equity_status: str
    risk_status: str
    capital_status: str
    analytics_status: str
    account_count: int
    position_count: int
    total_balance: float
    total_equity: float
    total_net_asset_value: float
    proposed_risk_amount: float
    proposed_allocation: float
    gross_exposure: float
    risk_ratio: float
    exposure_ratio: float
    concentration_ratio: float
    available_capital: float
    allocation_ratio: float
    utilization_ratio: float
    trend_direction: str
    trend_strength_percent: float
    risk_efficiency_ratio: float
    capital_utilization_percent: float
    failed_rules: tuple[str, ...]
    reason: str


class ProductionMilestoneBPortfolioRuntime:
    """Run production portfolio state across equity, risk, capital, and analytics."""

    def __init__(self) -> None:
        self.production_portfolio = ProductionPortfolio()

    def run(
        self,
        account_snapshots: Iterable[Mapping[str, object]],
        positions: Iterable[Mapping[str, object]],
        proposed_risk_amount: float,
        proposed_allocation: float,
        position_requests: Iterable[Mapping[str, object]],
        equity_observations: Iterable[Mapping[str, object]] | None = None,
        runtime_policy: Mapping[str, object] | None = None,
    ) -> ProductionMilestoneBPortfolioRuntimeResult:
        portfolio = self.production_portfolio.build(
            account_snapshots,
            positions,
            proposed_risk_amount,
            proposed_allocation,
            position_requests,
            equity_observations,
            runtime_policy,
        )
        return ProductionMilestoneBPortfolioRuntimeResult(
            status="PRODUCTION_MILESTONE_B_PORTFOLIO_READY" if portfolio.ready else "PRODUCTION_MILESTONE_B_PORTFOLIO_REVIEW",
            portfolio_status=portfolio.status,
            ready=portfolio.ready,
            equity_status=portfolio.equity_status,
            risk_status=portfolio.risk_status,
            capital_status=portfolio.capital_status,
            analytics_status=portfolio.analytics_status,
            account_count=portfolio.account_count,
            position_count=portfolio.position_count,
            total_balance=portfolio.total_balance,
            total_equity=portfolio.total_equity,
            total_net_asset_value=portfolio.total_net_asset_value,
            proposed_risk_amount=portfolio.proposed_risk_amount,
            proposed_allocation=portfolio.proposed_allocation,
            gross_exposure=portfolio.gross_exposure,
            risk_ratio=portfolio.risk_ratio,
            exposure_ratio=portfolio.exposure_ratio,
            concentration_ratio=portfolio.concentration_ratio,
            available_capital=portfolio.available_capital,
            allocation_ratio=portfolio.allocation_ratio,
            utilization_ratio=portfolio.utilization_ratio,
            trend_direction=portfolio.trend_direction,
            trend_strength_percent=portfolio.trend_strength_percent,
            risk_efficiency_ratio=portfolio.risk_efficiency_ratio,
            capital_utilization_percent=portfolio.capital_utilization_percent,
            failed_rules=portfolio.failed_rules,
            reason=portfolio.reason,
        )

    def run_dict(
        self,
        account_snapshots: Iterable[Mapping[str, object]],
        positions: Iterable[Mapping[str, object]],
        proposed_risk_amount: float,
        proposed_allocation: float,
        position_requests: Iterable[Mapping[str, object]],
        equity_observations: Iterable[Mapping[str, object]] | None = None,
        runtime_policy: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        return asdict(
            self.run(
                account_snapshots,
                positions,
                proposed_risk_amount,
                proposed_allocation,
                position_requests,
                equity_observations,
                runtime_policy,
            )
        )
