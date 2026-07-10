from datetime import datetime, timezone
from afip.decision_intelligence_foundation import DecisionIntelligenceFoundationRuntime
from afip.dashboard_ui import DashboardUIRuntime
NOW=datetime(2026,7,10,9,0,tzinfo=timezone.utc)
def base(**extra):
    d={"broker":"XM","symbol":"GOLD#","current_time_utc":NOW,"live_execution_enabled":False,"risk_allowed":True,"trading_cost_allowed":True}; d.update(extra); return d
def aligned(direction="BUY"):
    return {"market_regime_status":"READY","market_regime_direction":direction,"market_regime_confidence":.9,"market_structure_status":"READY","market_structure_direction":direction,"market_structure_confidence":.85,"multi_timeframe_status":"READY","multi_timeframe_direction":direction,"multi_timeframe_confidence":.8,"liquidity_status":"READY","liquidity_direction":"WAIT","liquidity_confidence":.6,"risk_status":"READY","risk_direction":"WAIT","risk_confidence":1.0,"trading_cost_status":"READY","trading_cost_direction":"WAIT","trading_cost_confidence":1.0}
def test_aligned_buy_context_is_ready_without_execution():
    r=DecisionIntelligenceFoundationRuntime().evaluate_one(base(**aligned("BUY")))
    assert r.status=="READY" and r.consensus=="BUY" and r.decision_ready is True and r.execution_allowed is False
def test_aligned_sell_context_is_ready():
    r=DecisionIntelligenceFoundationRuntime().evaluate_one(base(**aligned("SELL")))
    assert r.consensus=="SELL" and r.conflict_state=="LOW"
def test_high_conflict_waits_for_review():
    d=aligned("BUY"); d.update(market_structure_direction="SELL",multi_timeframe_direction="SELL",liquidity_direction="BUY")
    r=DecisionIntelligenceFoundationRuntime().evaluate_one(base(**d))
    assert r.conflict_state=="HIGH" and r.decision_ready is False
def test_insufficient_evidence_waits():
    r=DecisionIntelligenceFoundationRuntime().evaluate_one(base(market_regime_status="READY",market_regime_direction="BUY",market_regime_confidence=.8))
    assert r.status=="WAITING" and r.opportunity_state=="INSUFFICIENT_EVIDENCE"
def test_policy_and_risk_blocks_context():
    r=DecisionIntelligenceFoundationRuntime().evaluate_one(base(broker="EXNESS",risk_allowed=False,**aligned()))
    assert r.status=="BLOCKED" and "xm_only_required" in r.reason and r.execution_allowed is False
def test_dashboard_contains_bilingual_decision_foundation_panel():
    report=DashboardUIRuntime().evaluate_one(base(mode="PAPER",market_structure_status="READY",market_structure_direction="BUY",market_structure_confidence=.8,multi_timeframe_status="READY",multi_timeframe_direction="BUY",multi_timeframe_confidence=.8,liquidity_status="READY",liquidity_direction="WAIT",liquidity_confidence=.6))
    panel=next(p for p in report.panels if p.panel_id=="decision_intelligence_foundation")
    assert panel.title_en=="Decision Intelligence Foundation" and panel.title_th=="รากฐานปัญญาการตัดสินใจ"
    assert any("Direct Execution" in row[0] and row[1]=="False" for row in panel.rows)
