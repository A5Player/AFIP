"""Milestone O Pack 2: deterministic Learning Evidence Normalization.

The runtime converts an accepted immutable Pack 1 learning record into a
canonical, auditable research evidence record. It validates lineage, dataset
separation, chronology, finite numeric values, bounded ratios, and normalized
financial labels. It never tunes parameters, changes trading logic, modifies
positions, creates broker requests, or transmits orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping

_ALLOWED_DATASETS = {"TRAINING", "EVALUATION", "HOLDOUT"}
_ALLOWED_OUTCOMES = {"WIN", "LOSS", "BREAKEVEN", "NO_TRADE", "REJECTED"}
_ALLOWED_DIRECTIONS = {"BUY", "SELL", "FLAT"}
_ALLOWED_REGIMES = {
    "TRENDING_BULLISH",
    "TRENDING_BEARISH",
    "RANGING",
    "HIGH_VOLATILITY",
    "LOW_VOLATILITY",
    "TRANSITION",
    "UNKNOWN",
}


@dataclass(frozen=True)
class LearningEvidenceNormalizationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    evidence_record_id: str
    learning_record_id: str
    source_lineage_id: str
    dataset_role: str
    outcome: str
    direction: str
    market_regime: str
    decision_timestamp: int
    observation_timestamp: int
    confidence_score: float
    realized_r: float
    maximum_favourable_excursion_r: float
    maximum_adverse_excursion_r: float
    cost_ratio: float
    duration_seconds: int
    sample_weight: float
    chronology_valid: bool
    pack_1_record_accepted: bool
    immutable_learning_record: bool
    data_quality_certified: bool
    future_safe: bool
    evidence_schema_valid: bool
    evidence_record_accepted: bool
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


class LearningEvidenceNormalizationRuntime:
    """Normalize certified learning evidence without adaptive authority."""

    def evaluate_one(self, record: Mapping[str, Any]) -> LearningEvidenceNormalizationReport:
        learning_record_id = str(record.get("learning_record_id", "")).strip().upper()
        source_lineage_id = str(record.get("source_lineage_id", "")).strip().upper()
        dataset_role = str(record.get("dataset_role", "TRAINING")).strip().upper()
        outcome = str(record.get("outcome", "NO_TRADE")).strip().upper()
        direction = str(record.get("direction", "FLAT")).strip().upper()
        market_regime = str(record.get("market_regime", "UNKNOWN")).strip().upper()
        decision_timestamp = self._integer(record.get("decision_timestamp", 0))
        observation_timestamp = self._integer(record.get("observation_timestamp", 0))
        duration_seconds = self._integer(record.get("duration_seconds", 0))

        confidence = self._number(record.get("confidence_score", 0.0))
        realized_r = self._number(record.get("realized_r", 0.0))
        mfe_r = self._number(record.get("maximum_favourable_excursion_r", 0.0))
        mae_r = self._number(record.get("maximum_adverse_excursion_r", 0.0))
        cost_ratio = self._number(record.get("cost_ratio", 0.0))
        sample_weight = self._number(record.get("sample_weight", 1.0))

        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        base_lot = self._number(record.get("base_lot_per_unit", 0.01), 0.01)
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()

        pack_1_accepted = bool(record.get("learning_record_accepted", False))
        immutable = bool(record.get("immutable_learning_record", False))
        data_quality = bool(record.get("data_quality_certified", False))
        future_safe = not bool(record.get("future_leakage_detected", False))
        chronology_valid = decision_timestamp > 0 and observation_timestamp >= decision_timestamp

        finite_metrics = all(isfinite(value) for value in (confidence, realized_r, mfe_r, mae_r, cost_ratio, sample_weight, base_lot))
        metrics_in_range = (
            0.0 <= confidence <= 100.0
            and mfe_r >= 0.0
            and mae_r <= 0.0
            and 0.0 <= cost_ratio <= 1.0
            and 0.0 < sample_weight <= 1.0
            and duration_seconds >= 0
        )

        checks = (
            (not learning_record_id.startswith("OLRN-"), "learning_record_id_invalid"),
            (not source_lineage_id, "source_lineage_id_required"),
            (dataset_role not in _ALLOWED_DATASETS, "dataset_role_invalid"),
            (outcome not in _ALLOWED_OUTCOMES, "outcome_invalid"),
            (direction not in _ALLOWED_DIRECTIONS, "direction_invalid"),
            (market_regime not in _ALLOWED_REGIMES, "market_regime_invalid"),
            (not chronology_valid, "chronological_order_invalid"),
            (not pack_1_accepted, "pack_1_learning_record_not_accepted"),
            (not immutable, "learning_record_not_immutable"),
            (not data_quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not finite_metrics, "non_finite_evidence_metric"),
            (not metrics_in_range, "evidence_metric_out_of_range"),
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

        normalized = {
            "learning_record_id": learning_record_id,
            "source_lineage_id": source_lineage_id,
            "dataset_role": dataset_role,
            "outcome": outcome,
            "direction": direction,
            "market_regime": market_regime,
            "decision_timestamp": decision_timestamp,
            "observation_timestamp": observation_timestamp,
            "confidence_score": self._quantize(confidence),
            "realized_r": self._quantize(realized_r),
            "maximum_favourable_excursion_r": self._quantize(mfe_r),
            "maximum_adverse_excursion_r": self._quantize(mae_r),
            "cost_ratio": self._quantize(cost_ratio),
            "duration_seconds": duration_seconds,
            "sample_weight": self._quantize(sample_weight),
            "blocked": blocked,
        }
        evidence_record_id = "OEVN-" + sha256(
            json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        flags = tuple(sorted({
            "learning_evidence_normalization": accepted,
            "canonical_evidence_schema": accepted,
            "dataset_role_separation": dataset_role in _ALLOWED_DATASETS,
            "automatic_parameter_update_enabled": False,
            "trading_logic_change_enabled": False,
            "production_knowledge_enabled": False,
            "direct_execution_enabled": False,
            "live_execution_enabled": False,
        }.items()))

        if accepted:
            reason = "LEARNING_EVIDENCE_NORMALIZED_RESEARCH_ONLY"
            en = "The accepted immutable learning record was normalized into a canonical, finite, bounded, chronological research evidence record without adaptive or execution authority."
            th = "Learning Record แบบ immutable ที่ผ่านการยอมรับ ถูกทำให้เป็น Evidence Record มาตรฐาน ซึ่งมีค่าจำกัด ตรวจสอบลำดับเวลา และใช้เพื่อการวิจัยเท่านั้น โดยไม่มีสิทธิ์ปรับระบบหรือ Execution"
            next_en = "Retain the normalized evidence for Milestone O Pack 3 evidence aggregation; keep dataset roles isolated."
            next_th = "เก็บ Evidence ที่ผ่าน Normalization สำหรับ Milestone O Pack 3 Evidence Aggregation และคงการแยก Dataset Role"
        else:
            reason = "LEARNING_EVIDENCE_NORMALIZATION_BLOCKED"
            en = "Evidence normalization was blocked because lineage, chronology, schema, metric, policy, or safety validation failed."
            th = "Evidence Normalization ถูกระงับ เนื่องจาก Lineage ลำดับเวลา Schema ค่า Metric นโยบาย หรือข้อกำหนดความปลอดภัยไม่ผ่าน"
            next_en = "Keep adaptive and execution authority locked, correct every block reason, and normalize again."
            next_th = "คงการล็อก Adaptive และ Execution แก้ไข Block Reason ทั้งหมด แล้วทำ Normalization ใหม่"

        return LearningEvidenceNormalizationReport(
            status="READY" if accepted else "BLOCKED",
            reason=reason,
            milestone="O",
            pack="2",
            evidence_record_id=evidence_record_id,
            learning_record_id=learning_record_id,
            source_lineage_id=source_lineage_id,
            dataset_role=dataset_role,
            outcome=outcome,
            direction=direction,
            market_regime=market_regime,
            decision_timestamp=decision_timestamp,
            observation_timestamp=observation_timestamp,
            confidence_score=self._quantize(confidence),
            realized_r=self._quantize(realized_r),
            maximum_favourable_excursion_r=self._quantize(mfe_r),
            maximum_adverse_excursion_r=self._quantize(mae_r),
            cost_ratio=self._quantize(cost_ratio),
            duration_seconds=duration_seconds,
            sample_weight=self._quantize(sample_weight),
            chronology_valid=chronology_valid,
            pack_1_record_accepted=pack_1_accepted,
            immutable_learning_record=immutable,
            data_quality_certified=data_quality,
            future_safe=future_safe,
            evidence_schema_valid=finite_metrics and metrics_in_range,
            evidence_record_accepted=accepted,
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
    def _number(value: Any, default: float = float("nan")) -> float:
        try:
            return float(value)
        except (TypeError, ValueError, OverflowError):
            return default

    @staticmethod
    def _quantize(value: float) -> float:
        if not isfinite(value):
            return value
        try:
            return float(Decimal(str(value)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN))
        except (InvalidOperation, ValueError):
            return value
