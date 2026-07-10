from datetime import datetime, timezone
from afip.cot_intelligence import COTIntelligenceRuntime
from afip.dashboard_ui import DashboardUIRuntime
NOW=datetime(2026,7,10,5,0,tzinfo=timezone.utc)
def base(**extra):
    d={"broker":"XM","symbol":"GOLD#","current_time_utc":NOW,"live_execution_enabled":False,"cot_observations":[]}; d.update(extra); return d

def test_noncommercial_accumulation_is_bullish_context():
    r=COTIntelligenceRuntime().evaluate_one(base(cot_observations=[{"noncommercial_long":200000,"noncommercial_short":80000,"previous_noncommercial_net":110000,"commercial_long":90000,"commercial_short":210000}]))
    assert r.status=="READY" and r.bullish_count==1 and r.aggregate_positioning_bias=="BULLISH"

def test_noncommercial_reduction_is_bearish_context():
    r=COTIntelligenceRuntime().evaluate_one(base(cot_observations=[{"noncommercial_long":150000,"noncommercial_short":90000,"previous_noncommercial_net":90000,"commercial_long":100000,"commercial_short":180000}]))
    assert r.bearish_count==1 and r.observations[0].gold_effect=="BEARISH"

def test_stable_positioning_is_neutral():
    r=COTIntelligenceRuntime().evaluate_one(base(cot_observations=[{"noncommercial_long":150000,"noncommercial_short":90000,"previous_noncommercial_net":59500,"commercial_long":100000,"commercial_short":180000}]))
    assert r.neutral_count==1 and r.observations[0].positioning_trend=="STABLE"

def test_cot_never_executes_orders():
    r=COTIntelligenceRuntime().evaluate_one(base(cot_observations=[{"noncommercial_long":200000,"noncommercial_short":80000}]))
    assert r.execution_allowed is False and r.live_execution_enabled is False

def test_policy_blocks_non_xm_non_gold_and_live():
    r=COTIntelligenceRuntime().evaluate_one(base(broker="EXNESS",symbol="XAUUSD",live_execution_enabled=True,cot_observations=[{"noncommercial_long":200000,"noncommercial_short":80000}]))
    assert r.status=="BLOCKED" and "xm_only_required" in r.reason and "gold_symbol_only_required" in r.reason

def test_dashboard_contains_bilingual_cot_panel():
    report=DashboardUIRuntime().evaluate_one(base(mode="PAPER",cot_observations=[{"noncommercial_long":200000,"noncommercial_short":80000,"previous_noncommercial_net":100000}]))
    panel=next(p for p in report.panels if p.panel_id=="cot_intelligence")
    assert panel.title_en=="COT Intelligence" and panel.title_th=="ปัญญารายงาน COT"
    assert any("Direct Execution" in row[0] and row[1]=="False" for row in panel.rows)
