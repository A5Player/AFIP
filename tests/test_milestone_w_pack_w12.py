from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from afip.advisory_dashboard_read_model import (
    READ_MODEL_BLOCKED,
    READ_MODEL_READY,
    READ_MODEL_STALE,
    READ_MODEL_WAIT,
    AdvisoryDashboardReadModelRuntime,
)


def _snapshot(now):
    return {
        "schema_version": "AFIP_ADVISORY_SNAPSHOT_V1",
        "snapshot_id": "AFIP-W11-ABC",
        "status": "SNAPSHOT_READY",
        "generated_at_utc": now.isoformat(),
        "certification_status": "CERTIFIED",
        "trace_status": "TRACE_COMPLETE",
        "case_id": "case-001",
        "stage_summary": [{"stage": "CONTEXT", "status": "PASS"}],
        "source_digest": "a" * 64,
    }


def test_fresh_snapshot_is_ready():
    now = datetime(2026, 7, 30, tzinfo=timezone.utc)
    result = AdvisoryDashboardReadModelRuntime(300).build(_snapshot(now), now)
    assert result.status == READ_MODEL_READY
    assert result.display_ready is True
    assert result.stage_count == 1


def test_stale_snapshot_is_not_display_ready():
    now = datetime(2026, 7, 30, tzinfo=timezone.utc)
    old = now - timedelta(seconds=301)
    result = AdvisoryDashboardReadModelRuntime(300).build(_snapshot(old), now)
    assert result.status == READ_MODEL_STALE
    assert result.display_ready is False


def test_schema_and_digest_fail_closed():
    now = datetime(2026, 7, 30, tzinfo=timezone.utc)
    bad_schema = _snapshot(now)
    bad_schema["schema_version"] = "UNKNOWN"
    assert AdvisoryDashboardReadModelRuntime().build(bad_schema, now).status == READ_MODEL_BLOCKED

    bad_digest = _snapshot(now)
    bad_digest["source_digest"] = "invalid"
    assert AdvisoryDashboardReadModelRuntime().build(bad_digest, now).status == READ_MODEL_BLOCKED


def test_missing_file_or_incomplete_snapshot_waits(tmp_path):
    runtime = AdvisoryDashboardReadModelRuntime()
    missing = runtime.load(tmp_path / "missing.json")
    assert missing.status == READ_MODEL_WAIT

    incomplete = _snapshot(datetime.now(timezone.utc))
    del incomplete["case_id"]
    assert runtime.build(incomplete).status == READ_MODEL_WAIT


def test_no_execution_or_write_authority_and_contract():
    now = datetime(2026, 7, 30, tzinfo=timezone.utc)
    result = AdvisoryDashboardReadModelRuntime().build(_snapshot(now), now)
    assert result.execution_authority is False
    assert result.order_send_called is False
    assert result.order_modify_called is False
    assert result.order_close_called is False

    root = Path(__file__).resolve().parents[1]
    contract = json.loads(
        (root / "config" / "advisory_dashboard_read_model_contract.json").read_text(encoding="utf-8")
    )
    assert contract["authority"] == "READ_ONLY_CONSUMER"
    assert contract["fail_closed"] is True
