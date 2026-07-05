"""Production Milestone B Pack 14 runtime for mark-to-market valuation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from afip.accounting.position_valuation import PositionValuation
from afip.accounting.unrealized_pnl import UnrealizedPnlCalculator
from afip.accounting.valuation_reconciliation import ValuationReconciliation


@dataclass(frozen=True)
class ProductionMilestoneBValuationRuntimeResult:
    """Integrated Pack 14 runtime result."""

    status: str
    valuation_status: str
    pnl_status: str
    reconciliation_status: str
    reconciled: bool
    account_id: str
    symbol: str
    side: str
    market_price: float
    market_value: float
    cost_basis: float
    unrealized_pnl: float
    return_ratio: float
    failed_rules: tuple[str, ...]


class ProductionMilestoneBValuationRuntime:
    """Run position valuation, unrealized PnL, and reconciliation controls."""

    def __init__(self) -> None:
        self.valuation = PositionValuation()
        self.pnl = UnrealizedPnlCalculator()
        self.reconciliation = ValuationReconciliation()

    def run(
        self,
        ledger_snapshot: Mapping[str, object] | object | None = None,
        market_snapshot: Mapping[str, object] | None = None,
        valuation_limits: Mapping[str, object] | None = None,
    ) -> ProductionMilestoneBValuationRuntimeResult:
        valuation = self.valuation.value(ledger_snapshot, market_snapshot)
        pnl = self.pnl.calculate(valuation)
        reconciliation = self.reconciliation.evaluate(valuation, pnl, valuation_limits)
        ready = valuation.status == "POSITION_VALUATION_READY" and reconciliation.reconciled
        status = "PRODUCTION_MILESTONE_B_VALUATION_READY" if ready else "PRODUCTION_MILESTONE_B_VALUATION_REVIEW"
        return ProductionMilestoneBValuationRuntimeResult(
            status=status,
            valuation_status=valuation.status,
            pnl_status=pnl.status,
            reconciliation_status=reconciliation.status,
            reconciled=reconciliation.reconciled,
            account_id=valuation.account_id,
            symbol=valuation.symbol,
            side=valuation.side,
            market_price=valuation.market_price,
            market_value=valuation.market_value,
            cost_basis=valuation.cost_basis,
            unrealized_pnl=pnl.unrealized_pnl,
            return_ratio=pnl.return_ratio,
            failed_rules=reconciliation.failed_rules,
        )
