import json
from pathlib import Path
from afip.historical_replay_research import AppendOnlyResearchDataset
from tools.afip_a40_time_session_outcome_foundation import build_report,write_outputs

def _add(root:Path,stamp="2026-01-05T10:00:00Z",result=.5):
 d=AppendOnlyResearchDataset(root/"runtime/research")
 d.append("a22_holding_exit_validation_observations",{"decision_timestamp_utc":stamp,"research_case_id":stamp,"policy_id":"ATR","timeframe":"H1","pattern_family":"COMPRESSION","market_regime":"RANGE","session_name":"LONDON","event_window":"NONE","calendar_context":"NORMAL","net_realized_r":result,"mfe_r":1,"mae_r":.2,"holding_seconds":3600,"decision_score_percent":90,"future_data_used":False,"outcome_evaluation_uses_subsequent_closed_bars":True})

def test_a40_normalizes_chronological_context(tmp_path):
 _add(tmp_path);r=build_report(tmp_path);x=r["normalized_outcomes"][0]
 assert r["status"]=="READY_FOR_SELECTIVE_RANKING_RESEARCH" and x["weekday_utc"]=="MONDAY" and x["hour_utc"]==10
 assert x["session_name"]=="LONDON" and x["session_source"]=="RECORDED_A22_CONTEXT"

def test_a40_waits_and_never_authorizes(tmp_path):
 r=build_report(tmp_path);assert r["status"]=="WAITING_FOR_SCORED_CLOSED_OUTCOMES"
 assert r["no_trade_is_valid"] is True and r["demo_order_authorized"] is False and r["live_order_authorized"] is False and r["execution_authority"]=="NONE"

def test_a40_rejects_unproven_closed_bar(tmp_path):
 d=AppendOnlyResearchDataset(tmp_path/"runtime/research");d.append("a22_holding_exit_validation_observations",{"decision_timestamp_utc":"2026-01-01T00:00:00Z","net_realized_r":1})
 r=build_report(tmp_path);assert r["usable_closed_outcomes"]==0 and r["rejection_reasons"]["CLOSED_BAR_PROVENANCE_NOT_CONFIRMED"]==1

def test_a40_outputs_and_dashboard(tmp_path):
 _add(tmp_path);r=build_report(tmp_path);paths=write_outputs(r,tmp_path)
 assert all(p.exists() for p in paths) and len(paths[1].read_text().splitlines())==1
 from afip.dashboard_ui.split_runtime import SplitDashboardRenderer
 h=SplitDashboardRenderer().render_research_html({},tmp_path);assert "A40 Chronological Time/Session" in h and "no-trade valid" in h

def test_a40_source_has_no_execution_calls():
 t=(Path(__file__).parents[1]/"tools/afip_a40_time_session_outcome_foundation.py").read_text()
 assert "MetaTrader5" not in t and ".order_send(" not in t and ".order_check(" not in t
