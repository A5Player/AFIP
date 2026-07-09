"""Runtime event history builder for dashboard explainability."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .runtime_models import RuntimeEvent


_EVENT_MESSAGES: dict[str, tuple[str, str]] = {
    "runtime_started": ("ระบบเริ่มทำงานบน VPS", "Runtime started on VPS"),
    "runtime_paused": ("ระบบพักการประมวลผลเพื่อความปลอดภัย", "Runtime paused for safety"),
    "runtime_resumed": ("ระบบกลับมาประมวลผลหลังตรวจสอบครบ", "Runtime resumed after validation"),
    "internet_lost": ("อินเทอร์เน็ตขาดการเชื่อมต่อ", "Internet connection lost"),
    "internet_recovered": ("อินเทอร์เน็ตกลับมาเชื่อมต่อ", "Internet connection recovered"),
    "mt5_reconnected": ("MT5 กลับมาเชื่อมต่อ", "MT5 reconnected"),
    "broker_ready": ("โบรกเกอร์พร้อมใช้งาน", "Broker ready"),
    "profile_loaded": ("โหลดโปรไฟล์สำเร็จ", "Profile loaded"),
    "historical_download_started": ("เริ่มดาวน์โหลดข้อมูลย้อนหลัง", "Historical download started"),
    "walk_forward_started": ("เริ่ม Walk Forward", "Walk Forward started"),
    "watchdog_review": ("ระบบเฝ้าระวังขอให้ตรวจสอบ", "Watchdog requests review"),
}


def _normalize_event_name(value: Any) -> str:
    text = str(value or "runtime_started").strip().lower().replace(" ", "_")
    return text or "runtime_started"


class RuntimeEventLogger:
    """Create deterministic runtime event history without side effects."""

    def build(self, events: Iterable[Mapping[str, Any]] | None = None) -> tuple[RuntimeEvent, ...]:
        raw_events = list(events or ({"event_name": "runtime_started", "status": "INFO", "reason": "runtime_service_started", "action": "observe_runtime"},))
        built: list[RuntimeEvent] = []
        for index, event in enumerate(raw_events, start=1):
            name = _normalize_event_name(event.get("event_name"))
            th, en = _EVENT_MESSAGES.get(name, ("บันทึกเหตุการณ์ระบบ", "Runtime event recorded"))
            built.append(
                RuntimeEvent(
                    sequence=index,
                    event_name=name,
                    status=str(event.get("status", "INFO")).strip().upper() or "INFO",
                    reason=str(event.get("reason", name)).strip() or name,
                    action=str(event.get("action", "observe_runtime")).strip() or "observe_runtime",
                    dashboard_message_th=th,
                    dashboard_message_en=en,
                )
            )
        return tuple(built)
