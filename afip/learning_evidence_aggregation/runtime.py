"""Milestone O Pack 3: deterministic Learning Evidence Aggregation.

Aggregates only accepted Pack 2 evidence records into auditable research
statistics. The runtime has no adaptive, trading, position, broker, or order
authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable, Mapping

_ALLOWED_DATASETS = {"TRAINING", "EVALUATION", "HOLDOUT"}
_ALLOWED_OUTCOMES = {"WIN", "LOSS", "BREAKEVEN", "NO_TRADE", "REJECTED"}
_ALLOWED_DIRECTIONS = {"BUY", "SELL", "FLAT"}


@dataclass(frozen=True)
class LearningEvidenceAggregationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    aggregation_record_id: str
    evidence_record_ids: tuple[str, ...]
    dataset_role: str
    sample_count: int
    weighted_sample_count: float
    win_count: int
    loss_count: int
    breakeven_count: int
    no_trade_count: int
    rejected_count: int
    average_confidence_score: float
    average_realized_r: float
    total_realized_r: float
    average_maximum_favourable_excursion_r: float
    average_maximum_adverse_excursion_r: float
    average_cost_ratio: float
    average_duration_seconds: float
    chronology_valid: bool
    unique_evidence_records: bool
    pack_2_evidence_accepted: bool
    dataset_role_isolated: bool
    data_quality_certified: bool
    future_safe: bool
    aggregation_accepted: bool
    automatic_parameter_update_allowed: bool
    trading_logic_change_allowed: bool
    production_knowledge_allowed: bool
    research_only: bool
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
        return asdict(self)


class LearningEvidenceAggregationRuntime:
    """Aggregate normalized evidence without adaptive authority."""

    def evaluate_many(self, records: Iterable[Mapping[str, Any]]) -> LearningEvidenceAggregationReport:
        rows = [dict(row) for row in records]
        ids = tuple(sorted(str(row.get("evidence_record_id", "")).strip().upper() for row in rows))
        datasets = {str(row.get("dataset_role", "")).strip().upper() for row in rows}
        dataset_role = next(iter(datasets)) if len(datasets) == 1 else "MIXED"
        timestamps = [self._integer(row.get("observation_timestamp", 0)) for row in rows]
        chronology_valid = bool(rows) and all(ts > 0 for ts in timestamps) and timestamps == sorted(timestamps)
        unique = bool(ids) and all(identifier.startswith("OEVN-") for identifier in ids) and len(ids) == len(set(ids))
        pack_2_accepted = bool(rows) and all(bool(row.get("evidence_record_accepted", False)) for row in rows)
        data_quality = bool(rows) and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = bool(rows) and all(not bool(row.get("future_leakage_detected", False)) for row in rows)
        role_isolated = len(datasets) == 1 and dataset_role in _ALLOWED_DATASETS

        numeric_keys = (
            "confidence_score", "realized_r", "maximum_favourable_excursion_r",
            "maximum_adverse_excursion_r", "cost_ratio", "duration_seconds", "sample_weight",
        )
        finite = all(isfinite(self._number(row.get(key, 0.0))) for row in rows for key in numeric_keys)
        labels_valid = all(
            str(row.get("outcome", "")).strip().upper() in _ALLOWED_OUTCOMES
            and str(row.get("direction", "")).strip().upper() in _ALLOWED_DIRECTIONS
            for row in rows
        )
        policies_valid = all(
            str(row.get("broker", "XM")).strip().upper() == "XM"
            and str(row.get("symbol", "GOLD#")).strip().upper() == "GOLD#"
            and abs(self._number(row.get("base_lot_per_unit", 0.01)) - 0.01) <= 1e-12
            and str(row.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper() == "LOCKED_SIMULATION_ONLY"
            and str(row.get("order_status", "NO_ORDER_SENT")).strip().upper() == "NO_ORDER_SENT"
            and not bool(row.get("direct_execution", False))
            and not bool(row.get("live_execution_enabled", False))
            and not bool(row.get("automatic_parameter_update_requested", False))
            and not bool(row.get("trading_logic_change_requested", False))
            and not bool(row.get("production_knowledge_requested", False))
            for row in rows
        )

        checks = (
            (not rows, "evidence_records_required"),
            (not unique, "duplicate_or_invalid_evidence_record_id"),
            (not role_isolated, "dataset_role_contamination"),
            (not chronology_valid, "chronological_order_invalid"),
            (not pack_2_accepted, "pack_2_evidence_not_accepted"),
            (not data_quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not finite, "non_finite_aggregation_metric"),
            (not labels_valid, "financial_label_invalid"),
            (not policies_valid, "locked_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        accepted = not blocked

        outcomes = [str(row.get("outcome", "NO_TRADE")).strip().upper() for row in rows]
        weights = [self._number(row.get("sample_weight", 1.0)) for row in rows]
        weight_total = sum(weights)

        def avg(key: str) -> float:
            if not rows or weight_total <= 0:
                return 0.0
            return round(sum(self._number(row.get(key, 0.0)) * weight for row, weight in zip(rows, weights)) / weight_total, 8)

        total_r = round(sum(self._number(row.get("realized_r", 0.0)) * weight for row, weight in zip(rows, weights)), 8)
        identity = {
            "ids": ids,
            "dataset_role": dataset_role,
            "timestamps": timestamps,
            "blocked": blocked,
        }
        aggregation_id = "OEAG-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()

        if accepted:
            reason = "LEARNING_EVIDENCE_AGGREGATED_RESEARCH_ONLY"
            en = "Accepted Pack 2 evidence was aggregated into deterministic, dataset-isolated research statistics without adaptive or execution authority."
            th = "Evidence จาก Pack 2 ที่ผ่านการยอมรับถูกสรุปรวมเป็นสถิติวิจัยแบบ deterministic และแยก Dataset โดยไม่มีสิทธิ์ปรับระบบหรือ Execution"
            next_en = "Retain the accepted aggregate for Milestone O Pack 4 learning performance evaluation."
            next_th = "เก็บ Aggregate ที่ผ่านการยอมรับสำหรับ Milestone O Pack 4 Learning Performance Evaluation"
        else:
            reason = "LEARNING_EVIDENCE_AGGREGATION_BLOCKED"
            en = "Aggregation was blocked because evidence lineage, dataset isolation, chronology, data quality, future safety, schema, or locked policy validation failed."
            th = "Evidence Aggregation ถูกระงับเนื่องจาก Lineage การแยก Dataset ลำดับเวลา คุณภาพข้อมูล Future Safety Schema หรือนโยบายล็อกไม่ผ่าน"
            next_en = "Correct the blocked evidence inputs; do not tune parameters or promote knowledge."
            next_th = "แก้ Evidence Input ที่ถูกระงับ และห้ามปรับ Parameter หรือเลื่อนเป็น Production Knowledge"

        return LearningEvidenceAggregationReport(
            status="READY" if accepted else "BLOCKED", reason=reason, milestone="O", pack="3",
            aggregation_record_id=aggregation_id, evidence_record_ids=ids, dataset_role=dataset_role,
            sample_count=len(rows), weighted_sample_count=round(weight_total, 8),
            win_count=outcomes.count("WIN"), loss_count=outcomes.count("LOSS"),
            breakeven_count=outcomes.count("BREAKEVEN"), no_trade_count=outcomes.count("NO_TRADE"),
            rejected_count=outcomes.count("REJECTED"), average_confidence_score=avg("confidence_score"),
            average_realized_r=avg("realized_r"), total_realized_r=total_r,
            average_maximum_favourable_excursion_r=avg("maximum_favourable_excursion_r"),
            average_maximum_adverse_excursion_r=avg("maximum_adverse_excursion_r"),
            average_cost_ratio=avg("cost_ratio"), average_duration_seconds=avg("duration_seconds"),
            chronology_valid=chronology_valid, unique_evidence_records=unique,
            pack_2_evidence_accepted=pack_2_accepted, dataset_role_isolated=role_isolated,
            data_quality_certified=data_quality, future_safe=future_safe,
            aggregation_accepted=accepted, automatic_parameter_update_allowed=False,
            trading_logic_change_allowed=False, production_knowledge_allowed=False,
            research_only=True, block_reasons=blocked, explanation_reason_en=en,
            explanation_reason_th=th, expected_next_action_en=next_en, expected_next_action_th=next_th,
        )

    @staticmethod
    def _number(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float("nan")

    @staticmethod
    def _integer(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
