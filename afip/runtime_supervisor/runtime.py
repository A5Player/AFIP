"""Read-only runtime supervision for Production Bring-up Pack 9."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class RuntimeSupervisorReport:
    status: str
    reason: str
    broker: str
    symbol: str
    runtime_health: str
    healthy_modules: int
    warning_modules: int
    critical_modules: int
    supervised_modules: tuple[str, ...]
    warning_modules_list: tuple[str, ...]
    critical_modules_list: tuple[str, ...]
    recovery_action_en: str
    recovery_action_th: str
    expected_next_check_en: str
    expected_next_check_th: str
    supervisor_confidence: float
    live_execution_enabled: bool = False
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class RuntimeSupervisorRuntime:
    """Aggregate health of existing read-only production dependencies."""

    _MODULE_KEYS = (
        ("dashboard", "dashboard_runtime_status"),
        ("mt5", "mt5_status"),
        ("internet", "internet_status"),
        ("market_calendar", "market_calendar_status"),
        ("historical_data", "historical_data_status"),
        ("dashboard_live", "dashboard_live_runtime_status"),
        ("intelligence", "intelligence_health"),
    )
    _HEALTHY = {"READY", "OK", "RUNNING", "CONNECTED"}
    _WARNING = {"WAITING", "REVIEW", "CAUTION", "RECOVERING", "STALE"}

    def evaluate_one(self, record: Mapping[str, Any]) -> RuntimeSupervisorReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        live_requested = bool(record.get("live_execution_enabled", False))
        module_states = {
            name: str(record.get(key, "READY")).strip().upper() or "READY"
            for name, key in self._MODULE_KEYS
        }
        warnings = tuple(name for name, state in module_states.items() if state in self._WARNING)
        critical = tuple(
            name for name, state in module_states.items()
            if state not in self._HEALTHY and state not in self._WARNING
        )
        healthy = sum(1 for state in module_states.values() if state in self._HEALTHY)
        policy_ok = broker == "XM" and symbol == "GOLD#" and not live_requested

        if not policy_ok:
            status, reason, health = "BLOCKED", "runtime_supervisor_blocked_by_version1_or_live_policy", "POLICY_BLOCKED"
            action_en = "Restore XM, GOLD#, and disabled live execution before supervision continues."
            action_th = "คืนค่า XM, GOLD# และปิดการส่งคำสั่งจริงก่อนดำเนินการตรวจสุขภาพต่อ"
            next_en = "Recheck immediately after the policy is restored."
            next_th = "ตรวจซ้ำทันทีหลังคืนนโยบายแล้ว"
        elif critical:
            status, reason, health = "BLOCKED", "runtime_supervisor_critical_dependency_detected", "CRITICAL"
            action_en = "Keep execution locked and repair critical runtime dependencies."
            action_th = "คงการล็อก Execution และแก้ไขส่วนประกอบ Runtime ที่อยู่ในสถานะวิกฤต"
            next_en = "Recheck after each critical dependency is restored."
            next_th = "ตรวจซ้ำหลังแก้ไขส่วนประกอบวิกฤตแต่ละรายการ"
        elif warnings:
            status, reason, health = "REVIEW", "runtime_supervisor_warning_dependency_detected", "WARNING"
            action_en = "Review warning modules while keeping the dashboard in read-only mode."
            action_th = "ตรวจสอบโมดูลที่มีคำเตือนโดยคง Dashboard เป็นโหมดอ่านอย่างเดียว"
            next_en = "Review again at the next dashboard refresh."
            next_th = "ตรวจอีกครั้งในรอบรีเฟรช Dashboard ถัดไป"
        else:
            status, reason, health = "READY", "runtime_supervisor_all_dependencies_healthy", "HEALTHY"
            action_en = "Continue supervised paper and demo runtime operation."
            action_th = "ดำเนิน Runtime แบบ Paper และ Demo ภายใต้การกำกับต่อไป"
            next_en = "Run the next scheduled health review."
            next_th = "ตรวจสุขภาพตามรอบเวลาถัดไป"

        confidence = round((healthy / len(module_states)) * 100.0, 2)
        if not policy_ok:
            confidence = 0.0
        return RuntimeSupervisorReport(
            status=status,
            reason=reason,
            broker=broker,
            symbol=symbol,
            runtime_health=health,
            healthy_modules=healthy,
            warning_modules=len(warnings),
            critical_modules=len(critical),
            supervised_modules=tuple(module_states),
            warning_modules_list=warnings,
            critical_modules_list=critical,
            recovery_action_en=action_en,
            recovery_action_th=action_th,
            expected_next_check_en=next_en,
            expected_next_check_th=next_th,
            supervisor_confidence=confidence,
        )

    def explain_one(self, record: Mapping[str, Any]) -> RuntimeSupervisorReport:
        return self.evaluate_one(record)
