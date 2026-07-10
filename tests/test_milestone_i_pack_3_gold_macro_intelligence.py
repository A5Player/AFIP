from datetime import datetime, timezone
from afip.gold_macro_intelligence import GoldMacroIntelligenceRuntime
from afip.dashboard_ui import DashboardUIRuntime
NOW=datetime(2026,7,10,3,0,tzinfo=timezone.utc)
def base(**extra):
    d={"broker":"XM","symbol":"GOLD#","current_time_utc":NOW,"live_execution_enabled":False,"macro_indicators":[]}; d.update(extra); return d

def test_cpi_above_forecast_is_structured_bullish_context():
    r=GoldMacroIntelligenceRuntime().evaluate_one(base(macro_indicators=[{"indicator":"CPI YoY","actual":3.2,"forecast":3.0,"previous":2.9}]))
    assert r.status=="READY" and r.inflation_count==1 and r.indicators[0].gold_effect=="BULLISH"

def test_strong_nfp_is_bearish_gold_context():
    r=GoldMacroIntelligenceRuntime().evaluate_one(base(macro_indicators=[{"indicator":"NFP","actual":250,"forecast":180,"previous":165}]))
    assert r.employment_count==1 and r.indicators[0].gold_effect=="BEARISH"

def test_weak_pmi_is_bullish_gold_context():
    r=GoldMacroIntelligenceRuntime().evaluate_one(base(macro_indicators=[{"indicator":"Manufacturing PMI","actual":47,"forecast":50,"previous":49}]))
    assert r.activity_count==1 and r.indicators[0].gold_effect=="BULLISH"

def test_macro_never_allows_direct_execution():
    r=GoldMacroIntelligenceRuntime().evaluate_one(base(macro_indicators=[{"indicator":"GDP","actual":2,"forecast":2.2}]))
    assert r.execution_allowed is False and r.live_execution_enabled is False

def test_policy_blocks_non_xm_non_gold_and_live():
    r=GoldMacroIntelligenceRuntime().evaluate_one(base(broker="EXNESS",symbol="XAUUSD",live_execution_enabled=True,macro_indicators=[{"indicator":"CPI","actual":3,"forecast":2.8}]))
    assert r.status=="BLOCKED" and "xm_only_required" in r.reason and "gold_symbol_only_required" in r.reason

def test_dashboard_contains_bilingual_gold_macro_panel():
    report=DashboardUIRuntime().evaluate_one(base(mode="PAPER",macro_indicators=[{"indicator":"CPI","actual":3.2,"forecast":3.0}]))
    panel=next(p for p in report.panels if p.panel_id=="gold_macro_intelligence")
    assert panel.title_en=="Gold Macro Intelligence" and panel.title_th=="ปัญญามหภาคสำหรับทองคำ"
    assert any("Direct Execution" in row[0] and row[1]=="False" for row in panel.rows)
