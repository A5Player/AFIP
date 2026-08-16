"""A42 selective trading rankings from A40 candidate-group outcomes."""
from __future__ import annotations
import argparse,json,math
from collections import Counter,defaultdict
from datetime import datetime,timezone
from html import escape
from pathlib import Path
from statistics import mean
from typing import Any,Iterable

OUTPUT="runtime/research/a42_selective_trading_rankings"
POLICY_RR={"FIXED_TP":2.0,"BREAK_EVEN_FIXED_TP":2.0,"R_STEP":1.5,"MFE_PERCENT":1.0,
           "ATR":1.0,"STRUCTURE":1.0,"HYBRID_R_STRUCTURE":1.5,"PARTIAL_RUNNER":2.0}
MINIMUM={"train":30,"validation":15,"blind_forward":15,"sl_points":500,"walk_forward_passes":3,"walk_forward_windows":4}
CAPS=(1,3,5,10,None)

def _number(v:Any)->float|None:
    try:r=float(v)
    except (TypeError,ValueError):return None
    return r if math.isfinite(r) else None

def _load(root:Path)->list[dict[str,Any]]:
    path=root/"runtime/research/a40_time_session_outcomes/a40_normalized_closed_outcomes.jsonl"
    if not path.exists():return []
    rows=[]
    for line in path.read_text(encoding="utf-8").splitlines():
        try:row=json.loads(line)
        except json.JSONDecodeError:continue
        if row.get("selection_policy_version")=="A41_V2_DEDUP_CONF60_COOLDOWN24" and row.get("policy_variant_is_independent_trade") is False:rows.append(row)
    return rows

def _metrics(rows:Iterable[dict[str,Any]])->dict[str,Any]:
    values=sorted(rows,key=lambda x:(str(x.get("decision_timestamp_utc","")),str(x.get("outcome_id",""))))
    pnl=[float(x["net_realized_r"]) for x in values];wins=sum(x>0 for x in pnl);losses=sum(x<0 for x in pnl)
    gross_win=sum(x for x in pnl if x>0);gross_loss=-sum(x for x in pnl if x<0);equity=peak=drawdown=0.0
    for value in pnl:equity+=value;peak=max(peak,equity);drawdown=max(drawdown,peak-equity)
    return {"samples":len(pnl),"wins":wins,"losses":losses,"win_rate_pct":round(wins/len(pnl)*100,6) if pnl else None,
        "expectancy_r":round(mean(pnl),8) if pnl else None,"net_result_r":round(sum(pnl),8),
        "profit_factor":round(gross_win/gross_loss,8) if gross_loss else (None if not gross_win else "INFINITE"),
        "max_drawdown_r":round(drawdown,8)}

def _pf_number(value:Any)->float:
    return 10.0 if value=="INFINITE" else float(value or 0)

def _wf(rows:list[dict[str,Any]])->dict[str,Any]:
    train=sorted((x for x in rows if x["chronological_partition"]=="TRAIN"),key=lambda x:(x["decision_timestamp_utc"],x["outcome_id"]))
    windows=[]
    for window in range(4):
        start=len(train)*window//4;end=len(train)*(window+1)//4;m=_metrics(train[start:end]);m["window"]=window+1
        m["pass"]=m["samples"]>0 and (m["expectancy_r"] or 0)>0 and _pf_number(m["profit_factor"])>=1
        windows.append(m)
    return {"windows":windows,"passes":sum(x["pass"] for x in windows),"window_count":4}

def _dimensions(row:dict[str,Any])->tuple[tuple[str,str],...]:
    policy=str(row["policy_id"]);tf=str(row["timeframe"]);session=str(row["session_name"]);weekday=str(row["weekday_utc"]);hour=str(row["hour_utc"]);direction=str(row["direction"])
    return (("POLICY",policy),("POLICY_TIMEFRAME",f"{policy}|{tf}"),("POLICY_SESSION",f"{policy}|{session}"),
            ("POLICY_WEEKDAY",f"{policy}|{weekday}"),("POLICY_HOUR_UTC",f"{policy}|{hour}"),("POLICY_DIRECTION",f"{policy}|{direction}"))

def _composite(train:dict[str,Any],wf_passes:int)->float:
    expectancy=max(0,min(1,((train["expectancy_r"] or -1)+1)/2));win=max(0,min(1,(train["win_rate_pct"] or 0)/100))
    pf=max(0,min(1,_pf_number(train["profit_factor"])/3));dd=1/(1+(train["max_drawdown_r"] or 0)/max(1,train["samples"]));stability=wf_passes/4
    return round(100*(.35*expectancy+.25*win+.20*pf+.10*dd+.10*stability),6)

def _ranking_rows(rows:list[dict[str,Any]],point_size:float)->list[dict[str,Any]]:
    groups:dict[tuple[str,str],list[dict[str,Any]]]=defaultdict(list)
    for row in rows:
        for key in _dimensions(row):groups[key].append(row)
    result=[]
    for (dimension,key),items in groups.items():
        policy=key.split("|",1)[0];parts={p:_metrics(x for x in items if x["chronological_partition"]==p) for p in ("TRAIN","VALIDATION","BLIND_FORWARD")}
        wf=_wf(items);sl_values=[_number(x.get("initial_risk_distance")) for x in items];sl_values=[x/point_size for x in sl_values if x is not None]
        sl_points=round(min(sl_values),4) if sl_values else 0;rr=POLICY_RR.get(policy)
        reasons=[]
        if parts["TRAIN"]["samples"]<MINIMUM["train"]:reasons.append("TRAIN_SAMPLES_BELOW_30")
        if parts["VALIDATION"]["samples"]<MINIMUM["validation"]:reasons.append("VALIDATION_SAMPLES_BELOW_15")
        if parts["BLIND_FORWARD"]["samples"]<MINIMUM["blind_forward"]:reasons.append("BLIND_FORWARD_SAMPLES_BELOW_15")
        if wf["passes"]<3:reasons.append("TRAIN_WALK_FORWARD_BELOW_3_OF_4")
        if (parts["TRAIN"]["expectancy_r"] or 0)<=0:reasons.append("TRAIN_EXPECTANCY_NOT_POSITIVE")
        if (parts["VALIDATION"]["expectancy_r"] or 0)<=0:reasons.append("VALIDATION_EXPECTANCY_NOT_POSITIVE")
        if _pf_number(parts["VALIDATION"]["profit_factor"])<1:reasons.append("VALIDATION_PROFIT_FACTOR_BELOW_1")
        base_eligible=not reasons
        balanced_reasons=list(reasons)
        if rr is None or rr<1:balanced_reasons.append("PLANNED_RR_BELOW_1_TO_1")
        if sl_points<500:balanced_reasons.append("SL_BELOW_500_POINTS")
        result.append({"dimension":dimension,"key":key,"policy_id":policy,"planned_rr":rr,"minimum_sl_points_observed":sl_points,
            "train":parts["TRAIN"],"validation":parts["VALIDATION"],"blind_forward":parts["BLIND_FORWARD"],"train_walk_forward":wf,
            "standard_composite_score":_composite(parts["TRAIN"],wf["passes"]),"standard_eligible":base_eligible,"standard_reasons":reasons,
            "balanced_eligible":not balanced_reasons,"balanced_reasons":balanced_reasons,"research_only":True,"execution_authority":"NONE"})
    return result

def _daily(rows:list[dict[str,Any]])->list[dict[str,Any]]:
    # One outcome per candidate/policy. Selection is chronological first-N,
    # never retrospective highest-score-of-day.
    by_policy:dict[str,list[dict[str,Any]]]=defaultdict(list)
    for row in rows:by_policy[str(row["policy_id"])].append(row)
    results=[]
    for policy,items in sorted(by_policy.items()):
        for partition in ("TRAIN","VALIDATION","BLIND_FORWARD"):
            source=[x for x in items if x["chronological_partition"]==partition];by_day:dict[str,list[dict[str,Any]]]=defaultdict(list)
            for row in source:by_day[str(row["calendar_day_utc"])].append(row)
            for cap in CAPS:
                selected=[]
                for day in sorted(by_day):
                    chronological=sorted(by_day[day],key=lambda x:(x["decision_timestamp_utc"],x["candidate_group_id"]))
                    selected.extend(chronological if cap is None else chronological[:cap])
                m=_metrics(selected);trading_days=len({x["calendar_day_utc"] for x in selected});days=len(by_day)
                results.append({"policy_id":policy,"daily_policy":"UNLIMITED" if cap is None else f"ZERO_TO_{cap}","maximum_trades_per_candidate_day":cap,
                    "partition":partition,"candidate_days":days,"trading_days":trading_days,"no_trade_candidate_days":days-trading_days,
                    "selection_order":"FIRST_N_CHRONOLOGICALLY_NO_FUTURE_IN_DAY_RANKING",**m,"research_only":True,"execution_authority":"NONE"})
    return results

def build_report(project_root:str|Path)->dict[str,Any]:
    root=Path(project_root).resolve();rows=_load(root)
    a41_path=root/"runtime/research/a41_historical_closed_outcome_bridge/a41_historical_closed_outcome_bridge.json"
    try:a41=json.loads(a41_path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError):a41={}
    point_size=float(a41.get("research_parameters",{}).get("point_size",.01) or .01)
    groups=Counter(str(x.get("candidate_group_id","")) for x in rows);integrity=[]
    if any(v!=7 for v in groups.values()):integrity.append("CANDIDATE_GROUP_POLICY_COUNT_NOT_7")
    if len(rows)!=len(groups)*7:integrity.append("POLICY_OUTCOMES_NOT_EXACTLY_7_PER_CANDIDATE")
    ranking=_ranking_rows(rows,point_size) if rows and not integrity else [];daily=_daily(rows) if rows and not integrity else []
    standard=sorted((x for x in ranking if x["standard_eligible"]),key=lambda x:(x["standard_composite_score"],x["validation"]["expectancy_r"] or -999),reverse=True)
    balanced=sorted((x for x in ranking if x["balanced_eligible"]),key=lambda x:(x["validation"]["win_rate_pct"] or -1,x["validation"]["expectancy_r"] or -999,-x["validation"]["max_drawdown_r"]),reverse=True)
    sessions=[x for x in standard if x["dimension"] in {"POLICY_SESSION","POLICY_WEEKDAY","POLICY_HOUR_UTC","POLICY_TIMEFRAME"}]
    daily_validation=[x for x in daily if x["partition"]=="VALIDATION" and x["samples"]>=15 and (x["expectancy_r"] or 0)>0]
    daily_validation.sort(key=lambda x:(x["expectancy_r"],x["win_rate_pct"] or 0,-x["max_drawdown_r"]),reverse=True)
    ultimate=[x for x in daily_validation if x["daily_policy"]=="ZERO_TO_1"]
    status="READY_FOR_SELECTIVE_TRADING_RESEARCH_REVIEW" if ranking and not integrity else "BLOCKED_SOURCE_INTEGRITY"
    return {"schema":"afip.a42.selective_trading_rankings.v1","generated_at_utc":datetime.now(timezone.utc).isoformat(),"status":status,
        "source":"A40_NORMALIZED_A41_V2_ONLY","source_policy_outcomes":len(rows),"candidate_groups":len(groups),"expected_policy_variants_per_group":7,
        "integrity_blockers":integrity,"method":{"selection_fit":"TRAIN_ONLY_WITH_4_CHRONOLOGICAL_WINDOWS","confirmation":"VALIDATION",
            "final_audit":"BLIND_FORWARD_NOT_USED_TO_RANK","daily_selection":"FIRST_N_CHRONOLOGICALLY","minimum_samples":MINIMUM,
            "standard_composite_weights":{"expectancy":.35,"win_rate":.25,"profit_factor":.20,"drawdown_efficiency":.10,"walk_forward_stability":.10}},
        "ranking_rows":ranking,"standard_ranking":standard,"balanced_win_rate_ranking":balanced,"session_time_ranking":sessions,
        "daily_participation_results":daily,"daily_participation_validation_ranking":daily_validation,"ultimate_zero_to_one_ranking":ultimate,
        "summary":{"standard_eligible":len(standard),"balanced_eligible":len(balanced),"session_time_eligible":len(sessions),
            "daily_policy_rows":len(daily),"ultimate_candidates":len(ultimate)},"no_trade_is_valid":True,"profile_strategy_selection":"NOT_DECIDED",
        "automatic_profile_assignment":False,"demo_order_authorized":False,"live_order_authorized":False,"execution_authority":"NONE","orders_sent":False}

def _metric_cells(row:dict[str,Any])->str:
    v=row["validation"];b=row["blind_forward"]
    return f"<td>{escape(row['dimension'])}</td><td>{escape(row['key'])}</td><td>{row['planned_rr']}</td><td>{row['minimum_sl_points_observed']}</td><td>{v['samples']}</td><td>{v['win_rate_pct']}</td><td>{v['expectancy_r']}</td><td>{v['profit_factor']}</td><td>{v['max_drawdown_r']}</td><td>{b['samples']}</td><td>{b['expectancy_r']}</td>"

def write_outputs(report:dict[str,Any],project_root:str|Path)->tuple[Path,Path]:
    out=Path(project_root).resolve()/OUTPUT;out.mkdir(parents=True,exist_ok=True);jp=out/"a42_selective_trading_rankings.json";hp=out/"a42_selective_trading_rankings.html"
    jp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    sections=[]
    for title,key in (("Standard Composite","standard_ranking"),("Balanced Highest Win Rate","balanced_win_rate_ranking"),("Session / Day / Hour / Timeframe","session_time_ranking")):
        body="".join(f"<tr><td>{i}</td>{_metric_cells(x)}</tr>" for i,x in enumerate(report[key][:100],1))
        sections.append(f"<article><h2>{title}</h2><table><tr><th>Rank</th><th>Dimension</th><th>Key</th><th>RR</th><th>SL pts</th><th>Val N</th><th>Val Win%</th><th>Val Exp R</th><th>Val PF</th><th>Val DD R</th><th>Blind N</th><th>Blind Exp R</th></tr>{body or '<tr><td colspan=12>NO ELIGIBLE ROW</td></tr>'}</table></article>")
    daily="".join(f"<tr><td>{i}</td><td>{escape(x['policy_id'])}</td><td>{escape(x['daily_policy'])}</td><td>{x['samples']}</td><td>{x['win_rate_pct']}</td><td>{x['expectancy_r']}</td><td>{x['profit_factor']}</td><td>{x['max_drawdown_r']}</td></tr>" for i,x in enumerate(report["daily_participation_validation_ranking"],1))
    hp.write_text(f'''<!doctype html><meta charset="utf-8"><title>A42 Selective Trading Rankings</title><style>body{{font:14px system-ui;background:#edf2f7;color:#14243a}}main{{max-width:1500px;margin:auto}}header,article{{background:white;padding:18px;margin:14px;border-radius:14px;overflow:auto}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #d5dee8;padding:7px;white-space:nowrap}}</style><main><header><h1>A42 Selective Trading Rankings</h1><h2>{escape(report['status'])}</h2><p>Candidate groups {report['candidate_groups']} · policy outcomes {report['source_policy_outcomes']} · 7 variants are not 7 trades</p><p>TRAIN fit + 4 windows · VALIDATION confirm · BLIND audit only · no-trade valid · authority NONE</p></header>{''.join(sections)}<article><h2>Daily Participation 0-1 / 0-3 / 0-5 / 0-10 / Unlimited</h2><table><tr><th>Rank</th><th>Policy</th><th>Daily cap</th><th>Val N</th><th>Win%</th><th>Exp R</th><th>PF</th><th>DD R</th></tr>{daily}</table></article></main>''',encoding="utf-8");return jp,hp

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--project-root",type=Path,default=Path.cwd());a=p.parse_args();r=build_report(a.project_root);paths=write_outputs(r,a.project_root)
    print(json.dumps({"status":r["status"],"candidate_groups":r["candidate_groups"],"source_policy_outcomes":r["source_policy_outcomes"],**r["summary"],"outputs":[str(x) for x in paths],"execution_authority":"NONE"},indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
