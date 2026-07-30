from datetime import datetime, timezone
import json
from pathlib import Path

from afip.advisory_dashboard_runtime import (
    RUNTIME_BLOCKED,
    RUNTIME_READY,
    RUNTIME_WAIT,
    AdvisoryDashboardRuntime,
)
from afip.advisory_dashboard_runtime.bridge import build_advisory_dashboard_context


def _snapshot(now, status="SNAPSHOT_READY"):
    return {
        "schema_version": "AFIP_ADVISORY_SNAPSHOT_V1",
        "snapshot_id": "AFIP-W11-ABC",
        "status": status,
        "reason": "advisory_snapshot_ready",
        "generated_at_utc": now.isoformat(),
        "certification_status": "CERTIFIED",
        "certification_snapshot_id": "AFIP-W10-XYZ",
        "trace_status": "TRACE_COMPLETE",
        "trace_id": "AFIP-W9-TRACE",
        "case_id": "case-001",
        "stage_summary": [
            {"stage": "CONTEXT", "status": "PASS", "reason": "context_validated"},
            {"stage": "STRATEGY", "status": "PASS", "reason": "strategy_validated"},
            {"stage": "PLAN", "status": "PASS", "reason": "plan_selected"},
            {"stage": "OQS", "status": "PASS", "reason": "opportunity_quality_ready"},
            {"stage": "ADAPTIVE_SL", "status": "PASS", "reason": "adaptive_sl_ready"},
            {"stage": "HOLDING", "status": "MONITOR", "reason": "holding_valid"},
            {"stage": "EXIT", "status": "MONITOR", "reason": "exit_not_required"},
        ],
        "freshness_seconds": 0,
        "source_digest": "a" * 64,
    }


def test_end_to_end_ready_pipeline(tmp_path):
    now = datetime(2026, 7, 30, tzinfo=timezone.utc)
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(_snapshot(now)), encoding="utf-8")

    result = AdvisoryDashboardRuntime().build_from_snapshot(path, now_utc=now)
    assert result.status == RUNTIME_READY
    assert result.display_ready is True
    assert result.panel["panel_id"] == "afip_advisory_intelligence"
    assert len(result.panel["rows"]) == 7


def test_missing_snapshot_waits(tmp_path):
    result = AdvisoryDashboardRuntime().build_from_snapshot(tmp_path / "missing.json")
    assert result.status == RUNTIME_WAIT
    assert result.display_ready is False


def test_blocked_snapshot_blocks_dashboard(tmp_path):
    now = datetime(2026, 7, 30, tzinfo=timezone.utc)
    data = _snapshot(now, status="SNAPSHOT_BLOCKED")
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    result = AdvisoryDashboardRuntime().build_from_snapshot(path, now_utc=now)
    assert result.status == RUNTIME_BLOCKED
    assert result.display_ready is False


def test_dashboard_context_integration_preserves_existing_keys(tmp_path):
    now = datetime(2026, 7, 30, tzinfo=timezone.utc)
    root = tmp_path
    source = root / "runtime/advisory_snapshot/advisory_runtime_snapshot.json"
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps(_snapshot(now)), encoding="utf-8")

    context = build_advisory_dashboard_context(
        root,
        {"existing_key": "preserved"},
        now_utc=now,
    )
    assert context["existing_key"] == "preserved"
    assert context["advisory_runtime_status"] == RUNTIME_READY
    assert context["advisory_intelligence"]["panel_id"] == "afip_advisory_intelligence"


def test_no_execution_authority_and_contract():
    root = Path(__file__).resolve().parents[1]
    contract = json.loads(
        (root / "config" / "advisory_dashboard_runtime_contract.json").read_text(encoding="utf-8")
    )
    assert contract["authority"] == "READ_ONLY_DASHBOARD_RUNTIME"
    assert contract["fail_closed"] is True
    assert "EXECUTION_STATE_WRITE" in contract["forbidden_authorities"]
