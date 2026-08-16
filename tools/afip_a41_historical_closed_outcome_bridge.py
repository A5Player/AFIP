"""A41 v2 deduplicated bridge from canonical replay to existing A21 outcomes."""
from __future__ import annotations
import argparse,json,math
from collections import Counter,defaultdict
from datetime import datetime,timezone
from hashlib import sha256
from html import escape
from pathlib import Path
from typing import Any
from afip.exit_evidence_research import A21HoldingBucket,A21HoldingExitEvidenceProducer
from afip.exit_outcome_research import A16PolicySet,A16ResearchContext,PositionResearchCase
from afip.historical_replay_research import AppendOnlyResearchDataset
from afip.research_replay import ReplayCandle

OUTPUT="runtime/research/a41_historical_closed_outcome_bridge"
POLICY="A41_V2_DEDUP_CONF60_COOLDOWN24"
TF_SECONDS={"M1":60,"M5":300,"M15":900,"M30":1800,"H1":3600,"H4":14400,"D1":86400}

def _time(v:Any)->datetime|None:
    try:r=datetime.fromisoformat(str(v).replace("Z","+00:00"))
    except (TypeError,ValueError):return None
    return r.astimezone(timezone.utc) if r.tzinfo else None

def _session(stamp:str)->str:
    hour=_time(stamp).hour # type: ignore[union-attr]
    if 7<=hour<12:return "LONDON"
    if 12<=hour<17:return "LONDON_NEW_YORK_OVERLAP"
    if 17<=hour<22:return "NEW_YORK"
    return "ASIA_OR_OFF_HOURS"

def _records(ds:AppendOnlyResearchDataset,name:str)->list[dict[str,Any]]:
    return [dict(x.get("record",{})) for x in ds.records(name)]

def _tf(row:dict[str,Any])->str:
    parts=str(row.get("scenario_id","")).split("-")
    return parts[1].upper() if len(parts)>2 and parts[0].upper()=="GOLD" else "UNKNOWN"

def _key(row:dict[str,Any])->str:
    return "|".join((_tf(row),str(row.get("replay_timestamp_utc","")),str(row.get("direction","")).upper(),
        str(row.get("setup_id","UNSPECIFIED")),str(row.get("pattern_family","UNCLASSIFIED"))))

def _identity(key:str)->str:return "A41-V2-"+sha256(key.encode()).hexdigest()[:24].upper()

def build_report(project_root:str|Path,*,maximum_cases:int=500,point_size:float=.01,
                 minimum_sl_points:float=500,buffer_points:float=200,conservative_cost_points:float=80)->dict[str,Any]:
    if maximum_cases<=0 or min(point_size,minimum_sl_points)<=0 or min(buffer_points,conservative_cost_points)<0:
        raise ValueError("A41 research parameters are invalid")
    root=Path(project_root).resolve();src=AppendOnlyResearchDataset(root/"runtime/research/automatic/schema_v2")
    target=AppendOnlyResearchDataset(root/"runtime/research")
    snapshots=_records(src,"snapshots");candidates=_records(src,"candidates")
    by_replay:dict[str,list[dict[str,Any]]]=defaultdict(list)
    for row in snapshots:by_replay[str(row.get("replay_id",""))].append(row)
    for rows in by_replay.values():rows.sort(key=lambda x:int(x.get("replay_clock",{}).get("replay_index",-1)))
    representatives:dict[str,dict[str,Any]]={};raw=0
    for row in candidates:
        if str(row.get("direction","")).upper() not in {"BUY","SELL"}:continue
        raw+=1;key=_key(row);current=representatives.get(key)
        coverage=len(by_replay.get(str(row.get("replay_id","")),()))-int(row.get("replay_index",-1))-1
        old=(-1 if current is None else len(by_replay.get(str(current.get("replay_id","")),()))-int(current.get("replay_index",-1))-1)
        if current is None or coverage>old or (coverage==old and str(row.get("candidate_id",""))<str(current.get("candidate_id",""))):representatives[key]=row
    rejected=Counter();eligible=[];last:dict[str,datetime]={}
    for key,row in sorted(representatives.items(),key=lambda x:(str(x[1].get("replay_timestamp_utc","")),_tf(x[1]),x[0])):
        stamp=_time(row.get("replay_timestamp_utc"));tf=_tf(row)
        try:confidence=float(row.get("confidence",0))
        except (TypeError,ValueError):rejected["INVALID_CONFIDENCE"]+=1;continue
        if stamp is None or tf not in TF_SECONDS:rejected["INVALID_TIMESTAMP_OR_TIMEFRAME"]+=1;continue
        if confidence<60:rejected["BELOW_PREDECLARED_CONFIDENCE_60"]+=1;continue
        replay_rows=by_replay.get(str(row.get("replay_id","")),())
        if int(row.get("replay_index",-1))+1>=len(replay_rows):
            rejected["NO_SUBSEQUENT_CLOSED_BAR_BEFORE_ELIGIBILITY"]+=1;continue
        if tf in last and (stamp-last[tf]).total_seconds()<TF_SECONDS[tf]*24:
            rejected["PREDECLARED_24_BAR_TIME_COOLDOWN"]+=1;continue
        last[tf]=stamp;eligible.append((key,row))
    existing={str(x.get("research_case_id","")) for x in _records(target,"a20_holding_exit_observations")}
    pending=[x for x in eligible if _identity(x[0]) not in existing];already=len(eligible)-len(pending)
    producer=A21HoldingExitEvidenceProducer(target,buckets=(A21HoldingBucket("INTRADAY_1_6",6),A21HoldingBucket("SESSION_7_24",24),A21HoldingBucket("MULTIDAY_25_120",120),A21HoldingBucket("OPEN_ENDED",None)))
    produced=outcomes=0
    for key,c in pending[:maximum_cases]:
        case_id=_identity(key);rows=by_replay.get(str(c.get("replay_id","")),[]);index=int(c.get("replay_index",-1))
        if index<0 or index+1>=len(rows):rejected["NO_SUBSEQUENT_CLOSED_BAR"]+=1;continue
        try:
            bars=tuple(ReplayCandle(str(x["replay_clock"]["replay_timestamp_utc"]),float(x["market_snapshot"]["latest_open"]),float(x["market_snapshot"]["latest_high"]),float(x["market_snapshot"]["latest_low"]),float(x["market_snapshot"]["latest_close"]),float(x["market_snapshot"].get("latest_volume",0) or 0)) for x in rows)
            entry=bars[index].close;avg=float(rows[index]["market_snapshot"].get("average_visible_range",0) or 0)
        except (KeyError,TypeError,ValueError,OverflowError):rejected["INVALID_REPLAY_SNAPSHOT"]+=1;continue
        if not all(math.isfinite(x) for x in (entry,avg)) or entry<=0:rejected["INVALID_ENTRY_OR_RANGE"]+=1;continue
        risk=max(minimum_sl_points*point_size,avg+buffer_points*point_size);stamp=str(c.get("replay_timestamp_utc",""));tf=_tf(c)
        context=A16ResearchContext(str(c.get("setup_id","UNSPECIFIED")),str(c.get("pattern_family","UNCLASSIFIED")),case_id,stamp,
            str(rows[index]["market_snapshot"].get("visible_direction","UNCLASSIFIED")),_session(stamp),"UTC_HOUR_RECORDED","NOT_CONNECTED","NOT_CONNECTED",
            f"CONSERVATIVE_RESEARCH_ASSUMPTION_{conservative_cost_points:g}_POINTS",decision_score_percent=float(c.get("confidence",0) or 0))
        case=PositionResearchCase(case_id,str(c["replay_id"]),str(c["research_run_id"]),str(c["dataset_version"]),str(c["scenario_id"]),str(c["direction"]).upper(),index,entry)
        provenance={"selection_policy_version":POLICY,"stable_candidate_key_sha256":sha256(key.encode()).hexdigest(),"candidate_group_id":case_id,
            "policy_variant_is_independent_trade":False,"replay_generation_deduplicated":True,"confidence_threshold":60.0,"cooldown_seconds":TF_SECONDS[tf]*24}
        try:r=producer.produce(case=case,policy_set=A16PolicySet(risk),candles=bars,context=context,timeframe=tf,
            execution_cost_r=conservative_cost_points*point_size/risk,provenance=provenance,rank_after_produce=False)
        except ValueError as exc:rejected["PRODUCER_REJECTED_"+str(exc).upper().replace(" ","_")[:70]]+=1;continue
        produced+=1;outcomes+=len(r.observations)
    attempted=min(len(pending),maximum_cases);remaining=max(0,len(pending)-attempted)
    status="PRODUCED_CLOSED_OUTCOMES" if produced else ("COMPLETE_NO_NEW_ELIGIBLE_CASES" if not pending else "WAITING_FOR_PRODUCIBLE_CASES")
    return {"schema":"afip.a41.historical_closed_outcome_bridge.v2","selection_policy_version":POLICY,"generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "status":status,"raw_directional_candidates":raw,"unique_candidates":len(representatives),"duplicate_replay_generation_candidates":raw-len(representatives),
        "eligible_unique_candidates":len(eligible),"already_produced_v2_cases":already,"pending_before_run":len(pending),"produced_cases":produced,
        "produced_closed_outcomes":outcomes,"remaining_selected_cases":remaining,"rejection_reasons":dict(rejected),
        "selection_rules":{"confidence_at_least":60,"cooldown":"24 timeframe bars converted to elapsed UTC seconds independently per timeframe","outcome_peeking":False,
            "daily_caps":"NOT_APPLIED_HERE; evaluated downstream as 0-1/0-3/0-5/0-10/unlimited"},
        "research_parameters":{"point_size":point_size,"minimum_sl_points":minimum_sl_points,"buffer_points":buffer_points,"conservative_cost_points":conservative_cost_points},
        "superseded_a41_v1_outcomes":"QUARANTINED_BY_A40_PROVENANCE_GATE","policy_variants_are_independent_trades":False,"research_only":True,
        "demo_order_authorized":False,"live_order_authorized":False,"execution_authority":"NONE","orders_sent":False}

def write_outputs(report:dict[str,Any],project_root:str|Path)->tuple[Path,Path]:
    out=Path(project_root).resolve()/OUTPUT;out.mkdir(parents=True,exist_ok=True);jp=out/"a41_historical_closed_outcome_bridge.json";hp=out/"a41_historical_closed_outcome_bridge.html"
    jp.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    reasons="".join(f"<tr><td>{escape(k)}</td><td>{v}</td></tr>" for k,v in report["rejection_reasons"].items())
    hp.write_text(f'''<!doctype html><meta charset="utf-8"><title>A41 v2</title><style>body{{font:15px system-ui;background:#eef3f8;color:#14243a}}main{{max-width:1100px;margin:auto}}article{{background:white;padding:20px;margin:18px;border-radius:14px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ccd7e2;padding:8px}}</style><main><article><h1>A41 v2 Deduplicated Closed-Outcome Bridge</h1><h2>{escape(report['status'])}</h2><p>Raw {report['raw_directional_candidates']} · unique {report['unique_candidates']} · eligible {report['eligible_unique_candidates']} · produced {report['produced_cases']} · remaining {report['remaining_selected_cases']}</p><p>Generation dedupe · confidence ≥60 · 24-bar time cooldown · no outcome peeking</p><p>A41 v1 quarantined · policy variants are not independent trades · authority NONE</p></article><article><h2>Exclusions</h2><table><tr><th>Reason</th><th>Count</th></tr>{reasons}</table></article></main>''',encoding="utf-8");return jp,hp

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--project-root",type=Path,default=Path.cwd());p.add_argument("--maximum-cases",type=int,default=500);a=p.parse_args()
    report=build_report(a.project_root,maximum_cases=a.maximum_cases);paths=write_outputs(report,a.project_root)
    print(json.dumps({"status":report["status"],"unique_candidates":report["unique_candidates"],"eligible_unique_candidates":report["eligible_unique_candidates"],"produced_cases":report["produced_cases"],"produced_closed_outcomes":report["produced_closed_outcomes"],"remaining_selected_cases":report["remaining_selected_cases"],"outputs":[str(x) for x in paths],"execution_authority":"NONE"},indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
