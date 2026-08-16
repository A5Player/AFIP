import json
from pathlib import Path
from tools.afip_a42_selective_trading_rankings import build_report,write_outputs

POLICIES=("FIXED_TP","BREAK_EVEN_FIXED_TP","R_STEP","MFE_PERCENT","ATR","STRUCTURE","HYBRID_R_STRUCTURE")
def seed(root:Path,cases=120):
 out=root/"runtime/research/a40_time_session_outcomes";out.mkdir(parents=True)
 rows=[]
 for i in range(cases):
  partition="TRAIN" if i<72 else "VALIDATION" if i<96 else "BLIND_FORWARD"
  for policy in POLICIES:
   rows.append({"outcome_id":f"{i}-{policy}","candidate_group_id":f"C{i}","policy_variant_is_independent_trade":False,"selection_policy_version":"A41_V2_DEDUP_CONF60_COOLDOWN24","decision_timestamp_utc":f"2026-01-{i%28+1:02d}T{i%24:02d}:00:00Z","calendar_day_utc":f"2026-01-{i%28+1:02d}","weekday_utc":"MONDAY","hour_utc":i%24,"session_name":"LONDON","timeframe":"H1","direction":"BUY","policy_id":policy,"chronological_partition":partition,"net_realized_r":1 if i%3 else -1,"initial_risk_distance":5})
 out.joinpath("a40_normalized_closed_outcomes.jsonl").write_text("".join(json.dumps(x)+"\n" for x in rows),encoding="utf-8")
 a41=root/"runtime/research/a41_historical_closed_outcome_bridge";a41.mkdir(parents=True);a41.joinpath("a41_historical_closed_outcome_bridge.json").write_text(json.dumps({"research_parameters":{"point_size":.01}}))

def test_a42_groups_policy_variants_and_builds_all_rankings(tmp_path:Path):
 seed(tmp_path);r=build_report(tmp_path)
 assert r["status"]=="READY_FOR_SELECTIVE_TRADING_RESEARCH_REVIEW" and r["candidate_groups"]==120 and r["source_policy_outcomes"]==840
 assert r["standard_ranking"] and r["balanced_win_rate_ranking"] and r["session_time_ranking"] and r["ultimate_zero_to_one_ranking"]
 assert all(x["execution_authority"]=="NONE" for x in r["standard_ranking"])

def test_a42_daily_caps_are_chronological_and_include_unlimited(tmp_path:Path):
 seed(tmp_path);r=build_report(tmp_path);names={x["daily_policy"] for x in r["daily_participation_results"]}
 assert names=={"ZERO_TO_1","ZERO_TO_3","ZERO_TO_5","ZERO_TO_10","UNLIMITED"}
 assert all(x["selection_order"]=="FIRST_N_CHRONOLOGICALLY_NO_FUTURE_IN_DAY_RANKING" for x in r["daily_participation_results"])

def test_a42_blocks_incomplete_candidate_policy_groups(tmp_path:Path):
 seed(tmp_path,1);p=tmp_path/"runtime/research/a40_time_session_outcomes/a40_normalized_closed_outcomes.jsonl"
 lines=p.read_text().splitlines();p.write_text("\n".join(lines[:-1])+"\n")
 r=build_report(tmp_path);assert r["status"]=="BLOCKED_SOURCE_INTEGRITY" and r["integrity_blockers"]

def test_a42_outputs_and_has_no_execution_imports(tmp_path:Path):
 seed(tmp_path);r=build_report(tmp_path);assert all(x.exists() for x in write_outputs(r,tmp_path))
 text=(Path(__file__).parents[1]/"tools/afip_a42_selective_trading_rankings.py").read_text()
 assert "MetaTrader5" not in text and ".order_send(" not in text
