from afip.accounting.exposure_reconciliation import ExposureReconciliation
from afip.accounting.position_accounting_entry import PositionAccountingEntryBuilder
from afip.accounting.position_ledger import PositionLedger
from afip.runtime.production_milestone_b_position_runtime import ProductionMilestoneBPositionRuntime


def _settlement_result():
    return {
        "settled": True,
        "settlement_id": "AFIP-SETTLEMENT-000013-APPROVED-BUY",
        "position_quantity": 0.04,
        "average_price": 2367.25,
        "notional_value": 94.69,
        "reason": "order_settled_for_position_accounting",
    }


def _lifecycle_record():
    return {
        "account_id": "ACCOUNT_A",
        "symbol": "GOLD#",
        "action": "BUY",
    }


def test_position_accounting_entry_builder_records_settled_order():
    entry = PositionAccountingEntryBuilder().build(_settlement_result(), _lifecycle_record(), sequence=13)
    assert entry.accounting_state == "POSITION_ACCOUNTING_READY"
    assert entry.account_id == "ACCOUNT_A"
    assert entry.symbol == "GOLD#"
    assert entry.side == "LONG"
    assert entry.quantity == 0.04


def test_position_accounting_entry_builder_routes_unsettled_order_to_review():
    settlement = {**_settlement_result(), "settled": False, "position_quantity": 0.0}
    entry = PositionAccountingEntryBuilder().build(settlement, _lifecycle_record(), sequence=13)
    assert entry.accounting_state == "POSITION_ACCOUNTING_REVIEW"
    assert entry.side == "FLAT"
    assert entry.quantity == 0.0


def test_position_ledger_summarizes_long_exposure():
    builder = PositionAccountingEntryBuilder()
    entries = [
        builder.build(_settlement_result(), _lifecycle_record(), sequence=13),
        builder.build({**_settlement_result(), "position_quantity": 0.01, "notional_value": 23.6725}, _lifecycle_record(), sequence=14),
    ]
    snapshot = PositionLedger().summarize(entries)
    assert snapshot.status == "POSITION_LEDGER_READY"
    assert snapshot.net_quantity == 0.05
    assert snapshot.side == "LONG"
    assert snapshot.entry_count == 2


def test_position_ledger_summarizes_flat_when_long_and_short_offset():
    builder = PositionAccountingEntryBuilder()
    long_entry = builder.build(_settlement_result(), _lifecycle_record(), sequence=13)
    short_entry = builder.build({**_settlement_result(), "position_quantity": -0.04}, _lifecycle_record(), sequence=14)
    snapshot = PositionLedger().summarize([long_entry, short_entry])
    assert snapshot.status == "POSITION_LEDGER_READY"
    assert snapshot.net_quantity == 0.0
    assert snapshot.side == "FLAT"


def test_exposure_reconciliation_accepts_quantity_within_limit():
    entry = PositionAccountingEntryBuilder().build(_settlement_result(), _lifecycle_record(), sequence=13)
    snapshot = PositionLedger().summarize([entry])
    result = ExposureReconciliation().evaluate(snapshot, {"maximum_net_quantity": 0.10})
    assert result.status == "EXPOSURE_RECONCILIATION_READY"
    assert result.reconciled is True
    assert result.exposure_ratio == 0.4


def test_exposure_reconciliation_rejects_quantity_above_limit():
    entry = PositionAccountingEntryBuilder().build(_settlement_result(), _lifecycle_record(), sequence=13)
    snapshot = PositionLedger().summarize([entry])
    result = ExposureReconciliation().evaluate(snapshot, {"maximum_net_quantity": 0.02})
    assert result.status == "EXPOSURE_RECONCILIATION_REVIEW"
    assert result.reconciled is False
    assert "net_quantity_limit_exceeded" in result.failed_rules


def test_exposure_reconciliation_rejects_empty_ledger():
    snapshot = PositionLedger().summarize([])
    result = ExposureReconciliation().evaluate(snapshot, {"maximum_net_quantity": 0.10})
    assert result.reconciled is False
    assert "position_ledger_not_ready" in result.failed_rules


def test_production_milestone_b_position_runtime_integrates_accounting_and_reconciliation():
    result = ProductionMilestoneBPositionRuntime().run(
        settlement_result=_settlement_result(),
        lifecycle_record=_lifecycle_record(),
        exposure_limits={"maximum_net_quantity": 0.10},
        sequence=13,
    )
    assert result.status == "PRODUCTION_MILESTONE_B_POSITION_READY"
    assert result.accounting_state == "POSITION_ACCOUNTING_READY"
    assert result.ledger_status == "POSITION_LEDGER_READY"
    assert result.reconciliation_status == "EXPOSURE_RECONCILIATION_READY"
    assert result.net_quantity == 0.04
    assert result.side == "LONG"
    assert result.failed_rules == ()
