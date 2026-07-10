from datetime import datetime,timezone
from afip.consensus_engine import ConsensusEngineRuntime
from afip.dashboard_ui import DashboardUIRuntime
NOW=datetime(2026,7,10,10,0,tzinfo=timezone.utc)
def base(**x):
 d={"broker":"XM","symbol":"GOLD#","current_time_utc":NOW,"live_execution_enabled":False}; d.update(x); return d
def aligned(direction="BUY"):
 return {"market_regime_status":"READY","market_regime_direction":direction,"market_regime_confidence":.9,"market_structure_status":"READY","market_structure_direction":direction,"market_structure_confidence":.85,"multi_timeframe_status":"READY","multi_timeframe_direction":direction,"multi_timeframe_confidence":.8,"liquidity_status":"READY","liquidity_direction":"WAIT","liquidity_confidence":.6}
def test_weighted_buy_consensus_ready():
 r=ConsensusEngineRuntime().evaluate_one(base(**aligned("BUY"))); assert r.status=="READY" and r.consensus=="BUY" and r.direct_execution is False
def test_weighted_sell_consensus_ready():
 r=ConsensusEngineRuntime().evaluate_one(base(**aligned("SELL"))); assert r.consensus=="SELL"
def test_conflict_ratio_detects_opposition():
 d=aligned("BUY"); d.update(market_structure_direction="SELL",gold_macro_status="READY",gold_macro_direction="SELL",gold_macro_confidence=.9); r=ConsensusEngineRuntime().evaluate_one(base(**d)); assert r.conflict_ratio>0 and r.contradicting_sources
def test_custom_weights_change_dominance():
 d=aligned("BUY"); d.update(market_structure_direction="SELL",market_structure_weight=2.0,market_structure_confidence=1.0); r=ConsensusEngineRuntime().evaluate_one(base(**d)); assert r.sell_score>0
def test_insufficient_evidence_waits():
 r=ConsensusEngineRuntime().evaluate_one(base(market_regime_status="READY",market_regime_direction="BUY",market_regime_confidence=.9)); assert r.status=="WAITING"
def test_dashboard_has_bilingual_consensus_panel():
 report=DashboardUIRuntime().evaluate_one(base(mode="PAPER",**aligned("BUY"))); panel=next(p for p in report.panels if p.panel_id=="consensus_engine"); assert panel.title_en=="Consensus Engine" and panel.title_th=="กลไกฉันทามติ" and any(row[0]=="Direct Execution" and row[1]=="False" for row in panel.rows)
