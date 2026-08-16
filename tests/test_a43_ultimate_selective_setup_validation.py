import json
from pathlib import Path
from tools.afip_a43_ultimate_selective_setup_validation import build_report,write_outputs

def seed(root:Path,blind_positive=True):
 a42=root/"runtime/research/a42_selective_trading_rankings";a42.mkdir(parents=True)
 rule={"dimension":"POLICY_HOUR_UTC","key":"FIXED_TP|3","policy_id":"FIXED_TP","planned_rr":2,"minimum_sl_points_observed":500,"standard_composite_score":80}
 a42.joinpath("a42_selective_trading_rankings.json").write_text(json.dumps({"status":"READY_FOR_SELECTIVE_TRADING_RESEARCH_REVIEW","candidate_groups":100,"standard_ranking":[rule]}))
 a40=root/"runtime/research/a40_time_session_outcomes";a40.mkdir(parents=True);rows=[]
 for i in range(100):
  part="TRAIN" if i<60 else "VALIDATION" if i<80 else "BLIND_FORWARD";result=(1 if blind_positive or part!="BLIND_FORWARD" else -1)
  rows.append({"selection_policy_version":"A41_V2_DEDUP_CONF60_COOLDOWN24","candidate_group_id":f"C{i}","policy_id":"FIXED_TP","hour_utc":3,"timeframe":"H1","session_name":"ASIA","weekday_utc":"MONDAY","direction":"SELL","calendar_day_utc":f"2026-{i//28+1:02d}-{i%28+1:02d}","decision_timestamp_utc":f"2026-{i//28+1:02d}-{i%28+1:02d}T03:00:00Z","chronological_partition":part,"net_realized_r":result})
 a40.joinpath("a40_normalized_closed_outcomes.jsonl").write_text("".join(json.dumps(x)+"\n" for x in rows))

def test_a43_freezes_winner_before_blind_and_passes(tmp_path:Path):
 seed(tmp_path);r=build_report(tmp_path)
 assert r["status"]=="ULTIMATE_RESEARCH_CANDIDATE_BLIND_AUDIT_PASS" and r["frozen_winner_rule_id"]=="POLICY_HOUR_UTC:FIXED_TP|3"
 assert r["blind_used_to_select_or_reorder"] is False and r["execution_authority"]=="NONE"

def test_a43_blind_failure_is_no_trade_without_fallback(tmp_path:Path):
 seed(tmp_path,False);r=build_report(tmp_path)
 assert r["status"]=="NO_TRADE_RESEARCH_EVIDENCE_INSUFFICIENT" and r["final_research_recommendation"]=="NO_TRADE"
 assert r["fallback_after_blind_failure"] is False and r["frozen_winner"]["blind_audit_pass"] is False

def test_a43_outputs_and_has_no_execution_imports(tmp_path:Path):
 seed(tmp_path);r=build_report(tmp_path);assert all(x.exists() for x in write_outputs(r,tmp_path))
 text=(Path(__file__).parents[1]/"tools/afip_a43_ultimate_selective_setup_validation.py").read_text()
 assert "MetaTrader5" not in text and ".order_send(" not in text

def test_a43_does_not_open_any_blind_rule_when_no_preblind_winner(tmp_path:Path):
 seed(tmp_path);a42=tmp_path/"runtime/research/a42_selective_trading_rankings/a42_selective_trading_rankings.json"
 value=json.loads(a42.read_text());value["standard_ranking"][0]["minimum_sl_points_observed"]=300;a42.write_text(json.dumps(value))
 r=build_report(tmp_path)
 assert r["frozen_winner"] is None and r["blind_opened_rule_id"] is None
 assert r["rule_evaluations"][0]["partitions"]["BLIND_FORWARD"]["status"]=="SEALED_NOT_OPENED"

def test_a43_v1_exposure_forces_new_blind_cohort(tmp_path:Path):
 seed(tmp_path);out=tmp_path/"runtime/research/a43_ultimate_selective_setup_validation";out.mkdir(parents=True)
 out.joinpath("a43_ultimate_selective_setup_validation.json").write_text(json.dumps({"schema":"afip.a43.ultimate_selective_setup_validation.v1"}))
 r=build_report(tmp_path)
 assert r["status"]=="NO_TRADE_NEW_BLIND_COHORT_REQUIRED" and r["prior_blind_exposure_detected"] is True
 assert r["blind_opened_rule_id"] is None and r["frozen_winner"]["partitions"]["BLIND_FORWARD"]["status"]=="SEALED_NOT_OPENED"
