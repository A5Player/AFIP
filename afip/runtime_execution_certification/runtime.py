"""Deterministic runtime execution certification for locked simulation only."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Any, Mapping

_ALLOWED_ACTIONS = {
    "HOLD", "ENTRY", "EXIT", "EMERGENCY_EXIT", "PARTIAL_CLOSE",
    "TRAIL_STOP", "MOVE_STOP_LOSS", "CHANGE_TAKE_PROFIT",
}
_REQUIRED_DEPENDENCIES = (
    "execution_intelligence_foundation", "smart_entry", "smart_exit",
    "dynamic_stop_loss", "dynamic_take_profit", "trailing_stop",
    "partial_close", "execution_supervisor",
)


@dataclass(frozen=True)
class RuntimeExecutionCertificationReport:
    status: str
    reason: str
    certification_readiness: str
    certification_id: str
    approved_action: str
    supervisor_status: str
    supervisor_readiness: str
    dependency_statuses: tuple[tuple[str, str], ...]
    dependencies_certified: bool
    action_consistent: bool
    position_state_consistent: bool
    unit_policy_certified: bool
    broker_policy_certified: bool
    symbol_policy_certified: bool
    simulation_lock_certified: bool
    direct_execution_blocked: bool
    live_execution_blocked: bool
    no_order_sent_certified: bool
    runtime_integrity_certified: bool
    audit_record_ready: bool
    block_reasons: tuple[str, ...]
    certification_reason_en: str
    certification_reason_th: str
    holding_reason_en: str
    holding_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    confidence: float
    next_review_time_utc: str
    broker: str = "XM"
    symbol: str = "GOLD#"
    lot_per_unit: float = 0.01
    direct_execution: bool = False
    live_execution_enabled: bool = False
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    order_status: str = "NO_ORDER_SENT"
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class RuntimeExecutionCertificationRuntime:
    """Certify one supervised paper/demo instruction without executing it."""

    def evaluate_one(self, record: Mapping[str, Any]) -> RuntimeExecutionCertificationReport:
        now = self._utc_time(record.get("current_time_utc"))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot_per_unit = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        approved_action = str(record.get("approved_action", "HOLD")).strip().upper() or "HOLD"
        supervisor_status = str(record.get("supervisor_status", record.get("status", "READY"))).strip().upper()
        supervisor_readiness = str(record.get("supervisor_readiness", "MONITORING" if approved_action == "HOLD" else "READY")).strip().upper()
        position_state = str(record.get("position_state", "FLAT")).strip().upper()
        current_units = max(0, self._integer(record.get("current_units", 0)))
        approved_units = max(0, self._integer(record.get("approved_units", 0)))
        simulation_ready = bool(record.get("simulation_instruction_ready", approved_action != "HOLD"))
        direct_requested = bool(record.get("direct_execution", False))
        live_requested = bool(record.get("live_execution_enabled", False))
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()

        dependency_statuses = self._dependencies(record)
        dependencies_certified = all(status in {"READY", "MONITORING", "CERTIFIED", "COMPLETE", "COMPLETED"} for _, status in dependency_statuses)
        action_consistent = approved_action in _ALLOWED_ACTIONS and (
            (approved_action == "HOLD" and not simulation_ready) or
            (approved_action != "HOLD" and simulation_ready)
        )
        management_actions = {"EXIT", "EMERGENCY_EXIT", "PARTIAL_CLOSE", "TRAIL_STOP", "MOVE_STOP_LOSS", "CHANGE_TAKE_PROFIT"}
        position_state_consistent = (
            (approved_action == "ENTRY" and position_state == "FLAT" and current_units == 0 and approved_units > 0)
            or (approved_action in management_actions and position_state == "OPEN" and current_units > 0)
            or approved_action == "HOLD"
        )
        if approved_action == "PARTIAL_CLOSE":
            position_state_consistent = position_state_consistent and 0 < approved_units < current_units
        if approved_action in {"EXIT", "EMERGENCY_EXIT"}:
            position_state_consistent = position_state_consistent and approved_units == current_units

        checks = {
            "dependencies_not_certified": dependencies_certified,
            "supervisor_not_ready": supervisor_status == "READY" and supervisor_readiness in {"READY", "MONITORING"},
            "approved_action_inconsistent": action_consistent,
            "position_state_inconsistent": position_state_consistent,
            "xm_only_policy": broker == "XM",
            "gold_only_policy": symbol == "GOLD#",
            "fixed_unit_policy": abs(lot_per_unit - 0.01) <= 1e-12,
            "simulation_lock_missing": execution_status == "LOCKED_SIMULATION_ONLY",
            "direct_execution_requested": not direct_requested,
            "live_execution_requested": not live_requested,
            "order_status_not_safe": order_status == "NO_ORDER_SENT",
        }
        blocks = tuple(reason for reason, passed in checks.items() if not passed)
        integrity = not blocks
        audit_payload = {
            "action": approved_action, "broker": broker, "symbol": symbol,
            "units": approved_units, "position_state": position_state,
            "dependencies": dependency_statuses, "execution_status": execution_status,
            "order_status": order_status,
        }
        certification_id = "K9-" + sha256(json.dumps(audit_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:16].upper()

        if blocks:
            status, reason, readiness = "BLOCKED", blocks[0], "NOT_CERTIFIED"
            reason_en = "Runtime execution certification failed because at least one dependency, action, position, policy, or execution-safety control did not pass."
            reason_th = "การรับรอง Runtime Execution ไม่ผ่าน เนื่องจาก Dependency, Action, Position, นโยบาย หรือการควบคุมความปลอดภัยอย่างน้อยหนึ่งรายการไม่ผ่าน"
            hold_en = "Hold the current state and keep every execution path disabled."
            hold_th = "คงสถานะปัจจุบันและปิดทุกเส้นทางการส่งคำสั่งต่อไป"
            next_en = "Correct the certification blocks and run the full certification again."
            next_th = "แก้ไขรายการที่บล็อก แล้วรันการรับรองทั้งหมดอีกครั้ง"
        elif approved_action == "HOLD":
            status, reason, readiness = "CERTIFIED", "runtime_monitoring_certified", "MONITORING_CERTIFIED"
            reason_en = "Runtime controls are certified for monitoring; no supervised simulation action is currently approved."
            reason_th = "การควบคุม Runtime ผ่านการรับรองสำหรับการติดตาม และยังไม่มี Action จำลองที่ Supervisor อนุมัติ"
            hold_en = "Maintain the current state and continue certified monitoring without sending an order."
            hold_th = "คงสถานะปัจจุบันและติดตามภายใต้การรับรองต่อไปโดยไม่ส่งคำสั่ง"
            next_en = "Review when the supervisor produces a new validated instruction."
            next_th = "ทบทวนเมื่อ Supervisor สร้างคำแนะนำที่ผ่านการตรวจรายการใหม่"
        else:
            status, reason, readiness = "CERTIFIED", "runtime_simulation_instruction_certified", "CERTIFIED"
            reason_en = f"The {approved_action} instruction passed runtime, dependency, policy, position-state, and execution-safety certification for paper/demo simulation only."
            reason_th = f"คำแนะนำ {approved_action} ผ่านการรับรอง Runtime, Dependency, นโยบาย, Position State และความปลอดภัยสำหรับ Paper/Demo Simulation เท่านั้น"
            hold_en = "Do not bypass the certified instruction or enable a live execution path."
            hold_th = "ห้ามข้ามคำแนะนำที่รับรองแล้วหรือเปิดเส้นทาง Live Execution"
            next_en = "Record the certified simulation instruction in the audit trail; send no live order."
            next_th = "บันทึกคำแนะนำจำลองที่ผ่านการรับรองใน Audit Trail และไม่ส่งคำสั่งจริง"

        passed_count = sum(checks.values())
        confidence = round((passed_count / len(checks)) * 100.0, 2)
        review_seconds = max(30, self._integer(record.get("next_review_seconds", 60)) or 60)
        return RuntimeExecutionCertificationReport(
            status=status, reason=reason, certification_readiness=readiness,
            certification_id=certification_id, approved_action=approved_action,
            supervisor_status=supervisor_status, supervisor_readiness=supervisor_readiness,
            dependency_statuses=dependency_statuses, dependencies_certified=dependencies_certified,
            action_consistent=action_consistent, position_state_consistent=position_state_consistent,
            unit_policy_certified=checks["fixed_unit_policy"], broker_policy_certified=checks["xm_only_policy"],
            symbol_policy_certified=checks["gold_only_policy"], simulation_lock_certified=checks["simulation_lock_missing"],
            direct_execution_blocked=checks["direct_execution_requested"], live_execution_blocked=checks["live_execution_requested"],
            no_order_sent_certified=checks["order_status_not_safe"], runtime_integrity_certified=integrity,
            audit_record_ready=integrity, block_reasons=blocks,
            certification_reason_en=reason_en, certification_reason_th=reason_th,
            holding_reason_en=hold_en, holding_reason_th=hold_th,
            expected_next_action_en=next_en, expected_next_action_th=next_th,
            confidence=confidence, next_review_time_utc=(now + timedelta(seconds=review_seconds)).isoformat(),
            broker=broker, symbol=symbol, lot_per_unit=lot_per_unit,
        )

    def explain_one(self, record: Mapping[str, Any]) -> RuntimeExecutionCertificationReport:
        return self.evaluate_one(record)

    @staticmethod
    def _dependencies(record: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
        raw = record.get("dependency_statuses", {})
        mapping = raw if isinstance(raw, Mapping) else {}
        return tuple((name, str(mapping.get(name, "READY")).strip().upper() or "UNKNOWN") for name in _REQUIRED_DEPENDENCIES)

    @staticmethod
    def _number(value: Any) -> float:
        try: return float(value or 0.0)
        except (TypeError, ValueError): return 0.0

    @staticmethod
    def _integer(value: Any) -> int:
        try: return int(value or 0)
        except (TypeError, ValueError): return 0

    @staticmethod
    def _utc_time(value: Any) -> datetime:
        if isinstance(value, datetime): return value.astimezone(timezone.utc)
        if isinstance(value, str) and value.strip():
            try: return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
            except ValueError: pass
        return datetime.now(timezone.utc)
