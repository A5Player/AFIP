"""Read-only dashboard live runtime for Production Bring-up Pack 8."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class DashboardLiveRuntimeReport:
    status: str
    reason: str
    broker: str
    symbol: str
    runtime_state: str
    data_state: str
    refresh_interval_seconds: int
    last_refresh_utc: str
    next_refresh_utc: str
    snapshot_sequence: int
    stale_after_seconds: int
    data_age_seconds: int
    data_fresh: bool
    dependency_ready: bool
    dashboard_live_ready: bool
    waiting_reason_en: str
    waiting_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    live_execution_enabled: bool = False
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class DashboardLiveRuntime:
    """Evaluate observable dashboard refresh readiness without trading."""

    def evaluate_one(self, record: Mapping[str, Any]) -> DashboardLiveRuntimeReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        refresh = max(1, int(record.get("dashboard_refresh_interval_seconds", 5) or 5))
        stale_after = max(refresh, int(record.get("dashboard_stale_after_seconds", 30) or 30))
        data_age = max(0, int(record.get("dashboard_data_age_seconds", 0) or 0))
        sequence = max(0, int(record.get("dashboard_snapshot_sequence", 1) or 0))
        last_refresh = str(record.get("dashboard_last_refresh_utc", "not_recorded")).strip() or "not_recorded"
        next_refresh = str(record.get("dashboard_next_refresh_utc", "scheduled_by_launcher")).strip() or "scheduled_by_launcher"
        dependencies = tuple(
            str(record.get(key, "READY")).strip().upper() or "READY"
            for key in (
                "dashboard_runtime_status",
                "mt5_status",
                "internet_status",
                "market_calendar_status",
                "historical_data_status",
            )
        )
        dependency_ready = all(value in {"READY", "REVIEW", "WAITING"} for value in dependencies)
        data_fresh = data_age <= stale_after
        policy_ok = broker == "XM" and symbol == "GOLD#" and not bool(record.get("live_execution_enabled", False))
        launcher_enabled = bool(record.get("dashboard_live_runtime_enabled", True))

        if not policy_ok:
            status, reason = "BLOCKED", "dashboard_live_runtime_blocked_by_version1_or_live_policy"
            runtime_state, data_state = "BLOCKED", "POLICY_BLOCKED"
            waiting_en = "XM, GOLD#, and disabled live execution are required."
            waiting_th = "ต้องใช้ XM, GOLD# และปิดการส่งคำสั่งจริง"
            action_en = "Restore the Version 1 dashboard policy."
            action_th = "คืนค่านโยบาย Dashboard สำหรับ Version 1"
        elif not launcher_enabled:
            status, reason = "WAITING", "dashboard_live_runtime_launcher_disabled"
            runtime_state, data_state = "STOPPED", "NOT_REFRESHING"
            waiting_en = "The dashboard live refresh service is disabled."
            waiting_th = "บริการรีเฟรช Dashboard แบบสดถูกปิดอยู่"
            action_en = "Enable the dashboard live runtime service."
            action_th = "เปิดบริการ Dashboard Live Runtime"
        elif not dependency_ready:
            status, reason = "WAITING", "dashboard_live_runtime_dependency_not_ready"
            runtime_state, data_state = "WAITING", "DEPENDENCY_REVIEW"
            waiting_en = "One or more read-only dashboard dependencies are not ready."
            waiting_th = "ส่วนประกอบ Dashboard แบบอ่านอย่างเดียวอย่างน้อยหนึ่งรายการยังไม่พร้อม"
            action_en = "Review dependency status before the next refresh."
            action_th = "ตรวจสอบสถานะส่วนประกอบก่อนรอบรีเฟรชถัดไป"
        elif not data_fresh:
            status, reason = "REVIEW", "dashboard_live_runtime_data_stale"
            runtime_state, data_state = "RUNNING", "STALE"
            waiting_en = "Dashboard data is older than the configured freshness limit."
            waiting_th = "ข้อมูล Dashboard เก่ากว่าขีดจำกัดความสดที่กำหนด"
            action_en = "Refresh the dashboard snapshot and verify connectivity."
            action_th = "รีเฟรช Snapshot และตรวจสอบการเชื่อมต่อ"
        else:
            status, reason = "READY", "dashboard_live_runtime_refresh_ready"
            runtime_state, data_state = "RUNNING", "FRESH"
            waiting_en = "No blocking condition. Dashboard data is fresh."
            waiting_th = "ไม่มีเงื่อนไขบล็อก ข้อมูล Dashboard ยังสด"
            action_en = "Continue the scheduled read-only refresh cycle."
            action_th = "ดำเนินรอบรีเฟรชแบบอ่านอย่างเดียวตามกำหนดต่อไป"

        return DashboardLiveRuntimeReport(
            status=status,
            reason=reason,
            broker=broker,
            symbol=symbol,
            runtime_state=runtime_state,
            data_state=data_state,
            refresh_interval_seconds=refresh,
            last_refresh_utc=last_refresh,
            next_refresh_utc=next_refresh,
            snapshot_sequence=sequence,
            stale_after_seconds=stale_after,
            data_age_seconds=data_age,
            data_fresh=data_fresh,
            dependency_ready=dependency_ready,
            dashboard_live_ready=status in {"READY", "REVIEW"},
            waiting_reason_en=waiting_en,
            waiting_reason_th=waiting_th,
            expected_next_action_en=action_en,
            expected_next_action_th=action_th,
        )

    def explain_one(self, record: Mapping[str, Any]) -> DashboardLiveRuntimeReport:
        return self.evaluate_one(record)
