"""Production Milestone B Pack 13 runtime for position accounting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from afip.accounting.exposure_reconciliation import ExposureReconciliation
from afip.accounting.position_accounting_entry import PositionAccountingEntryBuilder
from afip.accounting.position_ledger import PositionLedger


@dataclass(frozen=True)
class ProductionMilestoneBPositionRuntimeResult:
    """Integrated Pack 13 runtime result."""

    status: str
    accounting_state: str
    ledger_status: str
    reconciliation_status: str
    reconciled: bool
    account_id: str
    symbol: str
    net_quantity: float
    side: str
    average_price: float
    exposure_ratio: float
    failed_rules: tuple[str, ...]


class ProductionMilestoneBPositionRuntime:
    """Run settlement-to-position accounting and exposure reconciliation."""

    def __init__(self) -> None:
        self.entry_builder = PositionAccountingEntryBuilder()
        self.ledger = PositionLedger()
        self.reconciliation = ExposureReconciliation()

    def run(
        self,
        settlement_result: Mapping[str, object] | object | None = None,
        lifecycle_record: Mapping[str, object] | object | None = None,
        exposure_limits: Mapping[str, object] | None = None,
        sequence: int = 13,
    ) -> ProductionMilestoneBPositionRuntimeResult:
        entry = self.entry_builder.build(settlement_result, lifecycle_record, sequence=sequence)
        snapshot = self.ledger.summarize([entry])
        reconciliation = self.reconciliation.evaluate(snapshot, exposure_limits or {"maximum_net_quantity": 1.0})
        ready = entry.accounting_state == "POSITION_ACCOUNTING_READY" and reconciliation.reconciled
        status = "PRODUCTION_MILESTONE_B_POSITION_READY" if ready else "PRODUCTION_MILESTONE_B_POSITION_REVIEW"
        return ProductionMilestoneBPositionRuntimeResult(
            status=status,
            accounting_state=entry.accounting_state,
            ledger_status=snapshot.status,
            reconciliation_status=reconciliation.status,
            reconciled=reconciliation.reconciled,
            account_id=snapshot.account_id,
            symbol=snapshot.symbol,
            net_quantity=snapshot.net_quantity,
            side=snapshot.side,
            average_price=snapshot.average_price,
            exposure_ratio=reconciliation.exposure_ratio,
            failed_rules=reconciliation.failed_rules,
        )
