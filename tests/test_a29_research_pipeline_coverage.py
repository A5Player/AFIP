import json
from pathlib import Path

from afip.dashboard_ui.split_runtime import SplitDashboardRenderer
from afip.historical_replay_research import AppendOnlyResearchDataset
from tools.afip_a29_research_pipeline_coverage import build_report


def test_audit_covers_every_registered_dataset_without_authority(tmp_path: Path):
    (tmp_path / "afip/historical_replay_research").mkdir(parents=True)
    (tmp_path / "afip/historical_replay_research/runtime.py").write_text("registry", encoding="utf-8")
    (tmp_path / "afip/dashboard_ui").mkdir(parents=True)
    (tmp_path / "afip/dashboard_ui/split_runtime.py").write_text("dashboard", encoding="utf-8")
    report = build_report(tmp_path)
    assert report["registered_datasets"] == len(AppendOnlyResearchDataset.DATASET_NAMES)
    assert report["execution_authority"] == "NONE" and report["orders_sent"] is False
    assert report["automatic_promotion_allowed"] is False


def test_audit_detects_static_producer_and_persisted_outcome(tmp_path: Path):
    (tmp_path / "afip/historical_replay_research").mkdir(parents=True)
    (tmp_path / "afip/historical_replay_research/runtime.py").write_text("registry", encoding="utf-8")
    (tmp_path / "afip/dashboard_ui").mkdir(parents=True)
    (tmp_path / "afip/dashboard_ui/split_runtime.py").write_text("a24_tp_volume_outcomes.jsonl", encoding="utf-8")
    (tmp_path / "afip/producer.py").write_text('dataset.append("a24_tp_volume_outcomes", value)', encoding="utf-8")
    research = tmp_path / "runtime/research"; research.mkdir(parents=True)
    envelope = {"chain_checksum": "X", "record": {"decision_id": "D1", "net_realized_r": 0.2}}
    (research / "a24_tp_volume_outcomes.jsonl").write_text(json.dumps(envelope) + "\n", encoding="utf-8")
    report = build_report(tmp_path)
    row = next(item for item in report["datasets"] if item["dataset"] == "a24_tp_volume_outcomes")
    assert row["state"] == "EVIDENCE_RECORDED" and row["producer_connected"] is True
    assert row["record_count"] == 1 and row["outcome_record_count"] == 1
    assert row["specialized_dashboard_connected"] is True


def test_dashboard_renders_a29_category_and_dataset_coverage(tmp_path: Path):
    report = {
        "registered_datasets": 2, "datasets_with_static_producer": 1,
        "datasets_with_evidence": 1, "datasets_with_outcomes": 1, "datasets_with_rankings": 0,
        "categories": [{"category": "EXIT, HOLDING & TP", "datasets": 2, "with_producer": 1,
                        "with_evidence": 1, "records": 4, "outcome_records": 2,
                        "ranked_records": 0, "specialized_dashboard": 1}],
        "datasets": [{"category": "EXIT, HOLDING & TP", "dataset": "a24_tp_volume_outcomes",
                      "state": "EVIDENCE_RECORDED", "record_count": 4, "outcome_record_count": 2,
                      "ranked_record_count": 0, "producer_connected": True,
                      "specialized_dashboard_connected": True}],
    }
    root = tmp_path / "runtime/research"; root.mkdir(parents=True)
    (root / "a29_research_pipeline_coverage.json").write_text(json.dumps(report), encoding="utf-8")
    html = SplitDashboardRenderer().render_research_html({}, tmp_path)
    assert "Research Pipeline Coverage" in html and "a24_tp_volume_outcomes" in html
    assert "EVIDENCE_RECORDED" in html and "execution authority: NONE" in html


def test_a29_tool_has_no_execution_calls():
    source = Path("tools/afip_a29_research_pipeline_coverage.py").read_text(encoding="utf-8")
    assert "MetaTrader5" not in source and ".order_send(" not in source and ".order_check(" not in source
