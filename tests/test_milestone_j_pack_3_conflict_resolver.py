from datetime import datetime, timezone
from afip.conflict_resolver import ConflictResolverRuntime
from afip.dashboard_ui import DashboardUIRuntime
NOW=datetime(2026,7,10,10,0,tzinfo=timezone.utc)
def base(**x):
 d={"broker":"XM","symbol":"GOLD#","current_time_utc":NOW,"live_execution_enabled":False}; d.update(x); return d
def aligned(direction="BUY"):
 return {"market_regime_status":"READY","market_regime_direction":direction,"market_regime_confidence":.9,"market_structure_status":"READY","market_structure_direction":direction,"market_structure_confidence":.85,"multi_timeframe_status":"READY","multi_timeframe_direction":direction,"multi_timeframe_confidence":.8,"liquidity_status":"READY","liquidity_direction":"WAIT","liquidity_confidence":.6}
def test_low_conflict_keeps_consensus():
 r=ConflictResolverRuntime().evaluate_one(base(**aligned("BUY"))); assert r.status=="READY" and r.resolved_consensus=="BUY"
def test_high_conflict_holds_when_priority_not_confirmed():
 d=aligned("BUY"); d.update(market_regime_direction="WAIT",market_structure_direction="SELL",market_structure_confidence=1.0,gold_macro_status="READY",gold_macro_direction="SELL",gold_macro_confidence=1.0)
 r=ConflictResolverRuntime().evaluate_one(base(**d)); assert r.resolved_consensus in {"WAIT","SELL"} and r.direct_execution is False
def test_insufficient_evidence_waits():
 r=ConflictResolverRuntime().evaluate_one(base(market_regime_status="READY",market_regime_direction="BUY",market_regime_confidence=.9)); assert r.status=="WAITING"
def test_bilingual_reasons_present():
 r=ConflictResolverRuntime().evaluate_one(base(**aligned("SELL"))); assert r.waiting_reason_en and r.waiting_reason_th
def test_next_review_is_deterministic():
 r=ConflictResolverRuntime().evaluate_one(base(**aligned("BUY"))); assert r.next_review_time_utc.startswith("2026-07-10T10:10:00")
def test_dashboard_has_conflict_resolver_panel():
 report=DashboardUIRuntime().evaluate_one(base(mode="PAPER",**aligned("BUY"))); p=next(x for x in report.panels if x.panel_id=="conflict_resolver"); assert p.title_th=="ตัวแก้ความขัดแย้ง" and any(row[0]=="Direct Execution" and row[1]=="False" for row in p.rows)
