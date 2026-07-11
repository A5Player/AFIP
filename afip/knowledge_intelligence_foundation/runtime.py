"""Milestone M Pack 1: deterministic knowledge intelligence foundation."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class KnowledgeIntelligenceFoundationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    foundation_id: str
    knowledge_version: str
    source_record_count: int
    accepted_record_count: int
    rejected_record_count: int
    data_quality_valid: bool
    chronological_integrity_valid: bool
    unique_record_ids_valid: bool
    market_regime_present: bool
    feature_schema_valid: bool
    outcome_schema_valid: bool
    explainability_metadata_present: bool
    lineage_valid: bool
    research_only: bool
    pattern_search_enabled: bool
    pattern_clustering_enabled: bool
    production_knowledge_approved: bool
    research_knowledge_approved: bool
    block_reasons: tuple[str, ...]
    foundation_reason_en: str
    foundation_reason_th: str
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
        return asdict(self)


class KnowledgeIntelligenceFoundationRuntime:
    """Validates and versions research knowledge records without execution authority."""

    REQUIRED_FIELDS = (
        "record_id", "observed_at_utc", "market_regime", "feature_vector",
        "outcome", "source_lineage", "explanation",
    )

    def evaluate_one(self, record: Mapping[str, Any]) -> KnowledgeIntelligenceFoundationReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        knowledge_version = str(record.get("knowledge_version", "M1.0.0-RESEARCH")).strip() or "M1.0.0-RESEARCH"
        records = self._records(record.get("knowledge_records", ()))

        ids = [str(item.get("record_id", "")).strip() for item in records]
        timestamps = [str(item.get("observed_at_utc", "")).strip() for item in records]
        complete = [item for item in records if all(self._present(item.get(field)) for field in self.REQUIRED_FIELDS)]
        feature_schema_valid = bool(records) and all(isinstance(item.get("feature_vector"), Mapping) and bool(item.get("feature_vector")) for item in records)
        outcome_schema_valid = bool(records) and all(isinstance(item.get("outcome"), Mapping) and "accepted" in item.get("outcome", {}) for item in records)
        checks = {
            "milestone_l_not_complete": bool(record.get("milestone_l_complete", False)),
            "milestone_m_not_authorized": bool(record.get("ready_for_milestone_m", False)),
            "knowledge_records_missing": bool(records),
            "knowledge_records_incomplete": len(complete) == len(records) and bool(records),
            "chronological_integrity_invalid": timestamps == sorted(timestamps) and all(timestamps),
            "duplicate_record_ids": len(ids) == len(set(ids)) and all(ids),
            "market_regime_missing": bool(records) and all(self._present(item.get("market_regime")) for item in records),
            "feature_schema_invalid": feature_schema_valid,
            "outcome_schema_invalid": outcome_schema_valid,
            "explainability_metadata_missing": bool(records) and all(self._present(item.get("explanation")) for item in records),
            "lineage_invalid": bool(records) and all(self._present(item.get("source_lineage")) for item in records),
            "future_leakage_detected": not bool(record.get("future_leakage_detected", False)),
            "data_quality_not_certified": bool(record.get("data_quality_certified", False)),
            "knowledge_version_missing": bool(knowledge_version),
            "xm_only_policy": broker == "XM",
            "gold_only_policy": symbol == "GOLD#",
            "fixed_unit_policy": abs(lot - 0.01) <= 1e-12,
            "simulation_lock_missing": execution_status == "LOCKED_SIMULATION_ONLY",
            "direct_execution_requested": not bool(record.get("direct_execution", False)),
            "live_execution_requested": not bool(record.get("live_execution_enabled", False)),
            "order_status_not_safe": order_status == "NO_ORDER_SENT",
            "broker_request_created": not bool(record.get("broker_request_created", False)),
            "order_transmission_attempted": not bool(record.get("order_transmission_attempted", False)),
        }
        blocks = tuple(name for name, passed in checks.items() if not passed)
        accepted = sum(1 for item in records if bool(item.get("outcome", {}).get("accepted", False)))
        payload = {
            "knowledge_version": knowledge_version,
            "record_ids": ids,
            "timestamps": timestamps,
            "lineage": [item.get("source_lineage") for item in records],
            "checks": checks,
        }
        foundation_id = "M01-" + sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()[:16].upper()
        ready = not blocks
        if ready:
            status, reason = "READY", "knowledge_intelligence_foundation_ready"
            en = "Research knowledge records passed deterministic schema, lineage, chronology, explainability, and data-quality controls."
            th = "ข้อมูลความรู้สำหรับการวิจัยผ่านการตรวจ Schema, Lineage, ลำดับเวลา, Explainability และคุณภาพข้อมูลแบบ Deterministic"
            next_en = "Continue to Milestone M Pack 2 Pattern Knowledge Engine. Keep all knowledge research-only and execution locked."
            next_th = "ดำเนินการต่อ Milestone M Pack 2 Pattern Knowledge Engine โดยคงความรู้ไว้ใน Research และล็อก Execution ทั้งหมด"
        else:
            status, reason = "BLOCKED", blocks[0]
            en = "Knowledge Intelligence Foundation is blocked until every source, schema, lineage, policy, and safety control passes."
            th = "Knowledge Intelligence Foundation ถูกบล็อกจนกว่า Source, Schema, Lineage, นโยบาย และความปลอดภัยจะผ่านทั้งหมด"
            next_en = "Correct every block reason and re-run without creating or transmitting an order."
            next_th = "แก้ไข Block Reason ทั้งหมดและรันใหม่โดยไม่สร้างหรือส่งคำสั่งซื้อขาย"
        return KnowledgeIntelligenceFoundationReport(
            status=status, reason=reason, milestone="MILESTONE_M", pack="PACK_1",
            foundation_id=foundation_id, knowledge_version=knowledge_version,
            source_record_count=len(records), accepted_record_count=accepted,
            rejected_record_count=max(0, len(records) - accepted),
            data_quality_valid=checks["data_quality_not_certified"] and checks["future_leakage_detected"],
            chronological_integrity_valid=checks["chronological_integrity_invalid"],
            unique_record_ids_valid=checks["duplicate_record_ids"],
            market_regime_present=checks["market_regime_missing"],
            feature_schema_valid=feature_schema_valid, outcome_schema_valid=outcome_schema_valid,
            explainability_metadata_present=checks["explainability_metadata_missing"],
            lineage_valid=checks["lineage_invalid"], research_only=True,
            pattern_search_enabled=False, pattern_clustering_enabled=False,
            production_knowledge_approved=False, research_knowledge_approved=ready,
            block_reasons=blocks, foundation_reason_en=en, foundation_reason_th=th,
            expected_next_action_en=next_en, expected_next_action_th=next_th,
            broker=broker, symbol=symbol, lot_per_unit=lot,
            execution_status=execution_status, direct_execution=False,
            live_execution_enabled=False, order_status=order_status,
            broker_request_created=False, order_transmission_attempted=False,
            trading_logic_changed=False,
        )

    @staticmethod
    def _records(value: Any) -> tuple[Mapping[str, Any], ...]:
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return tuple(item for item in value if isinstance(item, Mapping))
        return ()

    @staticmethod
    def _present(value: Any) -> bool:
        if value is None: return False
        if isinstance(value, str): return bool(value.strip())
        if isinstance(value, Mapping): return bool(value)
        return True

    @staticmethod
    def _number(value: Any) -> float:
        try: return float(value)
        except (TypeError, ValueError): return 0.0
