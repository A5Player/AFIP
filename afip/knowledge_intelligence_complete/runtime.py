"""Milestone M Pack 10: deterministic Knowledge Intelligence completion gate."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


_REQUIRED_CAPABILITIES = (
    "knowledge_intelligence_foundation",
    "pattern_knowledge_engine",
    "pattern_similarity_search",
    "pattern_clustering",
    "pattern_statistics",
    "pattern_validation",
    "pattern_explainability",
    "historical_pattern_database",
    "pattern_confidence",
)


@dataclass(frozen=True)
class KnowledgeIntelligenceCompleteReport:
    status: str
    reason: str
    milestone: str
    pack: str
    completion_id: str
    knowledge_version: str
    required_capability_count: int
    completed_capability_count: int
    missing_capabilities: tuple[str, ...]
    capability_lineage_valid: bool
    data_quality_certified: bool
    future_safe: bool
    deterministic_runtime_valid: bool
    market_regime_before_signal: bool
    milestone_m_complete: bool
    ready_for_milestone_n: bool
    research_knowledge_approved: bool
    production_knowledge_approved: bool
    feature_flags: tuple[tuple[str, bool], ...]
    block_reasons: tuple[str, ...]
    explanation_reason_en: str
    explanation_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    broker: str = "XM"
    symbol: str = "GOLD#"
    lot_per_unit: float = 0.01
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    direct_execution: bool = False
    live_execution_enabled: bool = False
    order_status: str = "NO_ORDER_SENT"
    broker_request_created: bool = False
    order_transmission_attempted: bool = False
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["feature_flags"] = dict(self.feature_flags)
        return payload


class KnowledgeIntelligenceCompleteRuntime:
    """Closes Milestone M without granting production or execution authority."""

    def evaluate_one(self, record: Mapping[str, Any]) -> KnowledgeIntelligenceCompleteReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01), 0.01)
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        knowledge_version = str(record.get("knowledge_version", "M1.10.0-RESEARCH")).strip() or "M1.10.0-RESEARCH"

        raw_caps = record.get("capabilities", {})
        capabilities = dict(raw_caps) if isinstance(raw_caps, Mapping) else {}
        completed = tuple(sorted(name for name in _REQUIRED_CAPABILITIES if bool(capabilities.get(name, False))))
        missing = tuple(sorted(set(_REQUIRED_CAPABILITIES) - set(completed)))
        lineages = self._strings(record.get("capability_lineages", ()))
        lineage_valid = len(lineages) >= len(_REQUIRED_CAPABILITIES) and len(set(lineages)) == len(lineages)
        data_quality = bool(record.get("data_quality_certified", False))
        future_safe = not bool(record.get("future_leakage_detected", False))
        deterministic = bool(record.get("deterministic_runtime_valid", True))
        regime_first = bool(record.get("market_regime_before_signal", True))

        blocked: list[str] = []
        if missing: blocked.append("required_capabilities_incomplete")
        if not lineage_valid: blocked.append("capability_lineage_invalid")
        if not data_quality: blocked.append("data_quality_not_certified")
        if not future_safe: blocked.append("future_leakage_detected")
        if not deterministic: blocked.append("deterministic_runtime_invalid")
        if not regime_first: blocked.append("market_regime_sequence_invalid")
        if broker != "XM": blocked.append("broker_policy_violation")
        if symbol != "GOLD#": blocked.append("symbol_policy_violation")
        if abs(lot - 0.01) > 1e-12: blocked.append("base_unit_policy_violation")
        if execution_status != "LOCKED_SIMULATION_ONLY": blocked.append("execution_lock_invalid")
        if order_status != "NO_ORDER_SENT": blocked.append("order_status_invalid")
        if bool(record.get("direct_execution", False)) or bool(record.get("live_execution_enabled", False)):
            blocked.append("execution_enablement_forbidden")
        if bool(record.get("broker_request_created", False)) or bool(record.get("order_transmission_attempted", False)):
            blocked.append("order_transmission_forbidden")

        ready = not blocked
        flags = tuple(sorted({
            "knowledge_intelligence_complete": ready,
            "portfolio_intelligence_enabled": False,
            "production_knowledge_approval_enabled": False,
            "direct_execution_enabled": False,
            "live_execution_enabled": False,
        }.items()))
        identity = {
            "knowledge_version": knowledge_version,
            "completed": completed,
            "lineages": sorted(lineages),
            "flags": flags,
            "blocked": sorted(set(blocked)),
        }
        completion_id = "MCOMP-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        return KnowledgeIntelligenceCompleteReport(
            status="READY" if ready else "BLOCKED",
            reason="Milestone M Knowledge Intelligence is complete under research-only authority." if ready else "Milestone M completion is blocked by integrity or safety controls.",
            milestone="M", pack="10", completion_id=completion_id, knowledge_version=knowledge_version,
            required_capability_count=len(_REQUIRED_CAPABILITIES), completed_capability_count=len(completed),
            missing_capabilities=missing, capability_lineage_valid=lineage_valid,
            data_quality_certified=data_quality, future_safe=future_safe,
            deterministic_runtime_valid=deterministic, market_regime_before_signal=regime_first,
            milestone_m_complete=ready, ready_for_milestone_n=ready,
            research_knowledge_approved=ready, production_knowledge_approved=False,
            feature_flags=flags, block_reasons=tuple(sorted(set(blocked))),
            explanation_reason_en="Confirms all Milestone M knowledge capabilities, lineage, data quality, future safety and permanent execution locks." if ready else "Completion remains blocked until all knowledge, integrity and safety gates pass.",
            explanation_reason_th="ยืนยันความสามารถด้านความรู้ของ Milestone M, Lineage, คุณภาพข้อมูล, Future Safety และ Execution Lock ครบถ้วน" if ready else "การปิด Milestone M ยังถูกบล็อกจนกว่าด่านความรู้ ความสมบูรณ์ และความปลอดภัยจะผ่านครบ",
            expected_next_action_en="Continue to Milestone N Pack 1 — Portfolio Intelligence Foundation." if ready else "Correct blocked inputs and evaluate again.",
            expected_next_action_th="ดำเนินการต่อ Milestone N Pack 1 — Portfolio Intelligence Foundation" if ready else "แก้ข้อมูลที่ถูกบล็อกแล้วประเมินใหม่",
            broker=broker, symbol=symbol, lot_per_unit=lot,
        )

    @staticmethod
    def _strings(value: Any) -> tuple[str, ...]:
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return tuple(str(v).strip() for v in value if str(v).strip())
        return ()

    @staticmethod
    def _number(value: Any, default: float) -> float:
        try:
            number = float(value)
            return number if number == number else default
        except (TypeError, ValueError):
            return default
