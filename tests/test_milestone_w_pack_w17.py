from datetime import datetime, timezone
import json
from pathlib import Path

from afip.advisory_integration_certification import AdvisoryIntegrationCertificationRuntime
from afip.milestone_w_closure import (
    MILESTONE_W_BLOCKED,
    MILESTONE_W_COMPLETE,
    MilestoneWClosureRuntime,
)


def test_certified_repository_closes_milestone_w():
    root = Path(__file__).resolve().parents[1]
    certification = AdvisoryIntegrationCertificationRuntime(root).certify()
    result = MilestoneWClosureRuntime(root).close(
        {
            "status": certification.status,
            "certification_id": certification.certification_id,
            "source_digest": certification.source_digest,
        },
        datetime(2026, 7, 30, tzinfo=timezone.utc),
    )
    assert result.status == MILESTONE_W_COMPLETE
    assert result.reason == "milestone_w_closed_successfully"
    assert result.closure_id.startswith("AFIP-W17-")
    assert result.completed_packs[0] == "W2"
    assert result.completed_packs[-1] == "W17"


def test_invalid_certification_blocks_closure():
    root = Path(__file__).resolve().parents[1]
    result = MilestoneWClosureRuntime(root).close(
        {
            "status": "BLOCKED",
            "certification_id": "invalid",
            "source_digest": "invalid",
        }
    )
    assert result.status == MILESTONE_W_BLOCKED


def test_closure_id_is_deterministic_for_same_repository():
    root = Path(__file__).resolve().parents[1]
    certification = AdvisoryIntegrationCertificationRuntime(root).certify()
    payload = {
        "status": certification.status,
        "certification_id": certification.certification_id,
        "source_digest": certification.source_digest,
    }
    runtime = MilestoneWClosureRuntime(root)
    first = runtime.close(payload)
    second = runtime.close(payload)
    assert first.closure_id == second.closure_id


def test_atomic_closure_record_write(tmp_path):
    root = Path(__file__).resolve().parents[1]
    certification = AdvisoryIntegrationCertificationRuntime(root).certify()
    runtime = MilestoneWClosureRuntime(root)
    record = runtime.close(
        {
            "status": certification.status,
            "certification_id": certification.certification_id,
            "source_digest": certification.source_digest,
        }
    )
    output = runtime.write_atomic(record, tmp_path / "closure.json")
    loaded = json.loads(output.read_text(encoding="utf-8"))
    assert loaded["status"] == MILESTONE_W_COMPLETE
    assert loaded["closure_id"] == record.closure_id
    assert not (tmp_path / "closure.json.tmp").exists()


def test_no_execution_authority_and_contract():
    root = Path(__file__).resolve().parents[1]
    certification = AdvisoryIntegrationCertificationRuntime(root).certify()
    result = MilestoneWClosureRuntime(root).close(
        {
            "status": certification.status,
            "certification_id": certification.certification_id,
            "source_digest": certification.source_digest,
        }
    )
    assert result.execution_authority is False
    assert result.order_send_called is False
    assert result.order_modify_called is False
    assert result.order_close_called is False

    contract = json.loads(
        (root / "config" / "milestone_w_closure_contract.json").read_text(encoding="utf-8")
    )
    assert contract["authority"] == "READ_ONLY_CLOSURE_AND_DOCUMENTATION"
    assert contract["fail_closed"] is True
