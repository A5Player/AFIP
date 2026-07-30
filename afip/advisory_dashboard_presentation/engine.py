from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

PRESENTATION_READY = "PRESENTATION_READY"
PRESENTATION_WAIT = "PRESENTATION_WAIT"
PRESENTATION_BLOCKED = "PRESENTATION_BLOCKED"

STATUS_MAP = {
    "READ_MODEL_READY": {
        "presentation_status": PRESENTATION_READY,
        "severity": "SUCCESS",
        "label_en": "Advisory Ready",
        "label_th": "Advisory พร้อมใช้งาน",
        "icon": "CHECK",
    },
    "READ_MODEL_STALE": {
        "presentation_status": PRESENTATION_WAIT,
        "severity": "WARNING",
        "label_en": "Advisory Data Stale",
        "label_th": "ข้อมูล Advisory เก่า",
        "icon": "CLOCK",
    },
    "READ_MODEL_WAIT": {
        "presentation_status": PRESENTATION_WAIT,
        "severity": "NEUTRAL",
        "label_en": "Waiting for Advisory Data",
        "label_th": "รอข้อมูล Advisory",
        "icon": "WAIT",
    },
    "READ_MODEL_BLOCKED": {
        "presentation_status": PRESENTATION_BLOCKED,
        "severity": "DANGER",
        "label_en": "Advisory Blocked",
        "label_th": "Advisory ถูกระงับ",
        "icon": "BLOCK",
    },
}

STAGE_LABELS = {
    "CONTEXT": ("Context Matching", "การจับคู่บริบท"),
    "STRATEGY": ("Strategy Intelligence", "ปัญญากลยุทธ์"),
    "PLAN": ("Trading Plan", "แผนการเทรด"),
    "OQS": ("Opportunity Quality", "คุณภาพโอกาส"),
    "ADAPTIVE_SL": ("Adaptive SL", "จุดตัดขาดทุนแบบปรับตัว"),
    "HOLDING": ("Holding Intelligence", "ปัญญาการถือสถานะ"),
    "EXIT": ("Exit Intelligence", "ปัญญาการออกจากสถานะ"),
}


@dataclass(frozen=True)
class DashboardStageItem:
    stage: str
    label_en: str
    label_th: str
    status: str
    reason: str
    sequence: int


@dataclass(frozen=True)
class AdvisoryDashboardPresentation:
    status: str
    severity: str
    label_en: str
    label_th: str
    icon: str
    reason: str
    snapshot_id: str
    case_id: str
    freshness_text_en: str
    freshness_text_th: str
    age_seconds: int
    display_ready: bool
    stages: Sequence[DashboardStageItem]
    execution_authority: bool = False
    order_send_called: bool = False
    order_modify_called: bool = False
    order_close_called: bool = False


class AdvisoryDashboardPresentationRuntime:
    """Transforms W12 read models into stable dashboard presentation data."""

    @staticmethod
    def _freshness(age_seconds: int, status: str) -> tuple[str, str]:
        age = max(0, int(age_seconds))
        if status == "READ_MODEL_STALE":
            return (
                f"Stale by {age} seconds",
                f"ข้อมูลเก่า {age} วินาที",
            )
        if age < 60:
            return (
                f"Updated {age} seconds ago",
                f"อัปเดตเมื่อ {age} วินาทีที่แล้ว",
            )
        minutes = age // 60
        return (
            f"Updated {minutes} minutes ago",
            f"อัปเดตเมื่อ {minutes} นาทีที่แล้ว",
        )

    @staticmethod
    def _stage_items(raw_stages: Sequence[Mapping[str, Any]]) -> tuple[DashboardStageItem, ...]:
        items: list[DashboardStageItem] = []
        for index, raw in enumerate(raw_stages, start=1):
            stage = str(raw.get("stage", "UNKNOWN"))
            labels = STAGE_LABELS.get(stage, (stage.title(), stage))
            items.append(
                DashboardStageItem(
                    stage=stage,
                    label_en=labels[0],
                    label_th=labels[1],
                    status=str(raw.get("status", "UNKNOWN")),
                    reason=str(raw.get("reason", "")),
                    sequence=index,
                )
            )
        return tuple(items)

    def build(self, read_model: Mapping[str, Any]) -> AdvisoryDashboardPresentation:
        source_status = str(read_model.get("status", "READ_MODEL_WAIT"))
        mapped = STATUS_MAP.get(source_status, STATUS_MAP["READ_MODEL_BLOCKED"])
        age_seconds = max(0, int(read_model.get("age_seconds", 0) or 0))
        freshness_en, freshness_th = self._freshness(age_seconds, source_status)
        stages = self._stage_items(tuple(read_model.get("stage_summary", ()) or ()))

        return AdvisoryDashboardPresentation(
            status=mapped["presentation_status"],
            severity=mapped["severity"],
            label_en=mapped["label_en"],
            label_th=mapped["label_th"],
            icon=mapped["icon"],
            reason=str(read_model.get("reason", "")),
            snapshot_id=str(read_model.get("snapshot_id", "")),
            case_id=str(read_model.get("case_id", "")),
            freshness_text_en=freshness_en,
            freshness_text_th=freshness_th,
            age_seconds=age_seconds,
            display_ready=bool(read_model.get("display_ready", False))
            and mapped["presentation_status"] == PRESENTATION_READY,
            stages=stages,
        )
