from datetime import datetime, timezone
from afip.bond_yield_intelligence import BondYieldIntelligenceRuntime
from afip.dashboard_ui import DashboardUIRuntime
NOW=datetime(2026,7,10,7,0,tzinfo=timezone.utc)
def base(**extra):
    d={"broker":"XM","symbol":"GOLD#","current_time_utc":NOW,"live_execution_enabled":False,"bond_yield_observations":[]}; d.update(extra); return d

def test_rising_real_yield_is_bearish_gold_context():
    r=BondYieldIntelligenceRuntime().evaluate_one(base(bond_yield_observations=[{"us2y_yield":4.5,"previous_us2y_yield":4.4,"us10y_yield":4.4,"previous_us10y_yield":4.3,"real_yield":2.1,"previous_real_yield":2.0}]))
    assert r.status=="READY" and r.aggregate_gold_effect=="BEARISH" and r.rising_real_count==1

def test_falling_real_yield_is_bullish_gold_context():
    r=BondYieldIntelligenceRuntime().evaluate_one(base(bond_yield_observations=[{"us2y_yield":4.3,"previous_us2y_yield":4.4,"us10y_yield":4.2,"previous_us10y_yield":4.3,"real_yield":1.9,"previous_real_yield":2.0}]))
    assert r.aggregate_gold_effect=="BULLISH" and r.falling_real_count==1

def test_inverted_curve_is_detected():
    r=BondYieldIntelligenceRuntime().evaluate_one(base(bond_yield_observations=[{"us2y_yield":4.6,"us10y_yield":4.2,"real_yield":2.0}]))
    assert r.inverted_curve_count==1 and r.observations[0].curve_shape=="INVERTED"

def test_stable_yields_are_neutral():
    r=BondYieldIntelligenceRuntime().evaluate_one(base(bond_yield_observations=[{"us2y_yield":4.4,"previous_us2y_yield":4.4,"us10y_yield":4.3,"previous_us10y_yield":4.3,"real_yield":2.0,"previous_real_yield":2.0}]))
    assert r.aggregate_gold_effect=="NEUTRAL" and r.aggregate_yield_trend=="STABLE"

def test_bond_yield_never_executes_orders_and_policy_blocks():
    r=BondYieldIntelligenceRuntime().evaluate_one(base(broker="EXNESS",symbol="XAUUSD",live_execution_enabled=True,bond_yield_observations=[{"real_yield":2.1,"previous_real_yield":2.0}]))
    assert r.status=="BLOCKED" and r.execution_allowed is False and r.live_execution_enabled is False

def test_dashboard_contains_bilingual_bond_yield_panel():
    report=DashboardUIRuntime().evaluate_one(base(mode="PAPER",bond_yield_observations=[{"us2y_yield":4.5,"us10y_yield":4.3,"real_yield":2.1,"previous_real_yield":2.0}]))
    panel=next(p for p in report.panels if p.panel_id=="bond_yield_intelligence")
    assert panel.title_en=="Bond Yield Intelligence" and panel.title_th=="ปัญญาอัตราผลตอบแทนพันธบัตร"
    assert any("Direct Execution" in row[0] and row[1]=="False" for row in panel.rows)
