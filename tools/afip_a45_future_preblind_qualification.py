"""A45 prospective pre-Blind qualification and winner freeze protocol."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from statistics import mean
from typing import Any

OUTPUT = "runtime/research/a45_future_preblind_qualification"
SOURCE_POLICY_VERSION = "A41_V2_DEDUP_CONF60_COOLDOWN24"
WINDOW_DAYS = 30
MINIMUM_RULE_DAYS = 15


def _json(path: Path) -> dict[str, Any]:
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return {}
    return value if isinstance(value, dict) else {}


def _utc(value: Any) -> datetime | None:
    try: parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError): return None
    if parsed.tzinfo is None: parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists(): return []
    result=[]
    for line in path.read_text(encoding="utf-8").splitlines():
        try: row=json.loads(line)
        except json.JSONDecodeError: continue
        if isinstance(row,dict) and row.get("selection_policy_version")==SOURCE_POLICY_VERSION: result.append(row)
    return result


def _matches(row: dict[str, Any], rule: dict[str, Any]) -> bool:
    key=str(rule.get("key", ""));policy,value=key.split("|",1) if "|" in key else (key,"")
    if str(row.get("policy_id"))!=policy:return False
    mapping={"POLICY_TIMEFRAME":str(row.get("timeframe")),"POLICY_SESSION":str(row.get("session_name")),
             "POLICY_WEEKDAY":str(row.get("weekday_utc")),"POLICY_HOUR_UTC":str(row.get("hour_utc")),
             "POLICY_DIRECTION":str(row.get("direction"))}
    return rule.get("dimension")=="POLICY" or mapping.get(str(rule.get("dimension")))==value


def _first_day(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped:dict[str,list[dict[str,Any]]]=defaultdict(list)
    for row in rows:
        if row.get("calendar_day_utc"):grouped[str(row["calendar_day_utc"])].append(row)
    return [sorted(grouped[day],key=lambda x:(str(x.get("decision_timestamp_utc")),str(x.get("candidate_group_id"))))[0] for day in sorted(grouped)]


def _metrics(rows:list[dict[str,Any]])->dict[str,Any]:
    pnl=[float(row.get("net_realized_r") or 0) for row in rows];wins=sum(x>0 for x in pnl);gw=sum(x for x in pnl if x>0);gl=-sum(x for x in pnl if x<0)
    equity=peak=drawdown=0.0
    for value in pnl:equity+=value;peak=max(peak,equity);drawdown=max(drawdown,peak-equity)
    return {"samples":len(pnl),"win_rate_pct":round(100*wins/len(pnl),6) if pnl else None,
            "expectancy_r":round(mean(pnl),8) if pnl else None,"profit_factor":round(gw/gl,8) if gl else ("INFINITE" if gw else None),
            "max_drawdown_r":round(drawdown,8),"net_result_r":round(sum(pnl),8)}


def _signature(rules:list[dict[str,Any]],cutoff:str,end:str)->str:
    payload={"schema":"afip.a45.future_preblind_qualification.v1","rules":rules,"cutoff":cutoff,"end":end,
             "minimum_rule_days":MINIMUM_RULE_DAYS,"selection":"FIRST_MATCH_CHRONOLOGICALLY_PER_UTC_DAY"}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()


def build_report(project_root:str|Path,now_utc:datetime|None=None)->dict[str,Any]:
    root=Path(project_root).resolve();out=root/OUTPUT;previous=_json(out/"a45_future_preblind_qualification.json")
    a42=_json(root/"runtime/research/a42_selective_trading_rankings/a42_selective_trading_rankings.json")
    now=(now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    frozen=previous.get("frozen_rules") if isinstance(previous.get("frozen_rules"),list) else []
    if not frozen:
        frozen=[{k:item.get(k) for k in ("dimension","key","policy_id","planned_rr","minimum_sl_points_observed","standard_composite_score")}
                for item in a42.get("standard_ranking",()) if isinstance(item,dict)]
    if not frozen:
        return {"schema":"afip.a45.future_preblind_qualification.v1","generated_at_utc":now.isoformat(),
                "status":"BLOCKED_NO_FROZEN_A42_RULES","frozen_rules":[],"frozen_preblind_winner":None,
                "final_research_recommendation":"NO_TRADE","execution_authority":"NONE","orders_sent":False}
    cutoff=str(previous.get("cutoff_timestamp_utc") or now.isoformat());cutoff_dt=_utc(cutoff)
    end=str(previous.get("qualification_end_timestamp_utc") or ((cutoff_dt or now)+timedelta(days=WINDOW_DAYS)).isoformat());end_dt=_utc(end)
    signature=_signature(frozen,cutoff,end)
    if previous.get("source_contract_signature_sha256") not in (None,signature):
        result=dict(previous);result.update({"generated_at_utc":now.isoformat(),"status":"BLOCKED_FROZEN_PROTOCOL_CHANGED",
                                            "observed_source_contract_signature_sha256":signature,"execution_authority":"NONE"});return result
    source=_rows(root/"runtime/research/a40_time_session_outcomes/a40_normalized_closed_outcomes.jsonl")
    evaluations=[]
    for rule in frozen:
        chosen=_first_day([row for row in source if (stamp:=_utc(row.get("decision_timestamp_utc"))) is not None and cutoff_dt is not None and end_dt is not None and cutoff_dt<stamp<=end_dt and _matches(row,rule)])
        evaluations.append({"rule_id":f'{rule.get("dimension")}:{rule.get("key")}',"rule":rule,"independent_days":len(chosen),
                            "minimum_required_days":MINIMUM_RULE_DAYS,"metrics":None,"sealed":now<end_dt if end_dt else True,"_chosen":chosen})
    window_complete=bool(end_dt and now>=end_dt)
    eligible=[]
    if window_complete:
        for item in evaluations:
            item["sealed"]=False;item["metrics"]=_metrics(item.pop("_chosen"))
            if item["independent_days"]>=MINIMUM_RULE_DAYS and (item["metrics"]["expectancy_r"] or 0)>0:eligible.append(item)
    else:
        for item in evaluations:item.pop("_chosen",None)
    eligible.sort(key=lambda x:(x["metrics"]["expectancy_r"],x["metrics"]["win_rate_pct"],-x["metrics"]["max_drawdown_r"],x["rule"].get("standard_composite_score") or 0),reverse=True)
    winner=eligible[0] if eligible else None
    status="FROZEN_PREBLIND_WINNER_READY_FOR_NEW_BLIND" if winner else ("NO_WINNER_NEW_QUALIFICATION_COHORT_REQUIRED" if window_complete else "SEALED_PROSPECTIVE_QUALIFICATION_ACCUMULATING")
    return {"schema":"afip.a45.future_preblind_qualification.v1","generated_at_utc":now.isoformat(),"status":status,
            "cutoff_timestamp_utc":cutoff,"qualification_end_timestamp_utc":end,"window_days":WINDOW_DAYS,
            "source_contract_signature_sha256":signature,"frozen_rules":frozen,"rule_evaluations":evaluations,
            "metrics_sealed":not window_complete,"minimum_rule_days":MINIMUM_RULE_DAYS,"eligible_rules":len(eligible),
            "frozen_preblind_winner_rule_id":winner["rule_id"] if winner else None,
            "frozen_preblind_winner":winner["rule"] if winner else None,"blind_used_for_selection":False,
            "historical_exposed_blind_reused":False,"final_research_recommendation":"NO_TRADE",
            "demo_order_authorized":False,"live_order_authorized":False,"execution_authority":"NONE","orders_sent":False}


def write_outputs(report:dict[str,Any],project_root:str|Path)->tuple[Path,Path]:
    out=Path(project_root).resolve()/OUTPUT;out.mkdir(parents=True,exist_ok=True);jp=out/"a45_future_preblind_qualification.json";hp=out/"a45_future_preblind_qualification.html"
    jp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    rows="".join(f'<tr><td>{escape(str(x.get("rule_id")))}</td><td>{x.get("independent_days",0)} / {x.get("minimum_required_days",15)}</td><td>{escape(str(x.get("sealed")))}</td></tr>' for x in report.get("rule_evaluations",()))
    hp.write_text(f'''<!doctype html><meta charset="utf-8"><title>A45 Future Pre-Blind Qualification</title><style>body{{font:14px system-ui;background:#edf2f7;color:#14243a}}main{{max-width:1100px;margin:auto;background:white;padding:20px;border-radius:14px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #d5dee8;padding:8px}}</style><main><h1>A45 Future Pre-Blind Qualification</h1><h2>{escape(str(report.get("status")))}</h2><p>Cutoff {escape(str(report.get("cutoff_timestamp_utc")))} · end {escape(str(report.get("qualification_end_timestamp_utc")))}</p><p>Metrics sealed {escape(str(report.get("metrics_sealed")))} · winner {escape(str(report.get("frozen_preblind_winner_rule_id")))}</p><table><tr><th>Frozen rule</th><th>Independent days</th><th>Sealed</th></tr>{rows}</table><p>NO_TRADE · Blind is not used for selection · authority NONE</p></main>''',encoding="utf-8");return jp,hp


def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument("--project-root",type=Path,default=Path.cwd());args=parser.parse_args();report=build_report(args.project_root);paths=write_outputs(report,args.project_root)
    print(json.dumps({"status":report["status"],"frozen_rule_count":len(report.get("frozen_rules",())),"metrics_sealed":report.get("metrics_sealed"),"frozen_preblind_winner_rule_id":report.get("frozen_preblind_winner_rule_id"),"outputs":[str(x) for x in paths],"execution_authority":"NONE"},indent=2));return 0


if __name__=="__main__":raise SystemExit(main())
