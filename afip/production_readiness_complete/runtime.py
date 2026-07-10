"""Deterministic Milestone L completion gate without enabling order transmission."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

@dataclass(frozen=True)
class ProductionReadinessCompleteReport:
    status: str; reason: str; milestone: str; pack: str; readiness: str
    completion_id: str; release_candidate_id: str
    release_candidate_ready: bool; all_milestone_l_packs_ready: bool
    production_health_monitor_ready: bool; emergency_safety_system_ready: bool
    production_report_ready: bool; decision_ledger_ready: bool
    data_quality_certified: bool; knowledge_versioning_ready: bool
    feature_flags_ready: bool; operation_manual_en_ready: bool
    operation_manual_th_ready: bool; audit_chain_ready: bool
    independent_trade_plan_valid: bool; protected_runner_exposure_included: bool
    traditional_dca_disabled: bool; averaging_down_disabled: bool
    milestone_l_complete: bool; ready_for_milestone_m: bool
    production_certified: bool; broker_request_created: bool
    order_transmission_attempted: bool; block_reasons: tuple[str, ...]
    completion_reason_en: str; completion_reason_th: str
    expected_next_action_en: str; expected_next_action_th: str
    broker: str = "XM"; symbol: str = "GOLD#"; lot_per_unit: float = 0.01
    execution_status: str = "LOCKED_SIMULATION_ONLY"; direct_execution: bool = False
    live_execution_enabled: bool = False; order_status: str = "NO_ORDER_SENT"
    trading_logic_changed: bool = False
    def as_dict(self) -> dict[str, Any]: return asdict(self)

class ProductionReadinessCompleteRuntime:
    def evaluate_one(self, record: Mapping[str, Any]) -> ProductionReadinessCompleteReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        candidate_id = str(record.get("release_candidate_id", "")).strip()
        checks = {
            "release_candidate_not_ready": bool(record.get("release_candidate_ready", False)),
            "release_candidate_id_missing": bool(candidate_id),
            "milestone_l_packs_incomplete": bool(record.get("all_milestone_l_packs_ready", False)),
            "production_health_monitor_not_ready": bool(record.get("production_health_monitor_ready", False)),
            "emergency_safety_system_not_ready": bool(record.get("emergency_safety_system_ready", False)),
            "production_report_not_ready": bool(record.get("production_report_ready", False)),
            "decision_ledger_not_ready": bool(record.get("decision_ledger_ready", False)),
            "data_quality_not_certified": bool(record.get("data_quality_certified", False)),
            "knowledge_versioning_not_ready": bool(record.get("knowledge_versioning_ready", False)),
            "feature_flags_not_ready": bool(record.get("feature_flags_ready", False)),
            "operation_manual_en_missing": bool(record.get("operation_manual_en_ready", False)),
            "operation_manual_th_missing": bool(record.get("operation_manual_th_ready", False)),
            "audit_chain_not_ready": bool(record.get("audit_chain_ready", False)),
            "independent_trade_plan_invalid": bool(record.get("independent_trade_plan_valid", False)),
            "protected_runner_exposure_excluded": bool(record.get("protected_runner_exposure_included", False)),
            "traditional_dca_enabled": not bool(record.get("traditional_dca_enabled", False)),
            "averaging_down_enabled": not bool(record.get("averaging_down_enabled", False)),
            "xm_only_policy": broker == "XM", "gold_only_policy": symbol == "GOLD#",
            "fixed_unit_policy": abs(lot - 0.01) <= 1e-12,
            "simulation_lock_missing": execution_status == "LOCKED_SIMULATION_ONLY",
            "direct_execution_requested": not bool(record.get("direct_execution", False)),
            "live_execution_requested": not bool(record.get("live_execution_enabled", False)),
            "order_status_not_safe": order_status == "NO_ORDER_SENT",
            "broker_request_created": not bool(record.get("broker_request_created", False)),
            "order_transmission_attempted": not bool(record.get("order_transmission_attempted", False)),
        }
        blocks = tuple(name for name, passed in checks.items() if not passed)
        payload = {"release_candidate_id": candidate_id, "checks": checks, "broker": broker, "symbol": symbol, "lot_per_unit": lot}
        completion_id = "L10-" + sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        complete = not blocks
        if complete:
            status, reason, readiness = "READY", "milestone_l_production_readiness_complete", "MILESTONE_L_COMPLETE"
            en = "Milestone L Packs 1-10 and all production-readiness controls passed without enabling broker order transmission."
            th = "Milestone L Pack 1-10 และระบบควบคุมความพร้อม Production ผ่านครบ โดยยังไม่เปิดการส่งคำสั่งไปยัง Broker"
            next_en = "Continue to Milestone M Pack 1 Knowledge Intelligence Foundation. Keep all execution locks active."
            next_th = "ดำเนินการต่อสู่ Milestone M Pack 1 Knowledge Intelligence Foundation และคง Execution Lock ทั้งหมด"
        else:
            status, reason, readiness = "BLOCKED", blocks[0], "MILESTONE_L_INCOMPLETE"
            en = "Milestone L cannot close until every release-candidate, operational, documentation, policy, and safety gate passes."
            th = "Milestone L ยังปิดไม่ได้จนกว่าเกณฑ์ Release Candidate ระบบปฏิบัติการ เอกสาร นโยบาย และความปลอดภัยจะผ่านทั้งหมด"
            next_en = "Correct every block reason and re-run the completion gate without creating or transmitting an order."
            next_th = "แก้ไข Block Reason ทั้งหมดและรันเกณฑ์ปิด Milestone ใหม่โดยไม่สร้างหรือส่งคำสั่งซื้อขาย"
        return ProductionReadinessCompleteReport(
            status, reason, "MILESTONE_L", "PACK_10", readiness, completion_id, candidate_id,
            checks["release_candidate_not_ready"], checks["milestone_l_packs_incomplete"],
            checks["production_health_monitor_not_ready"], checks["emergency_safety_system_not_ready"],
            checks["production_report_not_ready"], checks["decision_ledger_not_ready"],
            checks["data_quality_not_certified"], checks["knowledge_versioning_not_ready"],
            checks["feature_flags_not_ready"], checks["operation_manual_en_missing"],
            checks["operation_manual_th_missing"], checks["audit_chain_not_ready"],
            checks["independent_trade_plan_invalid"], checks["protected_runner_exposure_excluded"],
            checks["traditional_dca_enabled"], checks["averaging_down_enabled"], complete, complete,
            False, False, False, blocks, en, th, next_en, next_th,
            broker, symbol, lot, execution_status, False, False, order_status, False,
        )
    @staticmethod
    def _number(value: Any) -> float:
        try: return float(value)
        except (TypeError, ValueError): return 0.0
