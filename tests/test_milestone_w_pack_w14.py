import json
from pathlib import Path

from afip.advisory_dashboard_adapter import (
    ADAPTER_BLOCKED,
    ADAPTER_READY,
    ADAPTER_WAIT,
    AdvisoryDashboardPanelAdapter,
)


def _presentation(status="PRESENTATION_READY", display_ready=True):
    return {
        "status": status,
        "severity": "SUCCESS" if status == "PRESENTATION_READY" else "WARNING",
        "label_en": "Advisory Ready",
        "label_th": "Advisory พร้อมใช้งาน",
        "icon": "CHECK",
        "reason": "dashboard_read_model_ready",
        "snapshot_id": "AFIP-W11-ABC",
        "case_id": "case-001",
        "freshness_text_en": "Updated 3 seconds ago",
        "freshness_text_th": "อัปเดตเมื่อ 3 วินาทีที่แล้ว",
        "display_ready": display_ready,
        "stages": [
            {
                "stage": "CONTEXT",
                "label_en": "Context Matching",
                "label_th": "การจับคู่บริบท",
                "status": "PASS",
                "reason": "context_validated",
            },
            {
                "stage": "EXIT",
                "label_en": "Exit Intelligence",
                "label_th": "ปัญญาการออกจากสถานะ",
                "status": "MONITOR",
                "reason": "exit_pressure_not_dominant",
            },
        ],
    }


def test_ready_presentation_builds_ready_panel():
    panel = AdvisoryDashboardPanelAdapter().build(_presentation())
    assert panel.adapter_status == ADAPTER_READY
    assert panel.display_ready is True
    assert panel.panel_id == "afip_advisory_intelligence"
    assert len(panel.rows) == 2


def test_wait_and_blocked_are_fail_closed():
    adapter = AdvisoryDashboardPanelAdapter()
    waiting = adapter.build(_presentation("PRESENTATION_WAIT", False))
    blocked = adapter.build(_presentation("PRESENTATION_BLOCKED", False))
    assert waiting.adapter_status == ADAPTER_WAIT
    assert blocked.adapter_status == ADAPTER_BLOCKED
    assert waiting.display_ready is False
    assert blocked.display_ready is False


def test_stage_rows_preserve_order_and_bilingual_labels():
    panel = AdvisoryDashboardPanelAdapter().build(_presentation())
    assert [row.sequence for row in panel.rows] == [1, 2]
    assert panel.rows[0].label_en == "Context Matching"
    assert panel.rows[0].label_th == "การจับคู่บริบท"
    assert panel.rows[1].key == "EXIT"


def test_adapter_serialization_is_stable():
    adapter = AdvisoryDashboardPanelAdapter()
    panel = adapter.build(_presentation())
    data = adapter.to_dict(panel)
    assert data["panel_id"] == "afip_advisory_intelligence"
    assert data["rows"][0]["key"] == "CONTEXT"
    assert data["rows"][1]["sequence"] == 2


def test_no_execution_or_html_mutation_authority():
    panel = AdvisoryDashboardPanelAdapter().build(_presentation())
    assert panel.execution_authority is False
    assert panel.order_send_called is False
    assert panel.order_modify_called is False
    assert panel.order_close_called is False

    root = Path(__file__).resolve().parents[1]
    contract = json.loads(
        (root / "config" / "advisory_dashboard_adapter_contract.json").read_text(encoding="utf-8")
    )
    assert contract["authority"] == "READ_ONLY_ADAPTER"
    assert contract["fail_closed"] is True
    assert "HTML_MUTATION" in contract["forbidden_authorities"]
