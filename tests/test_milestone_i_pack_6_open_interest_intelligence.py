from datetime import datetime, timezone
from afip.open_interest_intelligence import OpenInterestIntelligenceRuntime
from afip.dashboard_ui import DashboardUIRuntime
NOW=datetime(2026,7,10,6,0,tzinfo=timezone.utc)
def base(**extra):
    d={"broker":"XM","symbol":"GOLD#","current_time_utc":NOW,"live_execution_enabled":False,"open_interest_observations":[]}; d.update(extra); return d

def test_price_up_and_rising_oi_is_bullish_expansion():
    r=OpenInterestIntelligenceRuntime().evaluate_one(base(open_interest_observations=[{"open_interest":110000,"previous_open_interest":100000,"price_change_pct":1.2}]))
    assert r.status=="READY" and r.aggregate_gold_effect=="BULLISH" and r.rising_count==1

def test_price_down_and_rising_oi_is_bearish_expansion():
    r=OpenInterestIntelligenceRuntime().evaluate_one(base(open_interest_observations=[{"open_interest":110000,"previous_open_interest":100000,"price_change_pct":-1.1}]))
    assert r.aggregate_gold_effect=="BEARISH" and r.observations[0].market_interpretation=="SHORT_PARTICIPATION_EXPANDING"

def test_falling_oi_is_contraction_context():
    r=OpenInterestIntelligenceRuntime().evaluate_one(base(open_interest_observations=[{"open_interest":90000,"previous_open_interest":100000,"price_change_pct":0.8}]))
    assert r.aggregate_participation=="CONTRACTING" and r.falling_count==1

def test_open_interest_never_executes_orders():
    r=OpenInterestIntelligenceRuntime().evaluate_one(base(open_interest_observations=[{"open_interest":110000,"previous_open_interest":100000,"price_change_pct":1.0}]))
    assert r.execution_allowed is False and r.live_execution_enabled is False

def test_policy_blocks_non_xm_non_gold_and_live():
    r=OpenInterestIntelligenceRuntime().evaluate_one(base(broker="EXNESS",symbol="XAUUSD",live_execution_enabled=True,open_interest_observations=[{"open_interest":110000,"previous_open_interest":100000}]))
    assert r.status=="BLOCKED" and "xm_only_required" in r.reason and "gold_symbol_only_required" in r.reason

def test_dashboard_contains_bilingual_open_interest_panel():
    report=DashboardUIRuntime().evaluate_one(base(mode="PAPER",open_interest_observations=[{"open_interest":110000,"previous_open_interest":100000,"price_change_pct":1.0}]))
    panel=next(p for p in report.panels if p.panel_id=="open_interest_intelligence")
    assert panel.title_en=="Open Interest Intelligence" and panel.title_th=="ปัญญา Open Interest"
    assert any("Direct Execution" in row[0] and row[1]=="False" for row in panel.rows)
