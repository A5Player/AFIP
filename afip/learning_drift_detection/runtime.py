"""Milestone O Pack 6: deterministic Learning Drift Detection.

Compares accepted Pack 5 stability windows against a certified baseline and
recent research window. The runtime is research-only and has no authority to
update parameters, alter trading logic, promote knowledge, modify positions,
or transmit orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class LearningDriftDetectionReport:
    status: str
    reason: str
    milestone: str
    pack: str
    drift_detection_id: str
    stability_validation_ids: tuple[str, ...]
    baseline_window_count: int
    recent_window_count: int
    baseline_sample_count: int
    recent_sample_count: int
    baseline_mean_realized_r: float
    recent_mean_realized_r: float
    realized_r_drift: float
    baseline_mean_generalization_gap_r: float
    recent_mean_generalization_gap_r: float
    generalization_gap_drift: float
    baseline_positive_window_rate: float
    recent_positive_window_rate: float
    positive_window_rate_drift: float
    baseline_coverage_met: bool
    recent_coverage_met: bool
    pack_5_stability_accepted: bool
    unique_stability_validations: bool
    chronology_valid: bool
    data_quality_certified: bool
    future_safe: bool
    realized_r_drift_within_limit: bool
    generalization_gap_drift_within_limit: bool
    positive_window_rate_drift_within_limit: bool
    drift_detected: bool
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


class LearningDriftDetectionRuntime:
    """Detect research drift without adaptive or execution authority."""

    def evaluate_many(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        baseline_window_count: int = 3,
        recent_window_count: int = 3,
        minimum_samples_per_segment: int = 30,
        maximum_absolute_realized_r_drift: float = 0.35,
        maximum_absolute_generalization_gap_drift: float = 0.30,
        maximum_absolute_positive_window_rate_drift: float = 0.35,
    ) -> LearningDriftDetectionReport:
        rows = [dict(row) for row in records]
        ids = tuple(str(row.get("stability_validation_id", "")).strip().upper() for row in rows)
        timestamps = [self._integer(row.get("drift_window_timestamp", row.get("stability_window_timestamp", 0))) for row in rows]

        base_n = max(1, int(baseline_window_count))
        recent_n = max(1, int(recent_window_count))
        required = base_n + recent_n
        baseline = rows[:base_n]
        recent = rows[-recent_n:] if len(rows) >= recent_n else []

        unique = bool(ids) and all(identifier.startswith("OSTB-") for identifier in ids) and len(ids) == len(set(ids))
        chronology = bool(rows) and all(ts > 0 for ts in timestamps) and timestamps == sorted(timestamps)
        pack_5_accepted = bool(rows) and all(bool(row.get("stability_accepted", False)) for row in rows)
        quality = bool(rows) and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = bool(rows) and all(not bool(row.get("future_leakage_detected", False)) for row in rows)
        finite = all(isfinite(self._number(row.get(key, 0.0))) for row in rows for key in (
            "total_sample_count", "mean_evaluation_realized_r", "mean_generalization_gap_r", "positive_evaluation_window_rate"
        ))
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

        baseline_samples = sum(max(0, self._integer(row.get("total_sample_count", 0))) for row in baseline)
        recent_samples = sum(max(0, self._integer(row.get("total_sample_count", 0))) for row in recent)
        baseline_coverage = len(baseline) == base_n and baseline_samples >= int(minimum_samples_per_segment)
        recent_coverage = len(recent) == recent_n and recent_samples >= int(minimum_samples_per_segment)

        base_r = self._mean(baseline, "mean_evaluation_realized_r")
        recent_r = self._mean(recent, "mean_evaluation_realized_r")
        r_drift = round(recent_r - base_r, 8)
        base_gap = self._mean(baseline, "mean_generalization_gap_r")
        recent_gap = self._mean(recent, "mean_generalization_gap_r")
        gap_drift = round(recent_gap - base_gap, 8)
        base_positive = self._mean(baseline, "positive_evaluation_window_rate")
        recent_positive = self._mean(recent, "positive_evaluation_window_rate")
        positive_drift = round(recent_positive - base_positive, 8)

        r_ok = abs(r_drift) <= float(maximum_absolute_realized_r_drift)
        gap_ok = abs(gap_drift) <= float(maximum_absolute_generalization_gap_drift)
        positive_ok = abs(positive_drift) <= float(maximum_absolute_positive_window_rate_drift)

        checks = (
            (len(rows) < required, "insufficient_drift_window_count"),
            (not unique, "duplicate_or_invalid_stability_validation_id"),
            (not chronology, "chronological_order_invalid"),
            (not pack_5_accepted, "pack_5_stability_not_accepted"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not finite, "non_finite_drift_metric"),
            (not baseline_coverage, "baseline_coverage_not_met"),
            (not recent_coverage, "recent_coverage_not_met"),
            (not r_ok, "realized_r_drift_limit_exceeded"),
            (not gap_ok, "generalization_gap_drift_limit_exceeded"),
            (not positive_ok, "positive_window_rate_drift_limit_exceeded"),
            (not policies_valid, "locked_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        drift_detected = any(reason.endswith("drift_limit_exceeded") for reason in blocked)
        accepted = not blocked

        identity = {
            "ids": ids, "timestamps": timestamps, "blocked": blocked,
            "baseline_window_count": base_n, "recent_window_count": recent_n,
            "minimum_samples_per_segment": int(minimum_samples_per_segment),
            "maximum_absolute_realized_r_drift": float(maximum_absolute_realized_r_drift),
            "maximum_absolute_generalization_gap_drift": float(maximum_absolute_generalization_gap_drift),
            "maximum_absolute_positive_window_rate_drift": float(maximum_absolute_positive_window_rate_drift),
        }
        detection_id = "ODRF-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()

        if accepted:
            reason = "LEARNING_DRIFT_NOT_DETECTED_RESEARCH_ONLY"
            en = "Accepted Pack 5 stability windows remained within certified drift limits without adaptive, knowledge-promotion, or execution authority."
            th = "ช่วงข้อมูลเสถียรภาพจาก Pack 5 อยู่ภายในเพดาน Drift ที่รับรอง โดยไม่มีสิทธิ์ Adaptive, เลื่อน Knowledge หรือ Execution"
            next_en = "Retain the accepted drift report for Milestone O Pack 7 learning confidence calibration."
            next_th = "เก็บรายงาน Drift ที่ผ่านสำหรับ Milestone O Pack 7 Learning Confidence Calibration"
        else:
            reason = "LEARNING_DRIFT_DETECTION_BLOCKED"
            en = "Drift validation was blocked because lineage, chronology, quality, future safety, coverage, drift limits, or locked policy validation failed."
            th = "การตรวจ Drift ถูกระงับเนื่องจาก Lineage, ลำดับเวลา, คุณภาพข้อมูล, Future Safety, Coverage, เพดาน Drift หรือนโยบายล็อกไม่ผ่าน"
            next_en = "Investigate the blocked research evidence; do not tune parameters or promote knowledge automatically."
            next_th = "ตรวจสอบหลักฐานวิจัยที่ถูกระงับ และห้ามปรับ Parameter หรือเลื่อน Knowledge อัตโนมัติ"

        return LearningDriftDetectionReport(
            status="READY" if accepted else "BLOCKED", reason=reason, milestone="O", pack="6",
            drift_detection_id=detection_id, stability_validation_ids=ids,
            baseline_window_count=len(baseline), recent_window_count=len(recent),
            baseline_sample_count=baseline_samples, recent_sample_count=recent_samples,
            baseline_mean_realized_r=base_r, recent_mean_realized_r=recent_r, realized_r_drift=r_drift,
            baseline_mean_generalization_gap_r=base_gap, recent_mean_generalization_gap_r=recent_gap,
            generalization_gap_drift=gap_drift, baseline_positive_window_rate=base_positive,
            recent_positive_window_rate=recent_positive, positive_window_rate_drift=positive_drift,
            baseline_coverage_met=baseline_coverage, recent_coverage_met=recent_coverage,
            pack_5_stability_accepted=pack_5_accepted, unique_stability_validations=unique,
            chronology_valid=chronology, data_quality_certified=quality, future_safe=future_safe,
            realized_r_drift_within_limit=r_ok, generalization_gap_drift_within_limit=gap_ok,
            positive_window_rate_drift_within_limit=positive_ok, drift_detected=drift_detected,
            automatic_parameter_update_allowed=False, trading_logic_change_allowed=False,
            production_knowledge_allowed=False, research_only=True, block_reasons=blocked,
            explanation_reason_en=en, explanation_reason_th=th,
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

    def _mean(self, rows: list[dict[str, Any]], key: str) -> float:
        if not rows:
            return 0.0
        values = [self._number(row.get(key, 0.0)) for row in rows]
        return round(sum(values) / len(values), 8)
