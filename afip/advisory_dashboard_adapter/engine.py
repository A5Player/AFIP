from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

ADAPTER_READY = "ADAPTER_READY"
ADAPTER_WAIT = "ADAPTER_WAIT"
ADAPTER_BLOCKED = "ADAPTER_BLOCKED"


@dataclass(frozen=True)
class DashboardPanelRow:
    key: str
    label_en: str
    label_th: str
    value: str
    severity: str
    sequence: int


@dataclass(frozen=True)
class DashboardAdvisoryPanel:
    adapter_status: str
    panel_id: str
    title_en: str
    title_th: str
    overall_label_en: str
    overall_label_th: str
    overall_severity: str
    overall_icon: str
    reason: str
    freshness_en: str
    freshness_th: str
    snapshot_id: str
    case_id: str
    rows: Sequence[DashboardPanelRow]
    display_ready: bool
    execution_authority: bool = False
    order_send_called: bool = False
    order_modify_called: bool = False
    order_close_called: bool = False


class AdvisoryDashboardPanelAdapter:
    """Converts W13 presentation output into a stable dashboard panel contract."""

    PANEL_ID = "afip_advisory_intelligence"

    @staticmethod
    def _adapter_status(presentation_status: str) -> str:
        if presentation_status == "PRESENTATION_READY":
            return ADAPTER_READY
        if presentation_status == "PRESENTATION_WAIT":
            return ADAPTER_WAIT
        return ADAPTER_BLOCKED

    @staticmethod
    def _row_from_stage(stage: Mapping[str, Any], sequence: int) -> DashboardPanelRow:
        status = str(stage.get("status", "UNKNOWN"))
        severity = "SUCCESS" if status in {"PASS", "READY", "HOLD", "MONITOR"} else "WARNING"
        if status in {"BLOCKED", "FAIL", "ERROR"}:
            severity = "DANGER"

        reason = str(stage.get("reason", "")).strip()
        value = status if not reason else f"{status} — {reason}"

        return DashboardPanelRow(
            key=str(stage.get("stage", f"STAGE_{sequence}")),
            label_en=str(stage.get("label_en", stage.get("stage", "Stage"))),
            label_th=str(stage.get("label_th", stage.get("stage", "ขั้นตอน"))),
            value=value,
            severity=severity,
            sequence=sequence,
        )

    def build(self, presentation: Mapping[str, Any]) -> DashboardAdvisoryPanel:
        status = str(presentation.get("status", "PRESENTATION_BLOCKED"))
        adapter_status = self._adapter_status(status)
        stages = tuple(presentation.get("stages", ()) or ())
        rows = tuple(
            self._row_from_stage(stage, index)
            for index, stage in enumerate(stages, start=1)
        )

        display_ready = (
            adapter_status == ADAPTER_READY
            and bool(presentation.get("display_ready", False))
        )

        return DashboardAdvisoryPanel(
            adapter_status=adapter_status,
            panel_id=self.PANEL_ID,
            title_en="AFIP Advisory Intelligence",
            title_th="ปัญญา Advisory ของ AFIP",
            overall_label_en=str(presentation.get("label_en", "Advisory Blocked")),
            overall_label_th=str(presentation.get("label_th", "Advisory ถูกระงับ")),
            overall_severity=str(presentation.get("severity", "DANGER")),
            overall_icon=str(presentation.get("icon", "BLOCK")),
            reason=str(presentation.get("reason", "")),
            freshness_en=str(presentation.get("freshness_text_en", "")),
            freshness_th=str(presentation.get("freshness_text_th", "")),
            snapshot_id=str(presentation.get("snapshot_id", "")),
            case_id=str(presentation.get("case_id", "")),
            rows=rows,
            display_ready=display_ready,
        )

    @staticmethod
    def to_dict(panel: DashboardAdvisoryPanel) -> dict[str, Any]:
        return asdict(panel)
