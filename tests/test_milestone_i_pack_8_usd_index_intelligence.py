from datetime import datetime, timezone
from afip.usd_index_intelligence import USDIndexIntelligenceRuntime
from afip.dashboard_ui import DashboardUIRuntime
NOW=datetime(2026,7,10,7,0,tzinfo=timezone.utc)
def base(**extra):
    d={"broker":"XM","symbol":"GOLD#","current_time_utc":NOW,"live_execution_enabled":False,"usd_index_observations":[]}; d.update(extra); return d

def test_rising_dxy_is_bearish_gold_context():
    r=USDIndexIntelligenceRuntime().evaluate_one(base(usd_index_observations=[{"index_name":"DXY","current_value":105.5,"previous_value":105.0,"gold_change_pct":-0.4}]))
    assert r.status=="READY" and r.aggregate_gold_effect=="BEARISH" and r.rising_count==1

def test_falling_dxy_is_bullish_gold_context():
    r=USDIndexIntelligenceRuntime().evaluate_one(base(usd_index_observations=[{"index_name":"DXY","current_value":104.5,"previous_value":105.0,"gold_change_pct":0.5}]))
    assert r.aggregate_gold_effect=="BULLISH" and r.falling_count==1

def test_stable_dxy_is_neutral():
    r=USDIndexIntelligenceRuntime().evaluate_one(base(usd_index_observations=[{"index_name":"DXY","current_value":105.01,"previous_value":105.0}]))
    assert r.aggregate_usd_trend=="STABLE" and r.stable_count==1

def test_same_direction_detects_divergence():
    r=USDIndexIntelligenceRuntime().evaluate_one(base(usd_index_observations=[{"index_name":"DXY","change_pct":0.4,"gold_change_pct":0.5}]))
    assert r.divergence_count==1 and r.observations[0].divergence=="POSITIVE_DIVERGENCE"

def test_usd_index_never_executes_orders_and_policy_blocks():
    r=USDIndexIntelligenceRuntime().evaluate_one(base(broker="EXNESS",symbol="XAUUSD",live_execution_enabled=True,usd_index_observations=[{"change_pct":0.4}]))
    assert r.status=="BLOCKED" and r.execution_allowed is False and r.live_execution_enabled is False

def test_dashboard_contains_bilingual_usd_index_panel():
    report=DashboardUIRuntime().evaluate_one(base(mode="PAPER",usd_index_observations=[{"index_name":"DXY","current_value":105.5,"previous_value":105.0}]))
    panel=next(p for p in report.panels if p.panel_id=="usd_index_intelligence")
    assert panel.title_en=="USD Index Intelligence" and panel.title_th=="ปัญญาดัชนีดอลลาร์สหรัฐ"
    assert any("Direct Execution" in row[0] and row[1]=="False" for row in panel.rows)
