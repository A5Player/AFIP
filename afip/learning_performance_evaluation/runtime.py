"""Milestone O Pack 4: deterministic Learning Performance Evaluation.

Evaluates accepted Pack 3 aggregate records as research evidence. It does not
modify parameters, trading logic, knowledge status, positions, or orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable, Mapping

_ALLOWED_DATASETS = {"TRAINING", "EVALUATION", "HOLDOUT"}


@dataclass(frozen=True)
class LearningPerformanceEvaluationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    performance_evaluation_id: str
    aggregation_record_ids: tuple[str, ...]
    dataset_roles: tuple[str, ...]
    aggregate_count: int
    total_sample_count: int
    total_weighted_sample_count: float
    weighted_win_rate: float
    weighted_loss_rate: float
    weighted_breakeven_rate: float
    weighted_average_confidence_score: float
    weighted_average_realized_r: float
    total_realized_r: float
    average_payoff_ratio: float
    training_average_realized_r: float
    evaluation_average_realized_r: float
    generalization_gap_r: float
    minimum_sample_count_met: bool
    evaluation_dataset_present: bool
    pack_3_aggregates_accepted: bool
    unique_aggregation_records: bool
    chronology_valid: bool
    data_quality_certified: bool
    future_safe: bool
    performance_accepted: bool
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


class LearningPerformanceEvaluationRuntime:
    """Evaluate learning aggregates without adaptive or execution authority."""

    def evaluate_many(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        minimum_sample_count: int = 2,
    ) -> LearningPerformanceEvaluationReport:
        rows = [dict(row) for row in records]
        ids = tuple(sorted(str(row.get("aggregation_record_id", "")).strip().upper() for row in rows))
        roles = tuple(sorted({str(row.get("dataset_role", "")).strip().upper() for row in rows}))
        timestamps = [self._integer(row.get("evaluation_timestamp", row.get("observation_end_timestamp", 0))) for row in rows]

        unique = bool(ids) and all(identifier.startswith("OEAG-") for identifier in ids) and len(ids) == len(set(ids))
        chronology = bool(rows) and all(ts > 0 for ts in timestamps) and timestamps == sorted(timestamps)
        pack_3_accepted = bool(rows) and all(bool(row.get("aggregation_accepted", False)) for row in rows)
        quality = bool(rows) and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = bool(rows) and all(not bool(row.get("future_leakage_detected", False)) for row in rows)
        valid_roles = bool(roles) and all(role in _ALLOWED_DATASETS for role in roles)
        evaluation_present = "EVALUATION" in roles or "HOLDOUT" in roles

        numeric_keys = (
            "sample_count", "weighted_sample_count", "win_count", "loss_count", "breakeven_count",
            "average_confidence_score", "average_realized_r", "total_realized_r",
        )
        finite = all(isfinite(self._number(row.get(key, 0.0))) for row in rows for key in numeric_keys)
        nonnegative_counts = all(
            self._number(row.get(key, 0.0)) >= 0
            for row in rows
            for key in ("sample_count", "weighted_sample_count", "win_count", "loss_count", "breakeven_count")
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

        total_samples = sum(self._integer(row.get("sample_count", 0)) for row in rows)
        total_weight = sum(self._number(row.get("weighted_sample_count", 0.0)) for row in rows)
        minimum_met = total_samples >= max(1, int(minimum_sample_count))

        def weighted_average(key: str) -> float:
            if total_weight <= 0:
                return 0.0
            return round(sum(self._number(row.get(key, 0.0)) * self._number(row.get("weighted_sample_count", 0.0)) for row in rows) / total_weight, 8)

        wins = sum(self._number(row.get("win_count", 0.0)) for row in rows)
        losses = sum(self._number(row.get("loss_count", 0.0)) for row in rows)
        breakeven = sum(self._number(row.get("breakeven_count", 0.0)) for row in rows)
        resolved = wins + losses + breakeven
        win_rate = round(wins / resolved, 8) if resolved > 0 else 0.0
        loss_rate = round(losses / resolved, 8) if resolved > 0 else 0.0
        breakeven_rate = round(breakeven / resolved, 8) if resolved > 0 else 0.0
        total_r = round(sum(self._number(row.get("total_realized_r", 0.0)) for row in rows), 8)

        positive_r = sum(max(0.0, self._number(row.get("total_realized_r", 0.0))) for row in rows)
        negative_r = abs(sum(min(0.0, self._number(row.get("total_realized_r", 0.0))) for row in rows))
        payoff = round(positive_r / negative_r, 8) if negative_r > 0 else (round(positive_r, 8) if positive_r > 0 else 0.0)

        def role_average(target_roles: set[str]) -> float:
            selected = [row for row in rows if str(row.get("dataset_role", "")).strip().upper() in target_roles]
            weight = sum(self._number(row.get("weighted_sample_count", 0.0)) for row in selected)
            if weight <= 0:
                return 0.0
            return round(sum(self._number(row.get("average_realized_r", 0.0)) * self._number(row.get("weighted_sample_count", 0.0)) for row in selected) / weight, 8)

        training_r = role_average({"TRAINING"})
        evaluation_r = role_average({"EVALUATION", "HOLDOUT"})
        gap = round(training_r - evaluation_r, 8)

        checks = (
            (not rows, "aggregation_records_required"),
            (not unique, "duplicate_or_invalid_aggregation_record_id"),
            (not valid_roles, "dataset_role_invalid"),
            (not evaluation_present, "evaluation_dataset_required"),
            (not chronology, "chronological_order_invalid"),
            (not pack_3_accepted, "pack_3_aggregate_not_accepted"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not finite, "non_finite_performance_metric"),
            (not nonnegative_counts, "negative_sample_count"),
            (total_weight <= 0, "weighted_sample_count_required"),
            (not minimum_met, "minimum_sample_count_not_met"),
            (not policies_valid, "locked_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        accepted = not blocked

        identity = {"ids": ids, "roles": roles, "timestamps": timestamps, "blocked": blocked, "minimum": int(minimum_sample_count)}
        evaluation_id = "OPEV-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()

        if accepted:
            reason = "LEARNING_PERFORMANCE_EVALUATED_RESEARCH_ONLY"
            en = "Accepted Pack 3 aggregates were evaluated across isolated research datasets without parameter, trading, knowledge-promotion, or execution authority."
            th = "Aggregate จาก Pack 3 ที่ผ่านการยอมรับถูกประเมินข้าม Dataset วิจัยที่แยกกัน โดยไม่มีสิทธิ์ปรับ Parameter, Trading Logic, เลื่อน Knowledge หรือ Execution"
            next_en = "Retain the accepted evaluation for Milestone O Pack 5 learning stability validation."
            next_th = "เก็บผลประเมินที่ผ่านการยอมรับสำหรับ Milestone O Pack 5 Learning Stability Validation"
        else:
            reason = "LEARNING_PERFORMANCE_EVALUATION_BLOCKED"
            en = "Performance evaluation was blocked because aggregate lineage, dataset coverage, chronology, quality, future safety, sample sufficiency, schema, or locked policy validation failed."
            th = "การประเมิน Performance ถูกระงับเนื่องจาก Lineage, Dataset Coverage, ลำดับเวลา, คุณภาพข้อมูล, Future Safety, จำนวนตัวอย่าง, Schema หรือนโยบายล็อกไม่ผ่าน"
            next_en = "Correct the blocked aggregate inputs; do not tune parameters or promote knowledge."
            next_th = "แก้ Aggregate Input ที่ถูกระงับ และห้ามปรับ Parameter หรือเลื่อนเป็น Production Knowledge"

        return LearningPerformanceEvaluationReport(
            status="READY" if accepted else "BLOCKED", reason=reason, milestone="O", pack="4",
            performance_evaluation_id=evaluation_id, aggregation_record_ids=ids, dataset_roles=roles,
            aggregate_count=len(rows), total_sample_count=total_samples,
            total_weighted_sample_count=round(total_weight, 8), weighted_win_rate=win_rate,
            weighted_loss_rate=loss_rate, weighted_breakeven_rate=breakeven_rate,
            weighted_average_confidence_score=weighted_average("average_confidence_score"),
            weighted_average_realized_r=weighted_average("average_realized_r"), total_realized_r=total_r,
            average_payoff_ratio=payoff, training_average_realized_r=training_r,
            evaluation_average_realized_r=evaluation_r, generalization_gap_r=gap,
            minimum_sample_count_met=minimum_met, evaluation_dataset_present=evaluation_present,
            pack_3_aggregates_accepted=pack_3_accepted, unique_aggregation_records=unique,
            chronology_valid=chronology, data_quality_certified=quality, future_safe=future_safe,
            performance_accepted=accepted, automatic_parameter_update_allowed=False,
            trading_logic_change_allowed=False, production_knowledge_allowed=False, research_only=True,
            block_reasons=blocked, explanation_reason_en=en, explanation_reason_th=th,
            expected_next_action_en=next_en, expected_next_action_th=next_th,
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
