import json
from datetime import datetime, timezone
from pathlib import Path

from tools.afip_a44_future_blind_cohort_accumulator import build_report, write_outputs


def _seed_a43(root: Path, winner: bool = True) -> None:
    out = root / "runtime/research/a43_ultimate_selective_setup_validation"
    out.mkdir(parents=True)
    rule = {"rule_id": "POLICY_HOUR_UTC:FIXED_TP|3", "dimension": "POLICY_HOUR_UTC", "key": "FIXED_TP|3",
            "policy_id": "FIXED_TP", "planned_rr": 2.0, "minimum_sl_points_observed": 500.0}
    out.joinpath("a43_ultimate_selective_setup_validation.json").write_text(json.dumps({
        "schema": "afip.a43.ultimate_selective_setup_validation.v2", "status": "NO_TRADE_NEW_BLIND_COHORT_REQUIRED",
        "frozen_winner_rule_id": rule["rule_id"] if winner else None, "frozen_winner": rule if winner else None,
    }), encoding="utf-8")


def _seed_rows(root: Path, days: int) -> None:
    out = root / "runtime/research/a40_time_session_outcomes"
    out.mkdir(parents=True)
    rows = []
    for day in range(1, days + 1):
        for hour in (3, 4):
            rows.append({"selection_policy_version": "A41_V2_DEDUP_CONF60_COOLDOWN24", "candidate_group_id": f"C{day}-{hour}",
                         "policy_id": "FIXED_TP", "hour_utc": hour, "calendar_day_utc": f"2027-01-{day:02d}",
                         "decision_timestamp_utc": f"2027-01-{day:02d}T{hour:02d}:00:00Z", "net_realized_r": 2 if day % 2 else -1})
    out.joinpath("a40_normalized_closed_outcomes.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_a44_blocks_without_preblind_frozen_winner(tmp_path: Path) -> None:
    _seed_a43(tmp_path, winner=False)
    report, rows = build_report(tmp_path, datetime(2026, 12, 31, tzinfo=timezone.utc))
    assert report["status"] == "BLOCKED_NO_PREBLIND_FROZEN_WINNER" and rows == []
    assert report["execution_authority"] == "NONE" and report["final_research_recommendation"] == "NO_TRADE"


def test_a44_accepts_only_future_first_match_per_day_and_seals_metrics(tmp_path: Path) -> None:
    _seed_a43(tmp_path); _seed_rows(tmp_path, 14)
    report, rows = build_report(tmp_path, datetime(2026, 12, 31, tzinfo=timezone.utc))
    assert len(rows) == 14 and all(row["hour_utc"] == 3 for row in rows)
    assert report["status"] == "SEALED_ACCUMULATING" and report["cohort"]["metrics_sealed"] is True
    assert report["cohort"]["win_rate_pct"] is None and report["cohort"]["remaining_days"] == 1


def test_a44_reaches_release_condition_without_calculating_metrics(tmp_path: Path) -> None:
    _seed_a43(tmp_path); _seed_rows(tmp_path, 15)
    report, rows = build_report(tmp_path, datetime(2026, 12, 31, tzinfo=timezone.utc))
    assert report["status"] == "COHORT_COMPLETE_METRICS_READY_FOR_A43_AUDIT"
    assert report["cohort"]["metrics_sealed"] is False and len(rows) == 15
    assert report["final_research_recommendation"] == "NO_TRADE"


def test_a44_freezes_cutoff_signature_and_rejects_winner_change(tmp_path: Path) -> None:
    _seed_a43(tmp_path); _seed_rows(tmp_path, 1)
    first, rows = build_report(tmp_path, datetime(2026, 12, 31, tzinfo=timezone.utc)); write_outputs(first, rows, tmp_path)
    second, _ = build_report(tmp_path, datetime(2027, 1, 2, tzinfo=timezone.utc))
    assert second["cutoff_timestamp_utc"] == first["cutoff_timestamp_utc"]
    assert second["source_contract_signature_sha256"] == first["source_contract_signature_sha256"]
    a43 = tmp_path / "runtime/research/a43_ultimate_selective_setup_validation/a43_ultimate_selective_setup_validation.json"
    value = json.loads(a43.read_text()); value["frozen_winner_rule_id"] = "CHANGED"; value["frozen_winner"]["rule_id"] = "CHANGED"; a43.write_text(json.dumps(value))
    blocked, _ = build_report(tmp_path, datetime(2027, 1, 3, tzinfo=timezone.utc))
    assert blocked["status"] == "BLOCKED_FROZEN_WINNER_CHANGED"


def test_a44_outputs_and_contains_no_execution_api(tmp_path: Path) -> None:
    _seed_a43(tmp_path); _seed_rows(tmp_path, 2)
    report, rows = build_report(tmp_path, datetime(2026, 12, 31, tzinfo=timezone.utc))
    assert all(path.exists() for path in write_outputs(report, rows, tmp_path))
    text = (Path(__file__).parents[1] / "tools/afip_a44_future_blind_cohort_accumulator.py").read_text()
    assert "MetaTrader5" not in text and ".order_send(" not in text


def test_a44_accepts_only_a45_completed_preblind_winner(tmp_path: Path) -> None:
    _seed_a43(tmp_path, winner=False)
    out=tmp_path/"runtime/research/a45_future_preblind_qualification";out.mkdir(parents=True)
    rule={"rule_id":"POLICY_HOUR_UTC:FIXED_TP|3","dimension":"POLICY_HOUR_UTC","key":"FIXED_TP|3",
          "policy_id":"FIXED_TP","planned_rr":2.0,"minimum_sl_points_observed":500.0}
    out.joinpath("a45_future_preblind_qualification.json").write_text(json.dumps({
        "status":"FROZEN_PREBLIND_WINNER_READY_FOR_NEW_BLIND","frozen_preblind_winner_rule_id":rule["rule_id"],
        "frozen_preblind_winner":rule}),encoding="utf-8")
    report,_=build_report(tmp_path,datetime(2026,12,31,tzinfo=timezone.utc))
    assert report["frozen_winner_rule_id"]==rule["rule_id"]
    assert report["frozen_winner_authority"]=="A45_PROSPECTIVE_PREBLIND"
