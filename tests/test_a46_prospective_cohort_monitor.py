import json
from datetime import datetime,timezone
from pathlib import Path

from tools.afip_a46_prospective_cohort_monitor import build_report,write_outputs


def _seed(root:Path,rows:int=0)->None:
    a45=root/"runtime/research/a45_future_preblind_qualification";a45.mkdir(parents=True)
    rule={"dimension":"POLICY_HOUR_UTC","key":"FIXED_TP|3","policy_id":"FIXED_TP"}
    a45.joinpath("a45_future_preblind_qualification.json").write_text(json.dumps({
        "status":"SEALED_PROSPECTIVE_QUALIFICATION_ACCUMULATING","cutoff_timestamp_utc":"2027-01-01T00:00:00+00:00",
        "qualification_end_timestamp_utc":"2027-01-31T00:00:00+00:00","source_contract_signature_sha256":"a"*64,
        "frozen_rules":[rule],"minimum_rule_days":15,"metrics_sealed":True}),encoding="utf-8")
    a40=root/"runtime/research/a40_time_session_outcomes";a40.mkdir(parents=True)
    values=[]
    for day in range(2,2+rows):
        values.append({"selection_policy_version":"A41_V2_DEDUP_CONF60_COOLDOWN24","candidate_group_id":f"C{day}",
                       "policy_id":"FIXED_TP","hour_utc":3,"calendar_day_utc":f"2027-01-{day:02d}",
                       "decision_timestamp_utc":f"2027-01-{day:02d}T03:00:00Z","net_realized_r":999})
    a40.joinpath("a40_normalized_closed_outcomes.jsonl").write_text("".join(json.dumps(x)+"\n" for x in values),encoding="utf-8")


def test_a46_waits_without_outcomes_and_exposes_no_metrics(tmp_path:Path)->None:
    _seed(tmp_path);report=build_report(tmp_path,datetime(2027,1,2,tzinfo=timezone.utc))
    assert report["status"]=="WAITING_FOR_FIRST_FUTURE_SOURCE_OUTCOME"
    assert report["outcome_metrics_accessed"] is False and report["expectancy_r"] is None
    assert report["execution_authority"]=="NONE"


def test_a46_counts_rule_days_without_reading_outcome_value(tmp_path:Path)->None:
    _seed(tmp_path,3);report=build_report(tmp_path,datetime(2027,1,4,4,tzinfo=timezone.utc))
    assert report["status"]=="COLLECTING_PROSPECTIVE_COHORT"
    assert report["future_source_rows_in_window"]==3
    assert report["rule_coverage"][0]["independent_days"]==3
    assert report["rule_coverage"][0]["outcome_metrics_accessed"] is False


def test_a46_warns_after_72_hours_without_future_flow(tmp_path:Path)->None:
    _seed(tmp_path);report=build_report(tmp_path,datetime(2027,1,5,tzinfo=timezone.utc))
    assert report["status"]=="WARNING_NO_FUTURE_SOURCE_OUTCOME_72H"


def test_a46_detects_protocol_mutation_fail_closed(tmp_path:Path)->None:
    _seed(tmp_path);first=build_report(tmp_path,datetime(2027,1,2,tzinfo=timezone.utc));write_outputs(first,tmp_path)
    path=tmp_path/"runtime/research/a45_future_preblind_qualification/a45_future_preblind_qualification.json"
    value=json.loads(path.read_text());value["source_contract_signature_sha256"]="b"*64;path.write_text(json.dumps(value))
    second=build_report(tmp_path,datetime(2027,1,3,tzinfo=timezone.utc))
    assert second["status"]=="BLOCKED_A45_MONITORING_CONTRACT_INVALID"
    assert "A45_SIGNATURE_CHANGED_AFTER_MONITORING_STARTED" in second["contract_errors"]


def test_a46_requests_finalize_after_window(tmp_path:Path)->None:
    _seed(tmp_path,3);report=build_report(tmp_path,datetime(2027,2,1,tzinfo=timezone.utc))
    assert report["status"]=="WINDOW_COMPLETE_RUN_A45_TO_FINALIZE"


def test_a46_outputs_and_contains_no_execution_api(tmp_path:Path)->None:
    _seed(tmp_path);report=build_report(tmp_path,datetime(2027,1,2,tzinfo=timezone.utc))
    assert all(path.exists() for path in write_outputs(report,tmp_path))
    text=(Path(__file__).parents[1]/"tools/afip_a46_prospective_cohort_monitor.py").read_text()
    assert "MetaTrader5" not in text and ".order_send(" not in text
