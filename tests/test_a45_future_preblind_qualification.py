import json
from datetime import datetime, timezone
from pathlib import Path

from tools.afip_a45_future_preblind_qualification import build_report, write_outputs


def _seed(root: Path, days: int = 15) -> None:
    a42 = root / "runtime/research/a42_selective_trading_rankings"
    a42.mkdir(parents=True)
    a42.joinpath("a42_selective_trading_rankings.json").write_text(json.dumps({"standard_ranking": [{
        "dimension": "POLICY_HOUR_UTC", "key": "FIXED_TP|3", "policy_id": "FIXED_TP",
        "planned_rr": 2.0, "minimum_sl_points_observed": 500.0, "standard_composite_score": 80.0,
    }]}), encoding="utf-8")
    a40 = root / "runtime/research/a40_time_session_outcomes"
    a40.mkdir(parents=True)
    rows=[]
    for day in range(1, days + 1):
        rows.append({"selection_policy_version":"A41_V2_DEDUP_CONF60_COOLDOWN24","candidate_group_id":f"C{day}",
                     "policy_id":"FIXED_TP","hour_utc":3,"calendar_day_utc":f"2027-01-{day:02d}",
                     "decision_timestamp_utc":f"2027-01-{day:02d}T03:00:00Z","net_realized_r":1.0})
    a40.joinpath("a40_normalized_closed_outcomes.jsonl").write_text("".join(json.dumps(x)+"\n" for x in rows), encoding="utf-8")


def test_a45_freezes_protocol_and_seals_metrics_during_window(tmp_path: Path) -> None:
    _seed(tmp_path)
    report=build_report(tmp_path,datetime(2026,12,31,tzinfo=timezone.utc))
    assert report["status"]=="SEALED_PROSPECTIVE_QUALIFICATION_ACCUMULATING"
    assert report["metrics_sealed"] is True and report["rule_evaluations"][0]["metrics"] is None
    assert report["blind_used_for_selection"] is False and report["execution_authority"]=="NONE"


def test_a45_releases_after_fixed_window_and_freezes_winner(tmp_path: Path) -> None:
    _seed(tmp_path)
    first=build_report(tmp_path,datetime(2026,12,31,tzinfo=timezone.utc));write_outputs(first,tmp_path)
    final=build_report(tmp_path,datetime(2027,2,1,tzinfo=timezone.utc))
    assert final["status"]=="FROZEN_PREBLIND_WINNER_READY_FOR_NEW_BLIND"
    assert final["frozen_preblind_winner_rule_id"]=="POLICY_HOUR_UTC:FIXED_TP|3"
    assert final["rule_evaluations"][0]["metrics"]["expectancy_r"]==1.0


def test_a45_insufficient_days_does_not_choose_winner(tmp_path: Path) -> None:
    _seed(tmp_path,days=14)
    first=build_report(tmp_path,datetime(2026,12,31,tzinfo=timezone.utc));write_outputs(first,tmp_path)
    final=build_report(tmp_path,datetime(2027,2,1,tzinfo=timezone.utc))
    assert final["status"]=="NO_WINNER_NEW_QUALIFICATION_COHORT_REQUIRED"
    assert final["frozen_preblind_winner"] is None


def test_a45_cutoff_and_candidate_rules_are_immutable(tmp_path: Path) -> None:
    _seed(tmp_path)
    first=build_report(tmp_path,datetime(2026,12,31,tzinfo=timezone.utc));write_outputs(first,tmp_path)
    a42=tmp_path/"runtime/research/a42_selective_trading_rankings/a42_selective_trading_rankings.json"
    changed=json.loads(a42.read_text());changed["standard_ranking"]=[];a42.write_text(json.dumps(changed))
    second=build_report(tmp_path,datetime(2027,1,2,tzinfo=timezone.utc))
    assert second["cutoff_timestamp_utc"]==first["cutoff_timestamp_utc"]
    assert second["frozen_rules"]==first["frozen_rules"]
    assert second["source_contract_signature_sha256"]==first["source_contract_signature_sha256"]


def test_a45_outputs_and_no_execution_api(tmp_path: Path) -> None:
    _seed(tmp_path);report=build_report(tmp_path,datetime(2026,12,31,tzinfo=timezone.utc))
    assert all(path.exists() for path in write_outputs(report,tmp_path))
    text=(Path(__file__).parents[1]/"tools/afip_a45_future_preblind_qualification.py").read_text()
    assert "MetaTrader5" not in text and ".order_send(" not in text
