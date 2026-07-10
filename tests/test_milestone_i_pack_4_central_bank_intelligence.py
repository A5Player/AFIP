from datetime import datetime, timezone
from afip.central_bank_intelligence import CentralBankIntelligenceRuntime
from afip.dashboard_ui import DashboardUIRuntime
NOW=datetime(2026,7,10,4,0,tzinfo=timezone.utc)
def base(**extra):
    d={"broker":"XM","symbol":"GOLD#","current_time_utc":NOW,"live_execution_enabled":False,"central_bank_observations":[]}; d.update(extra); return d

def test_hawkish_fomc_is_bearish_gold_context():
    r=CentralBankIntelligenceRuntime().evaluate_one(base(central_bank_observations=[{"institution":"FOMC","statement":"Rates may remain higher for longer"}]))
    assert r.status=="READY" and r.hawkish_count==1 and r.observations[0].gold_effect=="BEARISH"

def test_dovish_ecb_is_bullish_gold_context():
    r=CentralBankIntelligenceRuntime().evaluate_one(base(central_bank_observations=[{"institution":"ECB","policy_bias":"DOVISH","speaker":"ECB President"}]))
    assert r.dovish_count==1 and r.aggregate_gold_effect=="BULLISH"

def test_boj_neutral_statement_is_classified():
    r=CentralBankIntelligenceRuntime().evaluate_one(base(central_bank_observations=[{"institution":"BOJ","statement":"Policy remains under review"}]))
    assert r.neutral_count==1 and r.observations[0].policy_bias=="NEUTRAL"

def test_central_bank_intelligence_never_executes_orders():
    r=CentralBankIntelligenceRuntime().evaluate_one(base(central_bank_observations=[{"institution":"PBOC","policy_bias":"DOVISH"}]))
    assert r.execution_allowed is False and r.live_execution_enabled is False

def test_policy_blocks_non_xm_non_gold_and_live():
    r=CentralBankIntelligenceRuntime().evaluate_one(base(broker="EXNESS",symbol="XAUUSD",live_execution_enabled=True,central_bank_observations=[{"institution":"BOE","policy_bias":"HAWKISH"}]))
    assert r.status=="BLOCKED" and "xm_only_required" in r.reason and "gold_symbol_only_required" in r.reason

def test_dashboard_contains_bilingual_central_bank_panel():
    report=DashboardUIRuntime().evaluate_one(base(mode="PAPER",central_bank_observations=[{"institution":"FOMC","policy_bias":"HAWKISH"}]))
    panel=next(p for p in report.panels if p.panel_id=="central_bank_intelligence")
    assert panel.title_en=="Central Bank Intelligence" and panel.title_th=="ปัญญาธนาคารกลาง"
    assert any("Direct Execution" in row[0] and row[1]=="False" for row in panel.rows)
