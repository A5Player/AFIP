"""A46 outcome-blind monitoring for the A45 prospective cohort data flow."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

OUTPUT = "runtime/research/a46_prospective_cohort_monitor"
SOURCE_POLICY_VERSION = "A41_V2_DEDUP_CONF60_COOLDOWN24"
INACTIVITY_WARNING_HOURS = 72


def _load_json(path: Path) -> dict[str, Any]:
    try: value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError): return {}
    return value if isinstance(value,dict) else {}


def _utc(value: Any) -> datetime | None:
    try: parsed=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    except (TypeError,ValueError): return None
    if parsed.tzinfo is None: parsed=parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _source_rows(path: Path) -> tuple[list[dict[str,Any]],int]:
    if not path.exists(): return [],0
    rows=[];rejected=0
    for line in path.read_text(encoding="utf-8").splitlines():
        try: row=json.loads(line)
        except json.JSONDecodeError: rejected+=1;continue
        if not isinstance(row,dict) or row.get("selection_policy_version")!=SOURCE_POLICY_VERSION: rejected+=1;continue
        # A46 intentionally never reads net_realized_r or any outcome field.
        rows.append({key:row.get(key) for key in ("selection_policy_version","candidate_group_id","policy_id","timeframe",
                    "session_name","weekday_utc","hour_utc","direction","calendar_day_utc","decision_timestamp_utc")})
    return rows,rejected


def _matches(row:dict[str,Any],rule:dict[str,Any])->bool:
    key=str(rule.get("key",""));policy,value=key.split("|",1) if "|" in key else (key,"")
    if str(row.get("policy_id"))!=policy:return False
    mapping={"POLICY_TIMEFRAME":str(row.get("timeframe")),"POLICY_SESSION":str(row.get("session_name")),
             "POLICY_WEEKDAY":str(row.get("weekday_utc")),"POLICY_HOUR_UTC":str(row.get("hour_utc")),
             "POLICY_DIRECTION":str(row.get("direction"))}
    return rule.get("dimension")=="POLICY" or mapping.get(str(rule.get("dimension")))==value


def _first_days(rows:list[dict[str,Any]])->list[dict[str,Any]]:
    grouped:dict[str,list[dict[str,Any]]]=defaultdict(list)
    for row in rows:
        if row.get("calendar_day_utc"):grouped[str(row["calendar_day_utc"])].append(row)
    return [sorted(grouped[day],key=lambda x:(str(x.get("decision_timestamp_utc")),str(x.get("candidate_group_id"))))[0]
            for day in sorted(grouped)]


def build_report(project_root:str|Path,now_utc:datetime|None=None)->dict[str,Any]:
    root=Path(project_root).resolve();now=(now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    a45=_load_json(root/"runtime/research/a45_future_preblind_qualification/a45_future_preblind_qualification.json")
    previous=_load_json(root/OUTPUT/"a46_prospective_cohort_monitor.json")
    cutoff=_utc(a45.get("cutoff_timestamp_utc"));end=_utc(a45.get("qualification_end_timestamp_utc"));rules=a45.get("frozen_rules")
    signature=str(a45.get("source_contract_signature_sha256") or "")
    errors=[]
    if not a45:errors.append("A45_REPORT_MISSING")
    if cutoff is None:errors.append("A45_CUTOFF_MISSING_OR_INVALID")
    if end is None:errors.append("A45_END_MISSING_OR_INVALID")
    if cutoff and end and end<=cutoff:errors.append("A45_WINDOW_NOT_FORWARD")
    if not isinstance(rules,list) or not rules:errors.append("A45_FROZEN_RULES_MISSING")
    if len(signature)!=64 or any(char not in "0123456789abcdef" for char in signature.lower()):errors.append("A45_SIGNATURE_INVALID")
    if previous.get("observed_a45_signature_sha256") not in (None,"",signature):errors.append("A45_SIGNATURE_CHANGED_AFTER_MONITORING_STARTED")
    if previous.get("observed_cutoff_timestamp_utc") not in (None,"",a45.get("cutoff_timestamp_utc")):errors.append("A45_CUTOFF_CHANGED_AFTER_MONITORING_STARTED")
    source_path=root/"runtime/research/a40_time_session_outcomes/a40_normalized_closed_outcomes.jsonl"
    rows,rejected=_source_rows(source_path)
    future=[]
    if cutoff and end:
        future=[row for row in rows if (stamp:=_utc(row.get("decision_timestamp_utc"))) is not None and cutoff<stamp<=end]
    latest=max((_utc(row.get("decision_timestamp_utc")) for row in future),default=None)
    coverage=[]
    for rule in rules if isinstance(rules,list) else []:
        selected=_first_days([row for row in future if _matches(row,rule)])
        coverage.append({"rule_id":f'{rule.get("dimension")}:{rule.get("key")}',"independent_days":len(selected),
                         "minimum_required_days":int(a45.get("minimum_rule_days") or 15),
                         "remaining_days":max(0,int(a45.get("minimum_rule_days") or 15)-len(selected)),
                         "latest_matching_timestamp_utc":selected[-1].get("decision_timestamp_utc") if selected else None,
                         "outcome_metrics_accessed":False})
    elapsed_hours=max(0.0,(now-cutoff).total_seconds()/3600) if cutoff else 0.0
    lag_hours=max(0.0,(now-latest).total_seconds()/3600) if latest else None
    window_complete=bool(end and now>=end)
    if errors:status="BLOCKED_A45_MONITORING_CONTRACT_INVALID"
    elif window_complete and a45.get("metrics_sealed") is True:status="WINDOW_COMPLETE_RUN_A45_TO_FINALIZE"
    elif not future and elapsed_hours>=INACTIVITY_WARNING_HOURS:status="WARNING_NO_FUTURE_SOURCE_OUTCOME_72H"
    elif not future:status="WAITING_FOR_FIRST_FUTURE_SOURCE_OUTCOME"
    elif lag_hours is not None and lag_hours>=INACTIVITY_WARNING_HOURS:status="WARNING_FUTURE_SOURCE_INACTIVE_72H"
    else:status="COLLECTING_PROSPECTIVE_COHORT"
    return {"schema":"afip.a46.prospective_cohort_monitor.v1","generated_at_utc":now.isoformat(),"status":status,
            "a45_status":a45.get("status","MISSING"),"observed_a45_signature_sha256":signature or None,
            "observed_cutoff_timestamp_utc":a45.get("cutoff_timestamp_utc"),"qualification_end_timestamp_utc":a45.get("qualification_end_timestamp_utc"),
            "window_complete":window_complete,"contract_errors":errors,"source_path":str(source_path),"source_exists":source_path.exists(),
            "source_policy_version":SOURCE_POLICY_VERSION,"source_rows_accepted_contract":len(rows),"source_rows_rejected_contract":rejected,
            "future_source_rows_in_window":len(future),"latest_future_source_timestamp_utc":latest.isoformat() if latest else None,
            "source_inactivity_hours":round(lag_hours,2) if lag_hours is not None else None,"inactivity_warning_hours":INACTIVITY_WARNING_HOURS,
            "rule_coverage":coverage,"outcome_metrics_accessed":False,"outcome_metrics_exposed":False,
            "win_rate_pct":None,"expectancy_r":None,"profit_factor":None,"max_drawdown_r":None,
            "final_research_recommendation":"NO_TRADE","demo_order_authorized":False,"live_order_authorized":False,
            "execution_authority":"NONE","orders_sent":False}


def write_outputs(report:dict[str,Any],project_root:str|Path)->tuple[Path,Path]:
    out=Path(project_root).resolve()/OUTPUT;out.mkdir(parents=True,exist_ok=True);jp=out/"a46_prospective_cohort_monitor.json";hp=out/"a46_prospective_cohort_monitor.html"
    jp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    rows="".join('<tr>'+''.join(f'<td>{escape(str(value))}</td>' for value in (item.get("rule_id"),item.get("independent_days"),item.get("minimum_required_days"),item.get("remaining_days"),item.get("latest_matching_timestamp_utc")))+'</tr>' for item in report.get("rule_coverage",()))
    hp.write_text(f'''<!doctype html><meta charset="utf-8"><title>A46 Prospective Cohort Monitor</title><style>body{{font:14px system-ui;background:#edf2f7;color:#14243a}}main{{max-width:1200px;margin:auto;background:white;padding:20px;border-radius:14px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #d5dee8;padding:8px}}</style><main><h1>A46 Prospective Cohort Monitoring &amp; Data-Flow Audit</h1><h2>{escape(str(report['status']))}</h2><p>Future source rows {report['future_source_rows_in_window']} · latest {escape(str(report['latest_future_source_timestamp_utc']))} · inactivity hours {escape(str(report['source_inactivity_hours']))}</p><table><tr><th>Frozen rule</th><th>Days</th><th>Required</th><th>Remaining</th><th>Latest match</th></tr>{rows}</table><p>Outcome metrics accessed: False · exposed: False · NO_TRADE · authority NONE</p></main>''',encoding="utf-8");return jp,hp


def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument("--project-root",type=Path,default=Path.cwd());args=parser.parse_args();report=build_report(args.project_root);paths=write_outputs(report,args.project_root)
    print(json.dumps({"status":report["status"],"future_source_rows_in_window":report["future_source_rows_in_window"],"rule_coverage":report["rule_coverage"],"outcome_metrics_accessed":False,"outputs":[str(x) for x in paths],"execution_authority":"NONE"},indent=2));return 0


if __name__=="__main__":raise SystemExit(main())
