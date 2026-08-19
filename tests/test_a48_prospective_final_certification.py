import json
from pathlib import Path

from tools.afip_a48_prospective_final_certification import build_report, write_outputs


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_waits_fail_closed_before_a45_winner(tmp_path: Path):
    _write(tmp_path / "runtime/research/a45_future_preblind_qualification/a45_future_preblind_qualification.json", {"status": "SEALED_PROSPECTIVE_QUALIFICATION_ACCUMULATING"})
    report = build_report(tmp_path)
    assert report["status"] == "WAITING_FOR_A45_FROZEN_PREBLIND_WINNER"
    assert report["execution_authority"] == "NONE"
    assert report["blind_metrics"] is None


def test_keeps_metrics_sealed_until_a44_complete(tmp_path: Path):
    _write(tmp_path / "runtime/research/a45_future_preblind_qualification/a45_future_preblind_qualification.json", {"status": "FROZEN_PREBLIND_WINNER_READY_FOR_NEW_BLIND", "frozen_preblind_winner_rule_id": "R", "frozen_preblind_winner": {"planned_rr": 2}})
    _write(tmp_path / "runtime/research/a44_future_blind_cohort_accumulator/a44_future_blind_cohort_accumulator.json", {"status": "SEALED_ACCUMULATING", "frozen_winner_rule_id": "R", "cohort": {"independent_trading_days": 4, "remaining_days": 11, "metrics_sealed": True}})
    report = build_report(tmp_path)
    assert report["status"] == "SEALED_WAITING_FOR_A44_FUTURE_BLIND_COMPLETION"
    assert report["blind_metrics"] is None


def test_audits_only_completed_future_blind(tmp_path: Path):
    _write(tmp_path / "runtime/research/a45_future_preblind_qualification/a45_future_preblind_qualification.json", {"status": "FROZEN_PREBLIND_WINNER_READY_FOR_NEW_BLIND", "frozen_preblind_winner_rule_id": "R", "frozen_preblind_winner": {"planned_rr": 2}})
    out = tmp_path / "runtime/research/a44_future_blind_cohort_accumulator"
    _write(out / "a44_future_blind_cohort_accumulator.json", {"status": "COHORT_COMPLETE_METRICS_READY_FOR_A43_AUDIT", "frozen_winner_rule_id": "R", "cohort": {"independent_trading_days": 15, "remaining_days": 0, "metrics_sealed": False}})
    rows = [{"calendar_day_utc": f"2026-10-{day:02d}", "decision_timestamp_utc": f"2026-10-{day:02d}T01:00:00+00:00", "candidate_group_id": str(day), "net_realized_r": 2 if day <= 8 else -1} for day in range(1, 16)]
    (out / "a44_sealed_future_blind_cohort.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    report = build_report(tmp_path)
    assert report["status"] == "PROSPECTIVE_RESEARCH_CERTIFICATION_PASS"
    assert report["audit_pass"] is True
    assert report["demo_order_authorized"] is False
    assert report["live_order_authorized"] is False
    assert report["execution_authority"] == "NONE"
    paths = write_outputs(report, tmp_path)
    assert all(path.exists() for path in paths)
