"""Deterministic Version 1.0 release-candidate gate for Milestone L Pack 9."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

@dataclass(frozen=True)
class Version1ReleaseCandidateReport:
    status: str; reason: str; milestone: str; pack: str; release_readiness: str
    release_candidate_id: str; demo_certification_id: str
    dependency_statuses: tuple[tuple[str, str], ...]
    all_pack_dependencies_ready: bool; demo_observation_certified: bool
    production_health_monitor_ready: bool; emergency_safety_system_ready: bool
    production_report_ready: bool; decision_ledger_ready: bool
    data_quality_certified: bool; knowledge_versioning_ready: bool
    feature_flags_ready: bool; operation_manual_en_ready: bool
    operation_manual_th_ready: bool; audit_chain_ready: bool
    independent_trade_plan_valid: bool; protected_runner_exposure_included: bool
    traditional_dca_disabled: bool; averaging_down_disabled: bool
    release_candidate_approved: bool; production_certified: bool
    broker_request_created: bool; order_transmission_attempted: bool
    block_reasons: tuple[str, ...]; release_reason_en: str; release_reason_th: str
    expected_next_action_en: str; expected_next_action_th: str
    broker: str = "XM"; symbol: str = "GOLD#"; lot_per_unit: float = 0.01
    execution_status: str = "LOCKED_SIMULATION_ONLY"; direct_execution: bool = False
    live_execution_enabled: bool = False; order_status: str = "NO_ORDER_SENT"
    trading_logic_changed: bool = False
    def as_dict(self) -> dict[str, Any]: return asdict(self)

class Version1ReleaseCandidateRuntime:
    _DEPENDENCIES = (
        "paper_execution_foundation", "paper_execution_session_monitor",
        "paper_decision_ledger", "paper_outcome_evaluation",
        "paper_performance_analytics", "paper_performance_certification",
        "shadow_execution_observation", "demo_execution_certification",
    )
    def evaluate_one(self, record: Mapping[str, Any]) -> Version1ReleaseCandidateReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        demo_id = str(record.get("demo_certification_id", "")).strip()
        deps = tuple((n, str(record.get(f"{n}_status", "BLOCKED")).strip().upper() or "BLOCKED") for n in self._DEPENDENCIES)
        deps_ready = all(s == "READY" for _, s in deps)
        controls = {
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
        }
        policy = {
            "milestone_l_dependency_not_ready": deps_ready,
            "demo_observation_not_certified": bool(record.get("certified_for_demo_observation", False)),
            "demo_certification_id_missing": bool(demo_id),
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
        checks = {**policy, **controls}; blocks = tuple(k for k, v in checks.items() if not v)
        payload = {"demo_certification_id": demo_id, "dependency_statuses": deps, "checks": checks, "broker": broker, "symbol": symbol, "lot_per_unit": lot}
        candidate_id = "L09-" + sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        approved = not blocks
        if approved:
            status, reason, readiness = "READY", "production_release_candidate_approved", "PRODUCTION_RELEASE_CANDIDATE_READY"
            en = "Milestone L Packs 1-8, operational controls, documentation, audit, data quality, and permanent safety policies passed the release-candidate gate."
            th = "Milestone L Pack 1-8 ระบบควบคุม เอกสาร Audit คุณภาพข้อมูล และนโยบายความปลอดภัยถาวร ผ่านเกณฑ์ Release Candidate"
            next_en = "Continue to Pack 10 Production Readiness Complete. Keep demo and live order transmission disabled."
            next_th = "ดำเนินการต่อสู่ Pack 10 Production Readiness Complete และคงการส่งคำสั่ง Demo กับ Live ไว้เป็นปิด"
        else:
            status, reason, readiness = "BLOCKED", blocks[0], "PRODUCTION_RELEASE_CANDIDATE_BLOCKED"
            en = "The release candidate is blocked by an incomplete dependency, operational control, documentation, policy, or safety gate."
            th = "Release Candidate ถูกบล็อกโดย Dependency ระบบควบคุม เอกสาร นโยบาย หรือเกณฑ์ความปลอดภัยที่ยังไม่ครบ"
            next_en = "Correct every block reason and re-run the review without creating or transmitting an order."
            next_th = "แก้ไข Block Reason ทั้งหมดและทบทวนใหม่โดยไม่สร้างหรือส่งคำสั่งซื้อขาย"
        return Version1ReleaseCandidateReport(
            status, reason, "MILESTONE_L", "PACK_9", readiness, candidate_id, demo_id, deps, deps_ready,
            policy["demo_observation_not_certified"], controls["production_health_monitor_not_ready"],
            controls["emergency_safety_system_not_ready"], controls["production_report_not_ready"],
            controls["decision_ledger_not_ready"], controls["data_quality_not_certified"],
            controls["knowledge_versioning_not_ready"], controls["feature_flags_not_ready"],
            controls["operation_manual_en_missing"], controls["operation_manual_th_missing"],
            controls["audit_chain_not_ready"], policy["independent_trade_plan_invalid"],
            policy["protected_runner_exposure_excluded"], policy["traditional_dca_enabled"],
            policy["averaging_down_enabled"], approved, False, False, False, blocks, en, th, next_en, next_th,
            broker, symbol, lot, execution_status, False, False, order_status, False,
        )
    @staticmethod
    def _number(value: Any) -> float:
        try: return float(value)
        except (TypeError, ValueError): return 0.0
