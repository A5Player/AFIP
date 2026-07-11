"""Milestone O Pack 1: deterministic Learning Intelligence foundation.

The runtime converts certified, chronological observations into immutable
research learning records. It does not tune models, alter trading logic,
change risk policy, create broker requests, or transmit orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping

_ALLOWED_DATASETS = {"TRAINING", "EVALUATION", "HOLDOUT"}
_ALLOWED_OUTCOMES = {"WIN", "LOSS", "BREAKEVEN", "NO_TRADE", "REJECTED"}


@dataclass(frozen=True)
class LearningIntelligenceFoundationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    learning_record_id: str
    source_record_id: str
    source_lineage_id: str
    dataset_role: str
    outcome: str
    observation_timestamp: int
    decision_timestamp: int
    chronological_order_valid: bool
    source_certified: bool
    data_quality_certified: bool
    future_safe: bool
    portfolio_intelligence_complete: bool
    immutable_learning_record: bool
    learning_record_accepted: bool
    automatic_parameter_update_allowed: bool
    trading_logic_change_allowed: bool
    production_knowledge_allowed: bool
    research_only: bool
    feature_flags: tuple[tuple[str, bool], ...]
    block_reasons: tuple[str, ...]
    explanation_reason_en: str
    explanation_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    broker: str = "XM"
    symbol: str = "GOLD#"
    base_lot_per_unit: float = 0.01
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    direct_execution: bool = False
    live_execution_enabled: bool = False
    order_status: str = "NO_ORDER_SENT"
    broker_request_created: bool = False
    order_transmission_attempted: bool = False
    position_modification_attempted: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["feature_flags"] = dict(self.feature_flags)
        return payload


class LearningIntelligenceFoundationRuntime:
    """Create auditable learning records without granting adaptive authority."""

    def evaluate_one(self, record: Mapping[str, Any]) -> LearningIntelligenceFoundationReport:
        source_record_id = str(record.get("source_record_id", "")).strip()
        source_lineage_id = str(record.get("source_lineage_id", "")).strip()
        dataset_role = str(record.get("dataset_role", "TRAINING")).strip().upper()
        outcome = str(record.get("outcome", "NO_TRADE")).strip().upper()
        observation_timestamp = self._integer(record.get("observation_timestamp", 0))
        decision_timestamp = self._integer(record.get("decision_timestamp", 0))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        base_lot = self._number(record.get("base_lot_per_unit", 0.01), 0.01)
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()

        source_certified = bool(record.get("source_certified", False))
        data_quality = bool(record.get("data_quality_certified", False))
        future_safe = not bool(record.get("future_leakage_detected", False))
        portfolio_complete = bool(record.get("portfolio_intelligence_complete", False))
        chronology_valid = decision_timestamp > 0 and observation_timestamp >= decision_timestamp
        immutable = not bool(record.get("mutable_learning_record", False))

        checks = (
            (not source_record_id, "source_record_id_required"),
            (not source_lineage_id, "source_lineage_id_required"),
            (dataset_role not in _ALLOWED_DATASETS, "dataset_role_invalid"),
            (outcome not in _ALLOWED_OUTCOMES, "outcome_invalid"),
            (not chronology_valid, "chronological_order_invalid"),
            (not source_certified, "source_not_certified"),
            (not data_quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not portfolio_complete, "portfolio_intelligence_incomplete"),
            (not immutable, "learning_record_must_be_immutable"),
            (broker != "XM", "broker_policy_violation"),
            (symbol != "GOLD#", "symbol_policy_violation"),
            (not isfinite(base_lot) or abs(base_lot - 0.01) > 1e-12, "base_unit_policy_violation"),
            (execution_status != "LOCKED_SIMULATION_ONLY", "execution_lock_invalid"),
            (order_status != "NO_ORDER_SENT", "order_status_invalid"),
            (bool(record.get("direct_execution", False)) or bool(record.get("live_execution_enabled", False)), "execution_enablement_forbidden"),
            (bool(record.get("broker_request_created", False)) or bool(record.get("order_transmission_attempted", False)), "order_transmission_forbidden"),
            (bool(record.get("position_modification_attempted", False)), "position_modification_forbidden"),
            (bool(record.get("automatic_parameter_update_requested", False)), "automatic_parameter_update_forbidden"),
            (bool(record.get("trading_logic_change_requested", False)), "trading_logic_change_forbidden"),
            (bool(record.get("production_knowledge_requested", False)), "production_knowledge_promotion_forbidden"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        accepted = not blocked

        flags = tuple(sorted({
            "learning_intelligence_foundation": accepted,
            "immutable_learning_record": accepted,
            "automatic_parameter_update_enabled": False,
            "trading_logic_change_enabled": False,
            "production_knowledge_enabled": False,
            "direct_execution_enabled": False,
            "live_execution_enabled": False,
        }.items()))
        identity = {
            "source_record_id": source_record_id,
            "source_lineage_id": source_lineage_id,
            "dataset_role": dataset_role,
            "outcome": outcome,
            "observation_timestamp": observation_timestamp,
            "decision_timestamp": decision_timestamp,
            "flags": flags,
            "blocked": blocked,
        }
        learning_record_id = "OLRN-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if accepted:
            reason = "LEARNING_RECORD_ACCEPTED_RESEARCH_ONLY"
            en = "A certified, chronological, future-safe observation was accepted as an immutable research learning record without adaptive or execution authority."
            th = "Observation ที่ผ่านการรับรอง เรียงตามเวลา และปลอดภัยจาก Future Leakage ถูกยอมรับเป็น Learning Record แบบ immutable สำหรับงานวิจัย โดยไม่มีสิทธิ์ปรับระบบหรือ Execution"
            next_en = "Retain the record for Milestone O Pack 2 evidence normalization; do not update parameters or trading logic."
            next_th = "เก็บ Record สำหรับ Milestone O Pack 2 การทำ Evidence Normalization โดยห้ามปรับ Parameter หรือ Trading Logic"
        else:
            reason = "LEARNING_RECORD_BLOCKED"
            en = "The observation was blocked because one or more lineage, chronology, integrity, policy, or safety requirements failed."
            th = "Observation ถูกระงับ เนื่องจากข้อกำหนดด้าน Lineage ลำดับเวลา ความสมบูรณ์ นโยบาย หรือความปลอดภัยไม่ผ่านอย่างน้อยหนึ่งรายการ"
            next_en = "Keep execution and adaptive updates locked, correct every block reason, and evaluate again."
            next_th = "คงการล็อก Execution และ Adaptive Update แก้ไข Block Reason ทั้งหมด แล้วประเมินอีกครั้ง"

        return LearningIntelligenceFoundationReport(
            status="READY" if accepted else "BLOCKED",
            reason=reason,
            milestone="O",
            pack="1",
            learning_record_id=learning_record_id,
            source_record_id=source_record_id,
            source_lineage_id=source_lineage_id,
            dataset_role=dataset_role,
            outcome=outcome,
            observation_timestamp=observation_timestamp,
            decision_timestamp=decision_timestamp,
            chronological_order_valid=chronology_valid,
            source_certified=source_certified,
            data_quality_certified=data_quality,
            future_safe=future_safe,
            portfolio_intelligence_complete=portfolio_complete,
            immutable_learning_record=immutable,
            learning_record_accepted=accepted,
            automatic_parameter_update_allowed=False,
            trading_logic_change_allowed=False,
            production_knowledge_allowed=False,
            research_only=True,
            feature_flags=flags,
            block_reasons=blocked,
            explanation_reason_en=en,
            explanation_reason_th=th,
            expected_next_action_en=next_en,
            expected_next_action_th=next_th,
            broker=broker,
            symbol=symbol,
            base_lot_per_unit=base_lot,
            execution_status="LOCKED_SIMULATION_ONLY",
            direct_execution=False,
            live_execution_enabled=False,
            order_status="NO_ORDER_SENT",
            broker_request_created=False,
            order_transmission_attempted=False,
            position_modification_attempted=False,
        )

    @staticmethod
    def _integer(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError, OverflowError):
            return 0

    @staticmethod
    def _number(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError, OverflowError):
            return default
