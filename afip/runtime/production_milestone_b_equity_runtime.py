"""Production Milestone B Pack 15 runtime for portfolio equity accounting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from afip.portfolio.equity_calculator import EquityCalculator
from afip.portfolio.equity_reconciliation import EquityReconciliation
from afip.portfolio.net_asset_value import NetAssetValueCalculator
from afip.portfolio.portfolio_equity import PortfolioEquity


@dataclass(frozen=True)
class ProductionMilestoneBEquityRuntimeResult:
    """Integrated Pack 15 runtime result."""

    status: str
    equity_status: str
    nav_status: str
    portfolio_status: str
    reconciliation_status: str
    reconciled: bool
    account_id: str
    balance: float
    realized_pnl: float
    unrealized_pnl: float
    equity: float
    net_asset_value: float
    total_equity: float
    failed_rules: tuple[str, ...]


class ProductionMilestoneBEquityRuntime:
    """Run equity, NAV, portfolio summary, and reconciliation controls."""

    def __init__(self) -> None:
        self.equity = EquityCalculator()
        self.nav = NetAssetValueCalculator()
        self.portfolio = PortfolioEquity()
        self.reconciliation = EquityReconciliation()

    def run(
        self,
        account_snapshot: Mapping[str, object] | None = None,
        position_value: float = 0.0,
        equity_limits: Mapping[str, object] | None = None,
    ) -> ProductionMilestoneBEquityRuntimeResult:
        equity_snapshot = self.equity.calculate(account_snapshot)
        nav_result = self.nav.calculate(equity_snapshot, position_value)
        portfolio_summary = self.portfolio.summarize([equity_snapshot])
        reconciliation = self.reconciliation.evaluate(equity_snapshot, nav_result, equity_limits)
        ready = (
            equity_snapshot.status == "EQUITY_READY"
            and nav_result.status == "NET_ASSET_VALUE_READY"
            and portfolio_summary.status == "PORTFOLIO_EQUITY_READY"
            and reconciliation.reconciled
        )
        status = "PRODUCTION_MILESTONE_B_EQUITY_READY" if ready else "PRODUCTION_MILESTONE_B_EQUITY_REVIEW"
        return ProductionMilestoneBEquityRuntimeResult(
            status=status,
            equity_status=equity_snapshot.status,
            nav_status=nav_result.status,
            portfolio_status=portfolio_summary.status,
            reconciliation_status=reconciliation.status,
            reconciled=reconciliation.reconciled,
            account_id=equity_snapshot.account_id,
            balance=equity_snapshot.balance,
            realized_pnl=equity_snapshot.realized_pnl,
            unrealized_pnl=equity_snapshot.unrealized_pnl,
            equity=equity_snapshot.equity,
            net_asset_value=nav_result.net_asset_value,
            total_equity=portfolio_summary.total_equity,
            failed_rules=reconciliation.failed_rules,
        )
