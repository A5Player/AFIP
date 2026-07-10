from datetime import datetime, timezone
from afip.unit_allocation import UnitAllocationRuntime
from afip.dashboard_ui.runtime import DashboardUIRuntime

def _score(identifier="A", grade="A+", final=.95, eligible=True, direction="BUY"):
    return {"opportunity_id": identifier, "symbol": "GOLD#", "direction": direction, "grade": grade, "final_score": final, "eligible": eligible}

def test_fixed_unit_and_capital_allocation():
    report = UnitAllocationRuntime().evaluate_one({"profile_name":"Balanced", "capital_per_unit":500, "available_capital":1200, "maximum_units":3, "trade_scores":[_score()]})
    assert report.allocated_units == 2 and report.lot_per_unit == 0.01 and report.total_lot == 0.02

def test_grade_caps_units():
    assert UnitAllocationRuntime().evaluate_one({"available_capital":5000, "maximum_units":3, "trade_scores":[_score(grade="B")]}).allocated_units == 1

def test_upstream_or_risk_block_results_zero_units():
    report = UnitAllocationRuntime().evaluate_one({"available_capital":5000, "risk_allowed":False, "trade_scores":[_score()]})
    assert report.allocated_units == 0 and report.status == "WAITING"

def test_never_increases_lot_per_unit():
    report = UnitAllocationRuntime().evaluate_one({"available_capital":100000, "maximum_units":99, "trade_scores":[_score()]})
    assert report.lot_per_unit == 0.01 and report.allocated_units == 3

def test_direct_execution_disabled_and_review_time_deterministic():
    now = datetime(2026,7,10,8,0,tzinfo=timezone.utc)
    report = UnitAllocationRuntime().evaluate_one({"current_time_utc":now, "available_capital":1000, "trade_scores":[_score()]})
    assert report.direct_execution is False and report.next_review_time_utc == "2026-07-10T08:10:00+00:00"

def test_dashboard_contains_bilingual_unit_allocation_panel():
    report = DashboardUIRuntime().evaluate_one({"broker":"XM", "symbol":"GOLD#", "mode":"PAPER", "balance":2000, "opportunities":[]})
    panel = next(item for item in report.panels if item.panel_id == "unit_allocation")
    assert panel.title_en == "Unit Allocation Engine" and panel.title_th == "กลไกจัดสรร Unit"
