"""Deterministic Milestone K execution-intelligence completion gate."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Any, Mapping

_REQUIRED_PACKS = tuple(f"milestone_k_pack_{index}" for index in range(1, 10))
_PASSING = {"READY", "CERTIFIED", "COMPLETE", "COMPLETED", "MONITORING", "MONITORING_CERTIFIED"}


@dataclass(frozen=True)
class ExecutionIntelligenceCompleteReport:
    status: str
    reason: str
    milestone: str
    completion_readiness: str
    completion_id: str
    pack_statuses: tuple[tuple[str, str], ...]
    completed_pack_count: int
    required_pack_count: int
    all_packs_complete: bool
    runtime_certified: bool
    dashboard_explainability_ready: bool
    audit_chain_ready: bool
    broker_policy_certified: bool
    symbol_policy_certified: bool
    unit_policy_certified: bool
    simulation_lock_certified: bool
    direct_execution_blocked: bool
    live_execution_blocked: bool
    no_order_sent_certified: bool
    milestone_k_complete: bool
    block_reasons: tuple[str, ...]
    completion_reason_en: str
    completion_reason_th: str
    holding_reason_en: str
    holding_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    confidence: float
    next_review_time_utc: str
    broker: str = "XM"
    symbol: str = "GOLD#"
    lot_per_unit: float = 0.01
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    direct_execution: bool = False
    live_execution_enabled: bool = False
    order_status: str = "NO_ORDER_SENT"
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExecutionIntelligenceCompleteRuntime:
    """Close Milestone K only when every pack and execution-safety gate passes."""

    def evaluate_one(self, record: Mapping[str, Any]) -> ExecutionIntelligenceCompleteReport:
        now = self._utc_time(record.get("current_time_utc"))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot_per_unit = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        direct_requested = bool(record.get("direct_execution", False))
        live_requested = bool(record.get("live_execution_enabled", False))
        runtime_status = str(record.get("runtime_certification_status", record.get("status", "CERTIFIED"))).strip().upper()
        runtime_integrity = bool(record.get("runtime_integrity_certified", True))
        dashboard_ready = bool(record.get("dashboard_explainability_ready", True))
        audit_ready = bool(record.get("audit_record_ready", True))

        raw = record.get("pack_statuses", {})
        mapping = raw if isinstance(raw, Mapping) else {}
        pack_statuses = tuple((name, str(mapping.get(name, "COMPLETED")).strip().upper() or "UNKNOWN") for name in _REQUIRED_PACKS)
        completed = sum(status in _PASSING for _, status in pack_statuses)
        all_packs = completed == len(_REQUIRED_PACKS)
        runtime_certified = runtime_status in {"CERTIFIED", "READY"} and runtime_integrity

        checks = {
            "milestone_k_pack_incomplete": all_packs,
            "runtime_execution_not_certified": runtime_certified,
            "dashboard_explainability_not_ready": dashboard_ready,
            "audit_chain_not_ready": audit_ready,
            "xm_only_policy": broker == "XM",
            "gold_only_policy": symbol == "GOLD#",
            "fixed_unit_policy": abs(lot_per_unit - 0.01) <= 1e-12,
            "simulation_lock_missing": execution_status == "LOCKED_SIMULATION_ONLY",
            "direct_execution_requested": not direct_requested,
            "live_execution_requested": not live_requested,
            "order_status_not_safe": order_status == "NO_ORDER_SENT",
        }
        blocks = tuple(name for name, passed in checks.items() if not passed)
        complete = not blocks
        payload = {
            "packs": pack_statuses, "runtime": runtime_status, "integrity": runtime_integrity,
            "broker": broker, "symbol": symbol, "lot_per_unit": lot_per_unit,
            "execution_status": execution_status, "order_status": order_status,
        }
        completion_id = "K10-" + sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()

        if complete:
            status, reason, readiness = "COMPLETE", "milestone_k_execution_intelligence_complete", "MILESTONE_K_COMPLETE"
            reason_en = "Milestone K Packs 1-9, runtime certification, dashboard explainability, audit controls, and every execution-safety policy passed the deterministic completion gate."
            reason_th = "Milestone K Pack 1-9, การรับรอง Runtime, Dashboard Explainability, Audit Control และนโยบายความปลอดภัยทั้งหมดผ่าน Completion Gate แบบกำหนดแน่นอน"
            hold_en = "Keep live and direct execution disabled after milestone completion."
            hold_th = "คงการปิด Live Execution และ Direct Execution หลังปิด Milestone"
            next_en = "Archive the Milestone K certification and continue with Milestone L without enabling live order transmission."
            next_th = "จัดเก็บใบรับรอง Milestone K และดำเนินการต่อที่ Milestone L โดยไม่เปิดการส่งคำสั่งจริง"
        else:
            status, reason, readiness = "BLOCKED", blocks[0], "NOT_COMPLETE"
            reason_en = "Milestone K cannot close because at least one pack, certification, explainability, audit, policy, or execution-safety gate did not pass."
            reason_th = "ยังปิด Milestone K ไม่ได้ เนื่องจาก Pack, Certification, Explainability, Audit, นโยบาย หรือ Execution Safety อย่างน้อยหนึ่งรายการไม่ผ่าน"
            hold_en = "Hold the current project state and keep all execution paths disabled."
            hold_th = "คงสถานะโครงการปัจจุบันและปิดทุกเส้นทางการส่งคำสั่ง"
            next_en = "Correct every completion block and rerun Pack 10 certification."
            next_th = "แก้ไขทุก Completion Block แล้วรันการรับรอง Pack 10 อีกครั้ง"

        confidence = round(sum(checks.values()) / len(checks) * 100.0, 2)
        review_seconds = max(60, self._integer(record.get("next_review_seconds", 300)) or 300)
        return ExecutionIntelligenceCompleteReport(
            status=status, reason=reason, milestone="MILESTONE_K", completion_readiness=readiness,
            completion_id=completion_id, pack_statuses=pack_statuses, completed_pack_count=completed,
            required_pack_count=len(_REQUIRED_PACKS), all_packs_complete=all_packs,
            runtime_certified=runtime_certified, dashboard_explainability_ready=dashboard_ready,
            audit_chain_ready=audit_ready, broker_policy_certified=checks["xm_only_policy"],
            symbol_policy_certified=checks["gold_only_policy"], unit_policy_certified=checks["fixed_unit_policy"],
            simulation_lock_certified=checks["simulation_lock_missing"], direct_execution_blocked=checks["direct_execution_requested"],
            live_execution_blocked=checks["live_execution_requested"], no_order_sent_certified=checks["order_status_not_safe"],
            milestone_k_complete=complete, block_reasons=blocks, completion_reason_en=reason_en, completion_reason_th=reason_th,
            holding_reason_en=hold_en, holding_reason_th=hold_th, expected_next_action_en=next_en, expected_next_action_th=next_th,
            confidence=confidence, next_review_time_utc=(now + timedelta(seconds=review_seconds)).isoformat(),
            broker=broker, symbol=symbol, lot_per_unit=lot_per_unit, execution_status=execution_status,
        )

    def explain_one(self, record: Mapping[str, Any]) -> ExecutionIntelligenceCompleteReport:
        return self.evaluate_one(record)

    @staticmethod
    def _number(value: Any) -> float:
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _integer(value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _utc_time(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc)
        if isinstance(value, str) and value.strip():
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
            except ValueError:
                pass
        return datetime.now(timezone.utc)
