import json
from pathlib import Path

from tools.afip_a47_intermittent_prospective_catchup import TIMEFRAMES,build_commands,run_catchup,write_outputs


def _seed(root:Path)->None:
    out=root/"runtime/research/a45_future_preblind_qualification";out.mkdir(parents=True)
    out.joinpath("a45_future_preblind_qualification.json").write_text(json.dumps({
        "cutoff_timestamp_utc":"2026-08-18T14:51:11+00:00","source_contract_signature_sha256":"a"*64,
        "frozen_rules":[{"dimension":"POLICY_HOUR_UTC","key":"FIXED_TP|3"}]}),encoding="utf-8")


def _offline(root:Path,replay:int,batches:int):
    return {"a45_status":"SEALED_PROSPECTIVE_QUALIFICATION_ACCUMULATING","a46_status":"COLLECTING_PROSPECTIVE_COHORT","future_source_rows_in_window":3}


def test_a47_builds_stable_exact_profile_resume_commands(tmp_path:Path)->None:
    _seed(tmp_path);commands=build_commands(tmp_path,"P1",4)
    assert len(commands)==7
    for timeframe,command in zip(TIMEFRAMES,commands):
        assert command[command.index("--timeframe")+1]==timeframe
        assert command[command.index("--request-id")+1]==f"A47-GOLD-{timeframe}-P1"
        assert command[command.index("--start-utc")+1]=="2026-08-18T14:51:11+00:00"


def test_a47_completes_one_shot_and_allows_shutdown(tmp_path:Path)->None:
    _seed(tmp_path)
    def runner(command):return {"return_code":0,"payload":{"result":{"status":"COMPLETED"}},"stderr_tail":""}
    report=run_catchup(tmp_path,command_runner=runner,offline_runner=_offline)
    assert report["status"]=="CATCHUP_COMPLETE_MACHINE_MAY_SHUT_DOWN"
    assert report["operator_may_close_after_completion"] is True and len(report["backfill_results"])==7
    assert report["a45_protocol_unchanged"] is True and report["execution_authority"]=="NONE"


def test_a47_stops_fail_closed_on_timeframe_failure(tmp_path:Path)->None:
    _seed(tmp_path);calls=[]
    def runner(command):
        calls.append(command);return {"return_code":2 if len(calls)==3 else 0,"payload":{},"stderr_tail":"blocked"}
    report=run_catchup(tmp_path,command_runner=runner,offline_runner=_offline)
    assert report["status"]=="BLOCKED_CATCHUP_INCOMPLETE" and len(calls)==3
    assert report["offline_pipeline"]=={} and report["operator_may_close_after_completion"] is False


def test_a47_treats_not_yet_closed_higher_timeframe_as_waiting_not_failure(tmp_path:Path)->None:
    _seed(tmp_path);calls=[]
    def runner(command):
        calls.append(command);timeframe=command[command.index("--timeframe")+1]
        if timeframe in {"H4","D1"}:
            return {"return_code":2,"payload":{"result":{"status":"NO_DATA","reason":"historical_range_unavailable"},
                    "dashboard":{"status":"NO_DATA","reason":"historical_range_unavailable","coverage_start_utc":"2026-08-18T14:51:11+00:00","coverage_end_utc":"2026-08-18T13:00:00+00:00"}},"stderr_tail":""}
        return {"return_code":0,"payload":{"result":{"status":"COMPLETED"}},"stderr_tail":""}
    report=run_catchup(tmp_path,command_runner=runner,offline_runner=_offline)
    assert len(calls)==7 and report["status"]=="CATCHUP_COMPLETE_WITH_TIMEFRAMES_WAITING_MACHINE_MAY_SHUT_DOWN"
    assert report["timeframes_waiting_for_first_closed_bar"]==2
    assert report["operator_may_close_after_completion"] is True and report["offline_pipeline"]


def test_a47_refuses_missing_a45_protocol(tmp_path:Path)->None:
    try:build_commands(tmp_path)
    except ValueError as exc:assert str(exc)=="A45_FROZEN_PROTOCOL_UNAVAILABLE"
    else:raise AssertionError("missing A45 protocol must fail closed")


def test_a47_outputs_and_has_no_order_api(tmp_path:Path)->None:
    _seed(tmp_path)
    report=run_catchup(tmp_path,command_runner=lambda command:{"return_code":0,"payload":{},"stderr_tail":""},offline_runner=_offline)
    assert all(path.exists() for path in write_outputs(report,tmp_path))
    text=(Path(__file__).parents[1]/"tools/afip_a47_intermittent_prospective_catchup.py").read_text()
    assert "MetaTrader5" not in text and ".order_send(" not in text and "mt5.initialize" not in text
