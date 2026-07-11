"""Milestone M Pack 2: deterministic pattern knowledge engine."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class PatternKnowledgeEngineReport:
    status: str
    reason: str
    milestone: str
    pack: str
    engine_id: str
    knowledge_version: str
    source_record_count: int
    eligible_record_count: int
    pattern_count: int
    accepted_pattern_count: int
    rejected_pattern_count: int
    duplicate_pattern_count: int
    market_regime_partitioned: bool
    canonical_feature_schema_valid: bool
    outcome_statistics_valid: bool
    deterministic_identity_valid: bool
    lineage_valid: bool
    future_safe: bool
    research_only: bool
    pattern_search_enabled: bool
    pattern_clustering_enabled: bool
    pattern_statistics_enabled: bool
    pattern_validation_enabled: bool
    production_knowledge_approved: bool
    research_knowledge_approved: bool
    block_reasons: tuple[str, ...]
    engine_reason_en: str
    engine_reason_th: str
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


class PatternKnowledgeEngineRuntime:
    """Builds canonical research pattern identities without search or execution authority."""

    REQUIRED_FIELDS = (
        "record_id", "observed_at_utc", "market_regime", "feature_vector",
        "outcome", "source_lineage", "explanation",
    )

    def evaluate_one(self, record: Mapping[str, Any]) -> PatternKnowledgeEngineReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        knowledge_version = str(record.get("knowledge_version", "M1.1.0-RESEARCH")).strip() or "M1.1.0-RESEARCH"
        records = self._records(record.get("knowledge_records", ()))

        complete = tuple(item for item in records if all(self._present(item.get(field)) for field in self.REQUIRED_FIELDS))
        canonical = [self._canonical_pattern(item) for item in complete]
        pattern_ids = [item["pattern_id"] for item in canonical]
        unique_ids = set(pattern_ids)
        accepted = sum(1 for item in canonical if item["accepted"])
        feature_schema_valid = bool(complete) and all(item["feature_names"] for item in canonical)
        outcome_stats_valid = bool(complete) and all(isinstance(item["r_multiple"], float) for item in canonical)
        checks = {
            "foundation_not_ready": bool(record.get("knowledge_foundation_ready", False)),
            "research_knowledge_not_approved": bool(record.get("research_knowledge_approved", False)),
            "knowledge_records_missing": bool(records),
            "knowledge_records_incomplete": len(complete) == len(records) and bool(records),
            "canonical_feature_schema_invalid": feature_schema_valid,
            "outcome_statistics_invalid": outcome_stats_valid,
            "market_regime_partition_missing": bool(complete) and all(item["market_regime"] for item in canonical),
            "pattern_identity_invalid": bool(pattern_ids) and all(pattern_ids),
            "lineage_invalid": bool(complete) and all(item["source_lineage"] for item in canonical),
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
        payload = {
            "knowledge_version": knowledge_version,
            "patterns": canonical,
            "checks": checks,
        }
        engine_id = "M02-" + sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()[:16].upper()
        ready = not blocks
        if ready:
            status, reason = "READY", "pattern_knowledge_engine_ready"
            en = "Canonical research patterns were built with deterministic identity, regime partitioning, outcome statistics, lineage, and future-safety controls."
            th = "สร้าง Pattern สำหรับการวิจัยแบบ Canonical สำเร็จ พร้อมรหัส Deterministic การแบ่งตาม Market Regime สถิติผลลัพธ์ Lineage และการป้องกัน Future Leakage"
            next_en = "Continue to Milestone M Pack 3 Pattern Similarity Search. Keep search research-only and execution locked."
            next_th = "ดำเนินการต่อ Milestone M Pack 3 Pattern Similarity Search โดยคงการค้นหาไว้ใน Research และล็อก Execution"
        else:
            status, reason = "BLOCKED", blocks[0]
            en = "Pattern Knowledge Engine is blocked until every foundation, schema, lineage, data-quality, and safety control passes."
            th = "Pattern Knowledge Engine ถูกบล็อกจนกว่า Foundation, Schema, Lineage, คุณภาพข้อมูล และความปลอดภัยจะผ่านทั้งหมด"
            next_en = "Correct every block reason and re-run without creating or transmitting an order."
            next_th = "แก้ไข Block Reason ทั้งหมดและรันใหม่โดยไม่สร้างหรือส่งคำสั่งซื้อขาย"
        return PatternKnowledgeEngineReport(
            status=status, reason=reason, milestone="MILESTONE_M", pack="PACK_2",
            engine_id=engine_id, knowledge_version=knowledge_version,
            source_record_count=len(records), eligible_record_count=len(complete),
            pattern_count=len(unique_ids), accepted_pattern_count=accepted,
            rejected_pattern_count=max(0, len(canonical) - accepted),
            duplicate_pattern_count=max(0, len(pattern_ids) - len(unique_ids)),
            market_regime_partitioned=checks["market_regime_partition_missing"],
            canonical_feature_schema_valid=feature_schema_valid,
            outcome_statistics_valid=outcome_stats_valid,
            deterministic_identity_valid=checks["pattern_identity_invalid"],
            lineage_valid=checks["lineage_invalid"], future_safe=checks["future_leakage_detected"],
            research_only=True, pattern_search_enabled=False, pattern_clustering_enabled=False,
            pattern_statistics_enabled=True, pattern_validation_enabled=True,
            production_knowledge_approved=False, research_knowledge_approved=ready,
            block_reasons=blocks, engine_reason_en=en, engine_reason_th=th,
            expected_next_action_en=next_en, expected_next_action_th=next_th,
            broker=broker, symbol=symbol, lot_per_unit=lot, execution_status=execution_status,
            direct_execution=False, live_execution_enabled=False, order_status=order_status,
            broker_request_created=False, order_transmission_attempted=False, trading_logic_changed=False,
        )

    def _canonical_pattern(self, item: Mapping[str, Any]) -> dict[str, Any]:
        features = item.get("feature_vector", {})
        normalized = {str(key): self._number(value) for key, value in sorted(features.items(), key=lambda pair: str(pair[0]))}
        outcome = item.get("outcome", {})
        payload = {"market_regime": str(item.get("market_regime", "")).strip().upper(), "features": normalized}
        pattern_id = "PAT-" + sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        return {
            "pattern_id": pattern_id,
            "record_id": str(item.get("record_id", "")).strip(),
            "market_regime": payload["market_regime"],
            "feature_names": tuple(normalized),
            "features": normalized,
            "accepted": bool(outcome.get("accepted", False)),
            "r_multiple": float(self._number(outcome.get("r_multiple", 0.0))),
            "source_lineage": str(item.get("source_lineage", "")).strip(),
        }

    @staticmethod
    def _records(value: Any) -> tuple[Mapping[str, Any], ...]:
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return tuple(item for item in value if isinstance(item, Mapping))
        return ()

    @staticmethod
    def _present(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, Mapping):
            return bool(value)
        return True

    @staticmethod
    def _number(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
