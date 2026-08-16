"""A43 frozen-rule, zero-to-one daily ultimate setup blind audit."""
from __future__ import annotations
import argparse,json,math
from collections import defaultdict
from datetime import datetime,timezone
from html import escape
from pathlib import Path
from statistics import mean
from typing import Any,Iterable

OUTPUT="runtime/research/a43_ultimate_selective_setup_validation"
MIN_TRAIN=30;MIN_VALIDATION=15;MIN_BLIND=15;MAX_DRAWDOWN_R=10.0

def _load_json(path:Path)->dict[str,Any]:
    try:value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError):return {}
    return value if isinstance(value,dict) else {}

def _load_rows(path:Path)->list[dict[str,Any]]:
    if not path.exists():return []
    rows=[]
    for line in path.read_text(encoding="utf-8").splitlines():
        try:value=json.loads(line)
        except json.JSONDecodeError:continue
        if value.get("selection_policy_version")=="A41_V2_DEDUP_CONF60_COOLDOWN24":rows.append(value)
    return rows

def _metrics(rows:Iterable[dict[str,Any]])->dict[str,Any]:
    values=sorted(rows,key=lambda x:(x["decision_timestamp_utc"],x["candidate_group_id"]));pnl=[float(x["net_realized_r"]) for x in values]
    wins=sum(x>0 for x in pnl);losses=sum(x<0 for x in pnl);gw=sum(x for x in pnl if x>0);gl=-sum(x for x in pnl if x<0)
    equity=peak=dd=0.0
    for value in pnl:equity+=value;peak=max(peak,equity);dd=max(dd,peak-equity)
    return {"samples":len(pnl),"wins":wins,"losses":losses,"win_rate_pct":round(wins/len(pnl)*100,6) if pnl else None,
        "expectancy_r":round(mean(pnl),8) if pnl else None,"net_result_r":round(sum(pnl),8),
        "profit_factor":round(gw/gl,8) if gl else ("INFINITE" if gw else None),"max_drawdown_r":round(dd,8)}

def _pf(v:Any)->float:return 10.0 if v=="INFINITE" else float(v or 0)

def _matches(row:dict[str,Any],rule:dict[str,Any])->bool:
    policy,value=str(rule["key"]).split("|",1) if "|" in str(rule["key"]) else (str(rule["key"]),"")
    if str(row.get("policy_id"))!=policy:return False
    dimension=rule["dimension"]
    mapping={"POLICY":policy,"POLICY_TIMEFRAME":str(row.get("timeframe")),"POLICY_SESSION":str(row.get("session_name")),
        "POLICY_WEEKDAY":str(row.get("weekday_utc")),"POLICY_HOUR_UTC":str(row.get("hour_utc")),"POLICY_DIRECTION":str(row.get("direction"))}
    return dimension=="POLICY" or mapping.get(dimension)==value

def _first_per_day(rows:list[dict[str,Any]])->list[dict[str,Any]]:
    by_day:dict[str,list[dict[str,Any]]]=defaultdict(list)
    for row in rows:by_day[str(row["calendar_day_utc"])].append(row)
    return [sorted(by_day[day],key=lambda x:(x["decision_timestamp_utc"],x["candidate_group_id"]))[0] for day in sorted(by_day)]

def _win_threshold(rr:float)->float:
    if rr>=4:return 27
    if rr>=3:return 32
    if rr>=2:return 42
    if rr>=1.5:return 50
    return 60

def _evaluate_rule(rows:list[dict[str,Any]],source:dict[str,Any])->dict[str,Any]:
    selected=[x for x in rows if _matches(x,source)];parts={}
    for partition in ("TRAIN","VALIDATION"):
        candidate=[x for x in selected if x["chronological_partition"]==partition]
        chosen=_first_per_day(candidate);parts[partition]={**_metrics(chosen),"candidate_days":len({x["calendar_day_utc"] for x in candidate}),
            "trading_days":len(chosen),"selection":"FIRST_MATCH_CHRONOLOGICALLY_PER_UTC_DAY"}
    rr=float(source.get("planned_rr") or 0);pre=[]
    if parts["TRAIN"]["samples"]<MIN_TRAIN:pre.append("TRAIN_DAYS_BELOW_30")
    if parts["VALIDATION"]["samples"]<MIN_VALIDATION:pre.append("VALIDATION_DAYS_BELOW_15")
    if (parts["TRAIN"]["expectancy_r"] or 0)<=0:pre.append("TRAIN_EXPECTANCY_NOT_POSITIVE")
    if (parts["VALIDATION"]["expectancy_r"] or 0)<=0:pre.append("VALIDATION_EXPECTANCY_NOT_POSITIVE")
    if _pf(parts["VALIDATION"]["profit_factor"])<1:pre.append("VALIDATION_PROFIT_FACTOR_BELOW_1")
    if rr<1:pre.append("PLANNED_RR_BELOW_1_TO_1")
    if float(source.get("minimum_sl_points_observed") or 0)<500:pre.append("SL_BELOW_500_POINTS")
    parts["BLIND_FORWARD"]={"status":"SEALED_NOT_OPENED","samples":None,"win_rate_pct":None,"expectancy_r":None,
        "profit_factor":None,"max_drawdown_r":None}
    return {"rule_id":f'{source["dimension"]}:{source["key"]}',"dimension":source["dimension"],"key":source["key"],
        "policy_id":source["policy_id"],"planned_rr":rr,"minimum_sl_points_observed":source.get("minimum_sl_points_observed"),
        "a42_standard_composite_score":source.get("standard_composite_score"),"partitions":parts,"pre_blind_eligible":not pre,
        "pre_blind_reasons":pre,"blind_audit_pass":None,"blind_audit_reasons":["SEALED_NOT_OPENED"],"research_only":True,"execution_authority":"NONE"}

def _open_blind_for_winner(rows:list[dict[str,Any]],winner:dict[str,Any])->None:
    selected=[x for x in rows if _matches(x,winner) and x["chronological_partition"]=="BLIND_FORWARD"]
    chosen=_first_per_day(selected);metrics={**_metrics(chosen),"candidate_days":len({x["calendar_day_utc"] for x in selected}),
        "trading_days":len(chosen),"selection":"FIRST_MATCH_CHRONOLOGICALLY_PER_UTC_DAY","status":"OPENED_FOR_FROZEN_WINNER_ONLY"}
    winner["partitions"]["BLIND_FORWARD"]=metrics;blind=[];rr=float(winner.get("planned_rr") or 0)
    if metrics["samples"]<MIN_BLIND:blind.append("BLIND_DAYS_BELOW_15")
    if (metrics["expectancy_r"] or 0)<=0:blind.append("BLIND_EXPECTANCY_NOT_POSITIVE")
    if _pf(metrics["profit_factor"])<1:blind.append("BLIND_PROFIT_FACTOR_BELOW_1")
    if (metrics["win_rate_pct"] or 0)<_win_threshold(rr):blind.append("BLIND_WIN_RATE_BELOW_RR_SAFETY_THRESHOLD")
    if metrics["max_drawdown_r"]>MAX_DRAWDOWN_R:blind.append("BLIND_DRAWDOWN_ABOVE_10R")
    winner["blind_audit_pass"]=not blind;winner["blind_audit_reasons"]=blind

def build_report(project_root:str|Path)->dict[str,Any]:
    root=Path(project_root).resolve();a42=_load_json(root/"runtime/research/a42_selective_trading_rankings/a42_selective_trading_rankings.json")
    rows=_load_rows(root/"runtime/research/a40_time_session_outcomes/a40_normalized_closed_outcomes.jsonl")
    previous=_load_json(root/OUTPUT/"a43_ultimate_selective_setup_validation.json")
    prior_exposure=bool(previous.get("prior_blind_exposure_detected") or previous.get("schema")=="afip.a43.ultimate_selective_setup_validation.v1")
    # Freeze rule order from A42. Blind fields contained in A42 are never read
    # for selection, fallback, or ranking here.
    frozen=[{"dimension":x.get("dimension"),"key":x.get("key"),"policy_id":x.get("policy_id"),"planned_rr":x.get("planned_rr"),
             "minimum_sl_points_observed":x.get("minimum_sl_points_observed"),"standard_composite_score":x.get("standard_composite_score")}
            for x in a42.get("standard_ranking",())]
    evaluations=[_evaluate_rule(rows,x) for x in frozen]
    pre=[x for x in evaluations if x["pre_blind_eligible"]]
    pre.sort(key=lambda x:(x["partitions"]["VALIDATION"]["expectancy_r"] or -999,x["partitions"]["VALIDATION"]["win_rate_pct"] or -1,
                           -x["partitions"]["VALIDATION"]["max_drawdown_r"],x["a42_standard_composite_score"] or 0),reverse=True)
    winner=pre[0] if pre else None
    if winner is not None and not prior_exposure:_open_blind_for_winner(rows,winner)
    final_pass=bool(winner and winner["blind_audit_pass"] is True and not prior_exposure)
    status=("NO_TRADE_NEW_BLIND_COHORT_REQUIRED" if prior_exposure else
            "ULTIMATE_RESEARCH_CANDIDATE_BLIND_AUDIT_PASS" if final_pass else "NO_TRADE_RESEARCH_EVIDENCE_INSUFFICIENT")
    return {"schema":"afip.a43.ultimate_selective_setup_validation.v2","generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "status":status,"source_a42_status":a42.get("status","MISSING"),"source_candidate_groups":a42.get("candidate_groups",0),
        "frozen_rule_count":len(frozen),"pre_blind_eligible_rules":len(pre),"frozen_winner_rule_id":winner["rule_id"] if winner else None,
        "frozen_winner":winner,"rule_evaluations":evaluations,"selection_policy":"A42_STANDARD_ORDER_THEN_VALIDATION_CONFIRMATION",
        "prior_blind_exposure_detected":prior_exposure,"blind_opened_rule_id":winner["rule_id"] if winner and not prior_exposure else None,
        "blind_evidence_reusable_for_certification":not prior_exposure,"fallback_after_blind_failure":False,"blind_used_to_select_or_reorder":False,"daily_trade_budget":"ZERO_TO_ONE_FIRST_MATCH_CHRONOLOGICALLY",
        "final_research_recommendation":"REVIEW_ULTIMATE_CANDIDATE" if final_pass else "NO_TRADE",
        "no_trade_is_valid":True,"automatic_profile_assignment":False,"profile_strategy_selection":"NOT_DECIDED",
        "demo_order_authorized":False,"live_order_authorized":False,"execution_authority":"NONE","orders_sent":False}

def write_outputs(report:dict[str,Any],project_root:str|Path)->tuple[Path,Path]:
    out=Path(project_root).resolve()/OUTPUT;out.mkdir(parents=True,exist_ok=True);jp=out/"a43_ultimate_selective_setup_validation.json";hp=out/"a43_ultimate_selective_setup_validation.html"
    jp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    body=[]
    for rank,row in enumerate(report["rule_evaluations"],1):
        v=row["partitions"]["VALIDATION"];b=row["partitions"]["BLIND_FORWARD"]
        body.append('<tr>'+''.join(f'<td>{escape(str(x))}</td>' for x in (rank,row["rule_id"],row["pre_blind_eligible"],v["samples"],v["win_rate_pct"],v["expectancy_r"],b.get("samples"),b.get("win_rate_pct"),b.get("expectancy_r"),row["blind_audit_pass"],",".join(row["blind_audit_reasons"])))+'</tr>')
    hp.write_text(f'''<!doctype html><meta charset="utf-8"><title>A43 Ultimate Validation</title><style>body{{font:14px system-ui;background:#edf2f7;color:#14243a}}main{{max-width:1400px;margin:auto}}header,article{{background:white;padding:18px;margin:14px;border-radius:14px;overflow:auto}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #d5dee8;padding:7px;white-space:nowrap}}</style><main><header><h1>A43 Ultimate Selective Setup Validation</h1><h2>{escape(report['status'])}</h2><p>Frozen winner: {escape(str(report['frozen_winner_rule_id']))} · final: {escape(report['final_research_recommendation'])}</p><p>0–1 first chronological match/day · no blind fallback · P1–P4 NOT_DECIDED · authority NONE</p></header><article><table><tr><th>Rank</th><th>Rule</th><th>Pre-blind</th><th>Val N</th><th>Val Win%</th><th>Val Exp</th><th>Blind N</th><th>Blind Win%</th><th>Blind Exp</th><th>Blind Pass</th><th>Reasons</th></tr>{''.join(body)}</table></article></main>''',encoding="utf-8");return jp,hp

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--project-root",type=Path,default=Path.cwd());a=p.parse_args();r=build_report(a.project_root);paths=write_outputs(r,a.project_root)
    print(json.dumps({"status":r["status"],"frozen_rule_count":r["frozen_rule_count"],"pre_blind_eligible_rules":r["pre_blind_eligible_rules"],"frozen_winner_rule_id":r["frozen_winner_rule_id"],"final_research_recommendation":r["final_research_recommendation"],"outputs":[str(x) for x in paths],"execution_authority":"NONE"},indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
