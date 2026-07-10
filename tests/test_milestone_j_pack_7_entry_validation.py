from datetime import datetime, timezone

from afip.dashboard_ui.runtime import DashboardUIRuntime
from afip.entry_validation import EntryValidationRuntime


def _allocation(**overrides):
    item = {
        "opportunity_id": "OPP_A",
        "symbol": "GOLD#",
        "direction": "BUY",
        "trade_grade": "A",
        "allocated_units": 2,
        "lot_per_unit": 0.01,
        "eligible": True,
    }
    item.update(overrides)
    return item


def test_entry_approved_when_all_requirements_pass():
    report = EntryValidationRuntime().evaluate_one({
        "market_regime_ready": True,
        "conflict_allowed": True,
        "risk_allowed": True,
        "timing_allowed": True,
        "spread_allowed": True,
        "unit_allocations": [_allocation()],
    })
    assert report.entry_approved is True
    assert report.approved_units == 2
    assert report.total_lot == 0.02


def test_high_conflict_forces_wait():
    report = EntryValidationRuntime().evaluate_one({
        "market_regime_ready": True,
        "conflict_allowed": False,
        "unit_allocations": [_allocation()],
    })
    assert report.status == "WAITING"
    assert "unresolved_conflict_blocks_entry" in report.validations[0].block_reasons


def test_spread_or_timing_block_entry():
    report = EntryValidationRuntime().evaluate_one({
        "market_regime_ready": True,
        "timing_allowed": False,
        "spread_allowed": False,
        "unit_allocations": [_allocation()],
    })
    assert report.entry_approved is False
    assert "market_timing_blocks_entry" in report.validations[0].block_reasons
    assert "spread_or_trading_cost_blocks_entry" in report.validations[0].block_reasons


def test_fixed_unit_policy_is_required():
    report = EntryValidationRuntime().evaluate_one({
        "market_regime_ready": True,
        "unit_allocations": [_allocation(lot_per_unit=0.02)],
    })
    assert report.entry_approved is False
    assert "unit_allocation_not_approved" in report.validations[0].block_reasons


def test_direct_execution_disabled_and_review_time_deterministic():
    now = datetime(2026, 7, 10, 9, 0, tzinfo=timezone.utc)
    report = EntryValidationRuntime().evaluate_one({
        "current_time_utc": now,
        "market_regime_ready": True,
        "unit_allocations": [_allocation()],
    })
    assert report.direct_execution is False
    assert report.next_review_time_utc == "2026-07-10T09:05:00+00:00"


def test_dashboard_contains_bilingual_entry_validation_panel():
    report = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER", "balance": 2000})
    panel = next(item for item in report.panels if item.panel_id == "entry_validation")
    assert panel.title_en == "Entry Validation Engine"
    assert panel.title_th == "กลไกตรวจสอบจุดเข้า"
