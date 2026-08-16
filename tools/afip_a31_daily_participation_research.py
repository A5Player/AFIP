"""Generate A31 daily participation evidence from recorded A22 outcomes."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from afip.exit_evidence_research import A31DailyParticipationResearch,DailySetupOutcome
from afip.historical_replay_research import AppendOnlyResearchDataset

def _time(value):return datetime.fromisoformat(str(value).replace("Z","+00:00"))

def build(project_root:Path)->dict:
    dataset=AppendOnlyResearchDataset(project_root/"runtime/research")
    records=[dict(x["record"]) for x in dataset.records("a22_holding_exit_validation_observations")]
    usable=[x for x in records if x.get("decision_score_percent") is not None and x.get("decision_timestamp_utc")]
    if not usable:
        return {"schema":"afip.a31.daily_participation.v1","status":"WAITING_FOR_SCORED_CLOSED_OUTCOMES",
          "source_records":len(records),"usable_records":0,"reason":"A31 requires decision-time score plus later closed-position R outcome.",
          "profile_strategy_selection":"NOT_DECIDED","execution_authority":"NONE","orders_sent":False}
    snapshot_id=hashlib.sha256(json.dumps(usable,sort_keys=True,default=str,separators=(",",":")).encode()).hexdigest()
    previous=[dict(x["record"]) for x in dataset.records("a31_daily_participation_rankings")]
    if any(x.get("source_snapshot_id")==snapshot_id for x in previous):
        return {"schema":"afip.a31.daily_participation.v1","generated_at_utc":datetime.now(timezone.utc).isoformat(),
          "status":"ALREADY_CURRENT","source_snapshot_id":snapshot_id,"source_records":len(records),
          "usable_records":len(usable),"profile_strategy_selection":"NOT_DECIDED",
          "automatic_profile_assignment":False,"automatic_research_promotion":False,
          "execution_authority":"NONE","orders_sent":False}
    timestamps=sorted({_time(x["decision_timestamp_utc"]) for x in usable})
    train_at=timestamps[max(0,int(len(timestamps)*.6)-1)];validation_at=timestamps[max(0,int(len(timestamps)*.8)-1)]
    grouped={}
    for row in usable:grouped.setdefault(str(row.get("policy_id","UNCLASSIFIED")),[]).append(row)
    all_results=[];all_rankings=[];engine=A31DailyParticipationResearch()
    for source_policy,rows in sorted(grouped.items()):
        observations=[]
        for row in rows:
            stamp=_time(row["decision_timestamp_utc"]);phase="TRAIN" if stamp<=train_at else "VALIDATION" if stamp<=validation_at else "BLIND_FORWARD"
            observations.append(DailySetupOutcome(
              setup_id=f"{source_policy}|{row.get('research_case_id')}",decision_at_utc=row["decision_timestamp_utc"],partition=phase,
              decision_score_percent=float(row["decision_score_percent"]),result_r=float(row.get("net_realized_r",row.get("realized_r",0))),
              session_name=str(row.get("session_name","UNCLASSIFIED")),pattern_family=str(row.get("pattern_family","UNCLASSIFIED")),
              broker_order_count=int(row.get("broker_order_count",1)),unit_count=int(row.get("position_units",1))))
        results=engine.evaluate(observations)
        for item in results:
            payload={"source_snapshot_id":snapshot_id,"source_exit_policy_id":source_policy,**item.as_dict()};dataset.append("a31_daily_participation_results",payload);all_results.append(payload)
        for item in engine.rank_blind_forward(results):
            payload={"source_snapshot_id":snapshot_id,"source_exit_policy_id":source_policy,**item};dataset.append("a31_daily_participation_rankings",payload);all_rankings.append(payload)
    return {"schema":"afip.a31.daily_participation.v1","generated_at_utc":datetime.now(timezone.utc).isoformat(),"status":"COMPLETE",
      "source_snapshot_id":snapshot_id,"source_records":len(records),"usable_records":len(usable),"result_rows":len(all_results),"ranking_rows":len(all_rankings),
      "train_end_utc":train_at.isoformat(),"validation_end_utc":validation_at.isoformat(),"profile_strategy_selection":"NOT_DECIDED",
      "automatic_profile_assignment":False,"automatic_research_promotion":False,"execution_authority":"NONE","orders_sent":False,
      "units":{"win_rate_percent":"%","expectancy_r_per_setup":"R/setup","net_result_r":"R","profit_factor_ratio":"ratio (no unit)","maximum_drawdown_r":"R","selected_setups":"setups","broker_orders":"orders","units":"0.01-lot units as recorded"}}

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--project-root",required=True);args=p.parse_args();root=Path(args.project_root).resolve()
    report=build(root);out=root/"runtime/research/a31_daily_participation_report.json";out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2));print("A31 report:",out);return 0
if __name__=="__main__":raise SystemExit(main())
