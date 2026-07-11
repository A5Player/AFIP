"""Milestone O Pack 5: deterministic Learning Stability Validation.

Validates accepted Pack 4 performance evaluations across chronological research
windows. It has no authority to tune parameters, alter trading logic, promote
knowledge, modify positions, or transmit orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from statistics import mean, pstdev
from typing import Any, Iterable, Mapping

_ALLOWED_DATASETS = {"TRAINING", "EVALUATION", "HOLDOUT"}


@dataclass(frozen=True)
class LearningStabilityValidationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    stability_validation_id: str
    performance_evaluation_ids: tuple[str, ...]
    evaluation_window_count: int
    total_sample_count: int
    dataset_roles: tuple[str, ...]
    mean_evaluation_realized_r: float
    evaluation_realized_r_stddev: float
    mean_generalization_gap_r: float
    maximum_absolute_generalization_gap_r: float
    positive_evaluation_window_rate: float
    stable_window_rate: float
    minimum_window_count_met: bool
    minimum_sample_count_met: bool
    evaluation_coverage_present: bool
    pack_4_evaluations_accepted: bool
    unique_performance_evaluations: bool
    chronology_valid: bool
    data_quality_certified: bool
    future_safe: bool
    variability_within_limit: bool
    generalization_gap_within_limit: bool
    positive_window_rate_met: bool
    stability_accepted: bool
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


class LearningStabilityValidationRuntime:
    """Validate stability across Pack 4 evaluation windows without authority."""

    def evaluate_many(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        minimum_window_count: int = 3,
        minimum_total_sample_count: int = 30,
        maximum_evaluation_r_stddev: float = 0.35,
        maximum_absolute_generalization_gap_r: float = 0.50,
        minimum_positive_window_rate: float = 0.50,
    ) -> LearningStabilityValidationReport:
        rows = [dict(row) for row in records]
        ids = tuple(sorted(str(row.get("performance_evaluation_id", "")).strip().upper() for row in rows))
        roles = tuple(sorted({role for row in rows for role in self._roles(row.get("dataset_roles", ())) }))
        timestamps = [self._integer(row.get("stability_window_timestamp", row.get("evaluation_timestamp", 0))) for row in rows]

        unique = bool(ids) and all(identifier.startswith("OPEV-") for identifier in ids) and len(ids) == len(set(ids))
        chronology = bool(rows) and all(ts > 0 for ts in timestamps) and timestamps == sorted(timestamps)
        pack_4_accepted = bool(rows) and all(bool(row.get("performance_accepted", False)) for row in rows)
        quality = bool(rows) and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = bool(rows) and all(not bool(row.get("future_leakage_detected", False)) for row in rows)
        valid_roles = bool(roles) and all(role in _ALLOWED_DATASETS for role in roles)
        evaluation_present = "EVALUATION" in roles or "HOLDOUT" in roles

        numeric_keys = (
            "total_sample_count", "evaluation_average_realized_r", "generalization_gap_r",
            "weighted_win_rate", "weighted_loss_rate", "weighted_average_confidence_score",
        )
        finite = all(isfinite(self._number(row.get(key, 0.0))) for row in rows for key in numeric_keys)
        nonnegative_samples = all(self._integer(row.get("total_sample_count", 0)) >= 0 for row in rows)
        policies_valid = all(
            str(row.get("broker", "XM")).strip().upper() == "XM"
            and str(row.get("symbol", "GOLD#")).strip().upper() == "GOLD#"
            and abs(self._number(row.get("base_lot_per_unit", 0.01)) - 0.01) <= 1e-12
            and str(row.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper() == "LOCKED_SIMULATION_ONLY"
            and str(row.get("order_status", "NO_ORDER_SENT")).strip().upper() == "NO_ORDER_SENT"
            and not bool(row.get("direct_execution", False))
            and not bool(row.get("live_execution_enabled", False))
            and not bool(row.get("automatic_parameter_update_allowed", False))
            and not bool(row.get("trading_logic_change_allowed", False))
            and not bool(row.get("production_knowledge_allowed", False))
            for row in rows
        )

        evaluation_r = [self._number(row.get("evaluation_average_realized_r", 0.0)) for row in rows]
        gaps = [self._number(row.get("generalization_gap_r", 0.0)) for row in rows]
        total_samples = sum(self._integer(row.get("total_sample_count", 0)) for row in rows)
        mean_eval_r = round(mean(evaluation_r), 8) if rows and finite else 0.0
        stddev_eval_r = round(pstdev(evaluation_r), 8) if len(evaluation_r) > 1 and finite else 0.0
        mean_gap = round(mean(gaps), 8) if rows and finite else 0.0
        max_gap = round(max((abs(value) for value in gaps), default=0.0), 8) if finite else 0.0
        positive_rate = round(sum(1 for value in evaluation_r if value > 0) / len(evaluation_r), 8) if evaluation_r and finite else 0.0

        window_stable = [
            abs(gap) <= float(maximum_absolute_generalization_gap_r)
            and value >= -float(maximum_evaluation_r_stddev)
            for value, gap in zip(evaluation_r, gaps)
        ] if finite else []
        stable_rate = round(sum(1 for value in window_stable if value) / len(window_stable), 8) if window_stable else 0.0

        minimum_windows_met = len(rows) >= max(1, int(minimum_window_count))
        minimum_samples_met = total_samples >= max(1, int(minimum_total_sample_count))
        variability_ok = stddev_eval_r <= float(maximum_evaluation_r_stddev)
        gap_ok = max_gap <= float(maximum_absolute_generalization_gap_r)
        positive_rate_ok = positive_rate >= float(minimum_positive_window_rate)

        checks = (
            (not rows, "performance_evaluation_records_required"),
            (not unique, "duplicate_or_invalid_performance_evaluation_id"),
            (not valid_roles, "dataset_role_invalid"),
            (not evaluation_present, "evaluation_dataset_required"),
            (not chronology, "chronological_order_invalid"),
            (not pack_4_accepted, "pack_4_performance_not_accepted"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not finite, "non_finite_stability_metric"),
            (not nonnegative_samples, "negative_sample_count"),
            (not minimum_windows_met, "minimum_window_count_not_met"),
            (not minimum_samples_met, "minimum_total_sample_count_not_met"),
            (not variability_ok, "evaluation_variability_limit_exceeded"),
            (not gap_ok, "generalization_gap_limit_exceeded"),
            (not positive_rate_ok, "positive_window_rate_not_met"),
            (not policies_valid, "locked_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        accepted = not blocked

        identity = {
            "ids": ids, "roles": roles, "timestamps": timestamps, "blocked": blocked,
            "minimum_window_count": int(minimum_window_count),
            "minimum_total_sample_count": int(minimum_total_sample_count),
            "maximum_evaluation_r_stddev": float(maximum_evaluation_r_stddev),
            "maximum_absolute_generalization_gap_r": float(maximum_absolute_generalization_gap_r),
            "minimum_positive_window_rate": float(minimum_positive_window_rate),
        }
        validation_id = "OSTB-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()

        if accepted:
            reason = "LEARNING_STABILITY_VALIDATED_RESEARCH_ONLY"
            en = "Accepted Pack 4 performance evaluations were stable across chronological research windows without parameter, trading, knowledge-promotion, or execution authority."
            th = "ผลประเมิน Performance จาก Pack 4 มีเสถียรภาพข้ามช่วงเวลาวิจัยตามลำดับ โดยไม่มีสิทธิ์ปรับ Parameter, Trading Logic, เลื่อน Knowledge หรือ Execution"
            next_en = "Retain the accepted stability report for Milestone O Pack 6 learning drift detection."
            next_th = "เก็บรายงานเสถียรภาพที่ผ่านสำหรับ Milestone O Pack 6 Learning Drift Detection"
        else:
            reason = "LEARNING_STABILITY_VALIDATION_BLOCKED"
            en = "Stability validation was blocked because lineage, chronology, quality, future safety, sample coverage, variability, generalization, or locked policy validation failed."
            th = "การตรวจเสถียรภาพถูกระงับเนื่องจาก Lineage, ลำดับเวลา, คุณภาพข้อมูล, Future Safety, จำนวนตัวอย่าง, ความผันผวน, Generalization หรือนโยบายล็อกไม่ผ่าน"
            next_en = "Correct the blocked research windows; do not tune parameters or promote knowledge."
            next_th = "แก้ช่วงข้อมูลวิจัยที่ถูกระงับ และห้ามปรับ Parameter หรือเลื่อนเป็น Production Knowledge"

        return LearningStabilityValidationReport(
            status="READY" if accepted else "BLOCKED", reason=reason, milestone="O", pack="5",
            stability_validation_id=validation_id, performance_evaluation_ids=ids,
            evaluation_window_count=len(rows), total_sample_count=total_samples, dataset_roles=roles,
            mean_evaluation_realized_r=mean_eval_r, evaluation_realized_r_stddev=stddev_eval_r,
            mean_generalization_gap_r=mean_gap, maximum_absolute_generalization_gap_r=max_gap,
            positive_evaluation_window_rate=positive_rate, stable_window_rate=stable_rate,
            minimum_window_count_met=minimum_windows_met, minimum_sample_count_met=minimum_samples_met,
            evaluation_coverage_present=evaluation_present, pack_4_evaluations_accepted=pack_4_accepted,
            unique_performance_evaluations=unique, chronology_valid=chronology,
            data_quality_certified=quality, future_safe=future_safe,
            variability_within_limit=variability_ok, generalization_gap_within_limit=gap_ok,
            positive_window_rate_met=positive_rate_ok, stability_accepted=accepted,
            automatic_parameter_update_allowed=False, trading_logic_change_allowed=False,
            production_knowledge_allowed=False, research_only=True, block_reasons=blocked,
            explanation_reason_en=en, explanation_reason_th=th,
            expected_next_action_en=next_en, expected_next_action_th=next_th,
        )

    @staticmethod
    def _roles(value: Any) -> tuple[str, ...]:
        if isinstance(value, str):
            value = [value]
        try:
            return tuple(str(item).strip().upper() for item in value if str(item).strip())
        except TypeError:
            return ()

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
