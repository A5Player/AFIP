from datetime import datetime, timezone
from afip.etf_flow_intelligence import ETFFlowIntelligenceRuntime
from afip.dashboard_ui import DashboardUIRuntime
NOW=datetime(2026,7,10,6,0,tzinfo=timezone.utc)
def base(**extra):
    d={"broker":"XM","symbol":"GOLD#","current_time_utc":NOW,"live_execution_enabled":False,"etf_flow_observations":[]}; d.update(extra); return d

def test_gld_inflow_is_bullish_context():
    r=ETFFlowIntelligenceRuntime().evaluate_one(base(etf_flow_observations=[{"fund":"GLD","daily_flow_usd":25000000,"weekly_flow_usd":60000000,"holdings_change_tonnes":1.2}]))
    assert r.status=="READY" and r.aggregate_gold_effect=="BULLISH" and r.inflow_count==1

def test_iau_outflow_is_bearish_context():
    r=ETFFlowIntelligenceRuntime().evaluate_one(base(etf_flow_observations=[{"fund":"IAU","daily_flow_usd":-22000000,"weekly_flow_usd":-50000000,"holdings_change_tonnes":-0.8}]))
    assert r.aggregate_gold_effect=="BEARISH" and r.outflow_count==1

def test_balanced_flow_is_neutral():
    r=ETFFlowIntelligenceRuntime().evaluate_one(base(etf_flow_observations=[{"fund":"GLD","daily_flow_usd":100000,"weekly_flow_usd":-100000}]))
    assert r.aggregate_flow_trend=="BALANCED" and r.neutral_count==1

def test_etf_flow_never_executes_orders():
    r=ETFFlowIntelligenceRuntime().evaluate_one(base(etf_flow_observations=[{"fund":"GLD","daily_flow_usd":25000000}]))
    assert r.execution_allowed is False and r.live_execution_enabled is False

def test_policy_blocks_non_xm_non_gold_and_live():
    r=ETFFlowIntelligenceRuntime().evaluate_one(base(broker="EXNESS",symbol="XAUUSD",live_execution_enabled=True,etf_flow_observations=[{"fund":"GLD","daily_flow_usd":25000000}]))
    assert r.status=="BLOCKED" and "xm_only_required" in r.reason and "gold_symbol_only_required" in r.reason

def test_dashboard_contains_bilingual_etf_flow_panel():
    report=DashboardUIRuntime().evaluate_one(base(mode="PAPER",etf_flow_observations=[{"fund":"GLD","daily_flow_usd":25000000}]))
    panel=next(p for p in report.panels if p.panel_id=="etf_flow_intelligence")
    assert panel.title_en=="ETF Flow Intelligence" and panel.title_th=="ปัญญากระแสเงิน ETF"
    assert any("Direct Execution" in row[0] and row[1]=="False" for row in panel.rows)
