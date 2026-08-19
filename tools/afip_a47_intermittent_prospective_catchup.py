"""A47 one-shot intermittent prospective catch-up orchestration.

It reuses the exact-terminal resumable historical provider and existing offline
research pipeline.  It never launches MT5, never sends an order, and exits
after one catch-up cycle so the operator may shut the machine down.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime,timezone
from html import escape
from pathlib import Path
from typing import Any,Callable

OUTPUT="runtime/research/a47_intermittent_prospective_catchup"
TIMEFRAMES=("M1","M5","M15","M30","H1","H4","D1")


def _json(path:Path)->dict[str,Any]:
    try:value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError):return {}
    return value if isinstance(value,dict) else {}


def build_commands(project_root:str|Path,profile:str="P1",maximum_batches:int=4)->list[list[str]]:
    root=Path(project_root).resolve();a45=_json(root/"runtime/research/a45_future_preblind_qualification/a45_future_preblind_qualification.json")
    cutoff=a45.get("cutoff_timestamp_utc");signature=a45.get("source_contract_signature_sha256")
    if not cutoff or not signature or not a45.get("frozen_rules"):raise ValueError("A45_FROZEN_PROTOCOL_UNAVAILABLE")
    if maximum_batches<=0:raise ValueError("maximum_batches must be positive")
    return [[sys.executable,"-m","tools.afip_historical_mt5_backfill","--project-root",str(root),"--profile",profile,
             "--timeframe",timeframe,"--start-utc",str(cutoff),"--maximum-batches",str(maximum_batches),
             "--request-id",f"A47-GOLD-{timeframe}-{profile}"] for timeframe in TIMEFRAMES]


def _command(command:list[str])->dict[str,Any]:
    completed=subprocess.run(command,capture_output=True,text=True,check=False)
    payload:dict[str,Any]={}
    if completed.stdout.strip():
        try:payload=json.loads(completed.stdout)
        except json.JSONDecodeError:payload={"stdout_tail":completed.stdout[-2000:]}
    return {"return_code":completed.returncode,"payload":payload,"stderr_tail":completed.stderr[-2000:]}


def _waiting_for_first_closed_bar(result:dict[str,Any])->bool:
    payload=result.get("payload",{}) if isinstance(result.get("payload"),dict) else {}
    provider=payload.get("result",{}) if isinstance(payload.get("result"),dict) else {}
    dashboard=payload.get("dashboard",{}) if isinstance(payload.get("dashboard"),dict) else {}
    status=str(provider.get("status") or dashboard.get("status") or "")
    reason=str(provider.get("reason") or dashboard.get("reason") or "")
    start=str(dashboard.get("coverage_start_utc") or "")
    end=str(dashboard.get("coverage_end_utc") or "")
    return status=="NO_DATA" and reason=="historical_range_unavailable" and bool(start and end and end<start)


def _offline(root:Path,maximum_replay_bars:int,maximum_a41_batches:int)->dict[str,Any]:
    from afip.automatic_research_runtime import AutomaticResearchRuntime
    from tools.afip_a40_time_session_outcome_foundation import build_report as a40_build,write_outputs as a40_write
    from tools.afip_a41_historical_closed_outcome_bridge import build_report as a41_build,write_outputs as a41_write
    from tools.afip_a45_future_preblind_qualification import build_report as a45_build,write_outputs as a45_write
    from tools.afip_a46_prospective_cohort_monitor import build_report as a46_build,write_outputs as a46_write
    automatic=AutomaticResearchRuntime(root,progress=lambda _:None).run(collect_mt5_when_needed=False,maximum_replay_bars=maximum_replay_bars)
    latest_a41={"status":"NOT_RUN","remaining_selected_cases":None};batches=0
    while batches<maximum_a41_batches:
        latest_a41=a41_build(root,maximum_cases=500);a41_write(latest_a41,root);batches+=1
        if int(latest_a41.get("remaining_selected_cases") or 0)<=0:break
    a40=a40_build(root);a40_write(a40,root)
    a45=a45_build(root);a45_write(a45,root)
    a46=a46_build(root);a46_write(a46,root)
    return {"automatic_research":automatic.as_dict(),"a41_status":latest_a41.get("status"),"a41_batches":batches,
            "a41_remaining":latest_a41.get("remaining_selected_cases"),"a40_status":a40.get("status"),
            "a45_status":a45.get("status"),"a46_status":a46.get("status"),
            "future_source_rows_in_window":a46.get("future_source_rows_in_window",0)}


def run_catchup(project_root:str|Path,profile:str="P1",maximum_batches:int=4,maximum_replay_bars:int=5000,
                maximum_a41_batches:int=10,command_runner:Callable[[list[str]],dict[str,Any]]|None=None,
                offline_runner:Callable[[Path,int,int],dict[str,Any]]|None=None)->dict[str,Any]:
    root=Path(project_root).resolve();a45_before=_json(root/"runtime/research/a45_future_preblind_qualification/a45_future_preblind_qualification.json")
    commands=build_commands(root,profile,maximum_batches);runner=command_runner or _command;results=[]
    for timeframe,command in zip(TIMEFRAMES,commands):
        result=runner(command);waiting=_waiting_for_first_closed_bar(result)
        results.append({"timeframe":timeframe,"collection_state":"WAITING_FOR_FIRST_CLOSED_BAR_AFTER_CUTOFF" if waiting else "COLLECTED",**result})
        if int(result.get("return_code",1))!=0 and not waiting:break
    all_completed=len(results)==len(TIMEFRAMES) and all(int(x.get("return_code",1))==0 or x.get("collection_state")=="WAITING_FOR_FIRST_CLOSED_BAR_AFTER_CUTOFF" for x in results)
    offline={}
    if all_completed:offline=(offline_runner or _offline)(root,maximum_replay_bars,maximum_a41_batches)
    a45_after=_json(root/"runtime/research/a45_future_preblind_qualification/a45_future_preblind_qualification.json")
    protocol_unchanged=(a45_before.get("cutoff_timestamp_utc")==a45_after.get("cutoff_timestamp_utc") and
                        a45_before.get("source_contract_signature_sha256")==a45_after.get("source_contract_signature_sha256"))
    errors=[]
    if not all_completed:errors.append("ONE_OR_MORE_TIMEFRAME_BACKFILLS_BLOCKED")
    if all_completed and not protocol_unchanged:errors.append("A45_PROTOCOL_CHANGED_DURING_CATCHUP")
    waiting_count=sum(x.get("collection_state")=="WAITING_FOR_FIRST_CLOSED_BAR_AFTER_CUTOFF" for x in results)
    status=("CATCHUP_COMPLETE_WITH_TIMEFRAMES_WAITING_MACHINE_MAY_SHUT_DOWN" if all_completed and waiting_count and not errors else
            "CATCHUP_COMPLETE_MACHINE_MAY_SHUT_DOWN" if all_completed and not errors else "BLOCKED_CATCHUP_INCOMPLETE")
    return {"schema":"afip.a47.intermittent_prospective_catchup.v1","generated_at_utc":datetime.now(timezone.utc).isoformat(),
            "status":status,"profile":profile,"manual_mt5_required":True,"mt5_auto_launch":False,"timeframes":list(TIMEFRAMES),
            "backfill_results":results,"timeframes_waiting_for_first_closed_bar":waiting_count,"offline_pipeline":offline,"a45_protocol_unchanged":protocol_unchanged,"errors":errors,
            "resume_policy":"STABLE_REQUEST_ID_AND_EXISTING_HISTORICAL_BACKFILL_CHECKPOINT",
            "operator_may_close_after_completion":status in {"CATCHUP_COMPLETE_MACHINE_MAY_SHUT_DOWN","CATCHUP_COMPLETE_WITH_TIMEFRAMES_WAITING_MACHINE_MAY_SHUT_DOWN"},
            "outcome_metrics_exposed":False,"final_research_recommendation":"NO_TRADE","demo_order_authorized":False,
            "live_order_authorized":False,"execution_authority":"NONE","orders_sent":False}


def write_outputs(report:dict[str,Any],project_root:str|Path)->tuple[Path,Path]:
    out=Path(project_root).resolve()/OUTPUT;out.mkdir(parents=True,exist_ok=True);jp=out/"a47_intermittent_prospective_catchup.json";hp=out/"a47_intermittent_prospective_catchup.html"
    jp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    rows="".join(f'<tr><td>{escape(str(x.get("timeframe")))}</td><td>{escape(str(x.get("return_code")))}</td><td>{escape(str(x.get("payload",{}).get("result",{}).get("status","UNKNOWN")))}</td></tr>' for x in report.get("backfill_results",()))
    hp.write_text(f'''<!doctype html><meta charset="utf-8"><title>A47 Intermittent Catch-Up</title><style>body{{font:14px system-ui;background:#edf2f7;color:#14243a}}main{{max-width:1100px;margin:auto;background:white;padding:20px;border-radius:14px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #d5dee8;padding:8px}}</style><main><h1>A47 Intermittent Prospective Catch-Up</h1><h2>{escape(str(report['status']))}</h2><table><tr><th>Timeframe</th><th>Return</th><th>Provider status</th></tr>{rows}</table><p>A45 protocol unchanged: {report['a45_protocol_unchanged']} · machine may shut down: {report['operator_may_close_after_completion']}</p><p>Manual MT5 only · no auto-launch · NO_TRADE · authority NONE</p></main>''',encoding="utf-8");return jp,hp


def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument("--project-root",type=Path,default=Path.cwd());parser.add_argument("--profile",choices=("P1","P2","P3","P4"),default="P1");parser.add_argument("--maximum-batches",type=int,default=4);parser.add_argument("--maximum-replay-bars",type=int,default=5000);args=parser.parse_args()
    try:report=run_catchup(args.project_root,args.profile,args.maximum_batches,args.maximum_replay_bars)
    except ValueError as exc:report={"schema":"afip.a47.intermittent_prospective_catchup.v1","status":"BLOCKED_A45_PROTOCOL_UNAVAILABLE","reason":str(exc),"execution_authority":"NONE","orders_sent":False}
    paths=write_outputs(report,args.project_root);print(json.dumps({"status":report["status"],"timeframes_completed":len(report.get("backfill_results",())),"timeframes_waiting_for_first_closed_bar":report.get("timeframes_waiting_for_first_closed_bar",0),"offline_pipeline":report.get("offline_pipeline",{}),"machine_may_shut_down":report.get("operator_may_close_after_completion",False),"outputs":[str(x) for x in paths],"execution_authority":"NONE"},indent=2));return 0 if report.get("operator_may_close_after_completion") else 2


if __name__=="__main__":raise SystemExit(main())
