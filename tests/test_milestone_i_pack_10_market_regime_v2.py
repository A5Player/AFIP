from datetime import datetime, timezone
from afip.market_regime_v2 import MarketRegimeV2Runtime
from afip.dashboard_ui import DashboardUIRuntime
NOW=datetime(2026,7,10,8,0,tzinfo=timezone.utc)
def base(**extra):
    d={"broker":"XM","symbol":"GOLD#","current_time_utc":NOW,"live_execution_enabled":False}; d.update(extra); return d
def ready_components(effect="BULLISH"):
    d={}
    for n in ("economic_calendar","news","gold_macro","central_bank","cot","open_interest","etf_flow","usd_index","bond_yield"):
        d[f"{n}_status"]="READY"; d[f"{n}_effect"]=effect; d[f"{n}_score"]=0.7 if effect=="BULLISH" else -0.7 if effect=="BEARISH" else 0; d[f"{n}_confidence"]=0.8
    return d
def test_aligned_bullish_components_create_strong_directional_regime():
    r=MarketRegimeV2Runtime().evaluate_one(base(**ready_components("BULLISH")))
    assert r.status=="READY" and r.regime=="DIRECTIONAL_STRONG" and r.directional_bias=="BULLISH"
def test_aligned_bearish_components_create_bearish_regime():
    r=MarketRegimeV2Runtime().evaluate_one(base(**ready_components("BEARISH")))
    assert r.directional_bias=="BEARISH" and r.component_alignment=="ALIGNED"
def test_mixed_components_create_transition_regime():
    d=ready_components("BULLISH")
    for n in ("news","central_bank","usd_index","bond_yield"):
        d[f"{n}_effect"]="BEARISH"; d[f"{n}_score"]=-0.7
    r=MarketRegimeV2Runtime().evaluate_one(base(**d))
    assert r.regime=="TRANSITION" and r.risk_state=="HIGH"
def test_insufficient_components_wait_without_execution():
    r=MarketRegimeV2Runtime().evaluate_one(base(news_status="READY",news_effect="BULLISH",news_score=.5,news_confidence=.8))
    assert r.status=="WAITING" and r.execution_allowed is False and r.intelligence_ready is False
def test_policy_blocks_non_xm_non_gold_and_live_execution():
    r=MarketRegimeV2Runtime().evaluate_one(base(broker="EXNESS",symbol="XAUUSD",live_execution_enabled=True,**ready_components()))
    assert r.status=="BLOCKED" and r.execution_allowed is False and r.live_execution_enabled is False
def test_dashboard_contains_bilingual_market_regime_v2_panel():
    report=DashboardUIRuntime().evaluate_one(base(mode="PAPER"))
    panel=next(p for p in report.panels if p.panel_id=="market_regime_v2")
    assert panel.title_en=="Market Regime V2" and panel.title_th=="ภาวะตลาด V2"
    assert any("Direct Execution" in row[0] and row[1]=="False" for row in panel.rows)
