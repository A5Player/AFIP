import json
from pathlib import Path

from afip.advisory_dashboard_presentation import (
    PRESENTATION_BLOCKED,
    PRESENTATION_READY,
    PRESENTATION_WAIT,
    AdvisoryDashboardPresentationRuntime,
)


def _model(status="READ_MODEL_READY", age=12, display_ready=True):
    return {
        "status": status,
        "reason": "dashboard_read_model_ready",
        "snapshot_id": "AFIP-W11-ABC",
        "case_id": "case-001",
        "age_seconds": age,
        "display_ready": display_ready,
        "stage_summary": [
            {"stage": "CONTEXT", "status": "PASS", "reason": "context_validated"},
            {"stage": "STRATEGY", "status": "PASS", "reason": "strategy_validated"},
        ],
    }


def test_ready_mapping_is_bilingual_and_display_ready():
    result = AdvisoryDashboardPresentationRuntime().build(_model())
    assert result.status == PRESENTATION_READY
    assert result.severity == "SUCCESS"
    assert result.label_en == "Advisory Ready"
    assert result.label_th == "Advisory พร้อมใช้งาน"
    assert result.display_ready is True


def test_stale_and_wait_mapping_are_not_display_ready():
    runtime = AdvisoryDashboardPresentationRuntime()
    stale = runtime.build(_model("READ_MODEL_STALE", age=401, display_ready=False))
    waiting = runtime.build(_model("READ_MODEL_WAIT", display_ready=False))
    assert stale.status == PRESENTATION_WAIT
    assert stale.severity == "WARNING"
    assert waiting.status == PRESENTATION_WAIT
    assert waiting.severity == "NEUTRAL"
    assert stale.display_ready is False
    assert waiting.display_ready is False


def test_blocked_mapping_is_fail_closed():
    result = AdvisoryDashboardPresentationRuntime().build(
        _model("READ_MODEL_BLOCKED", display_ready=False)
    )
    assert result.status == PRESENTATION_BLOCKED
    assert result.severity == "DANGER"
    assert result.display_ready is False


def test_stage_order_and_labels_are_stable():
    result = AdvisoryDashboardPresentationRuntime().build(_model())
    assert [item.sequence for item in result.stages] == [1, 2]
    assert result.stages[0].label_en == "Context Matching"
    assert result.stages[0].label_th == "การจับคู่บริบท"
    assert result.stages[1].stage == "STRATEGY"


def test_no_execution_or_html_mutation_authority():
    result = AdvisoryDashboardPresentationRuntime().build(_model())
    assert result.execution_authority is False
    assert result.order_send_called is False
    assert result.order_modify_called is False
    assert result.order_close_called is False

    root = Path(__file__).resolve().parents[1]
    contract = json.loads(
        (root / "config" / "advisory_dashboard_presentation_contract.json").read_text(encoding="utf-8")
    )
    assert contract["authority"] == "READ_ONLY_PRESENTATION"
    assert contract["fail_closed"] is True
    assert "HTML_MUTATION" in contract["forbidden_authorities"]
