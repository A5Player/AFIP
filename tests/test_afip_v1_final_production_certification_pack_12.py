from __future__ import annotations

import json
from pathlib import Path

from afip.production_certification.runtime import FINAL_CERTIFICATION_DOMAINS, FinalV1ProductionCertification


def _sources(root: Path) -> None:
    for paths in FINAL_CERTIFICATION_DOMAINS.values():
        for relative in paths:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("# evidence\n", encoding="utf-8")


def test_full_pass_grants_production_certification(tmp_path: Path) -> None:
    _sources(tmp_path)
    report = FinalV1ProductionCertification(tmp_path).certify(
        regression_status="PASS", regression_scope="FULL", regression_count=3000,
        runtime_truth={"status": "PASS", "conflict_count": 0, "missing_authority_count": 0},
    )
    assert report["status"] == "PRODUCTION_CERTIFIED"
    assert report["production_certified"] is True
    assert report["readiness_score"] == 100.0


def test_focused_pass_is_conditional_not_overclaimed(tmp_path: Path) -> None:
    _sources(tmp_path)
    report = FinalV1ProductionCertification(tmp_path).certify(
        regression_status="PASS", regression_scope="FOCUSED",
        runtime_truth={"status": "PASS", "conflict_count": 0, "missing_authority_count": 0},
    )
    assert report["status"] == "CONDITIONALLY_CERTIFIED"
    assert report["production_certified"] is False
    assert "full_repository_regression_not_yet_recorded" in report["conditions"]


def test_runtime_truth_conflict_blocks_certification(tmp_path: Path) -> None:
    _sources(tmp_path)
    report = FinalV1ProductionCertification(tmp_path).certify(
        regression_status="PASS", regression_scope="FULL",
        runtime_truth={"status": "CONFLICT", "conflict_count": 1, "missing_authority_count": 0},
    )
    assert report["status"] == "NOT_CERTIFIED"
    assert "runtime_truth_not_clean" in report["blockers"]


def test_missing_source_blocks_certification(tmp_path: Path) -> None:
    report = FinalV1ProductionCertification(tmp_path).certify(
        regression_status="PASS", regression_scope="FULL",
        runtime_truth={"status": "PASS", "conflict_count": 0, "missing_authority_count": 0},
    )
    assert report["status"] == "NOT_CERTIFIED"
    assert "required_source_evidence_missing" in report["blockers"]


def test_reports_are_written_and_passive(tmp_path: Path) -> None:
    _sources(tmp_path)
    report = FinalV1ProductionCertification(tmp_path).certify(
        regression_status="PASS", regression_scope="FOCUSED",
        runtime_truth={"status": "PASS", "conflict_count": 0, "missing_authority_count": 0},
    )
    json_path = tmp_path / "runtime/certification/AFIP_V1_PRODUCTION_CERTIFICATION_REPORT.json"
    html_path = tmp_path / "runtime/certification/AFIP_V1_PRODUCTION_READINESS_REPORT.html"
    assert json_path.is_file() and html_path.is_file()
    saved = json.loads(json_path.read_text(encoding="utf-8"))
    assert saved["safety"]["order_send_called"] is False
    assert saved["safety"]["mt5_initialize_called"] is False
    assert "AFIP V1 Production Readiness Report" in html_path.read_text(encoding="utf-8")
