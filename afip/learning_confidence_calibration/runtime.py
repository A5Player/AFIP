"""Milestone O Pack 7: deterministic Learning Confidence Calibration.

Calibrates research confidence from accepted Pack 6 drift reports. The runtime
is evidence-only and cannot update parameters, alter trading logic, promote
knowledge, modify positions, create broker requests, or transmit orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class LearningConfidenceCalibrationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    confidence_calibration_id: str
    drift_detection_ids: tuple[str, ...]
    report_count: int
    total_sample_count: int
    raw_confidence_score: float
    evidence_coverage_score: float
    drift_stability_score: float
    generalization_stability_score: float
    positive_window_consistency_score: float
    calibrated_confidence_score: float
    confidence_band: str
    minimum_report_count_met: bool
    minimum_sample_count_met: bool
    pack_6_drift_accepted: bool
    unique_drift_reports: bool
    chronology_valid: bool
    data_quality_certified: bool
    future_safe: bool
    finite_metrics: bool
    locked_policy_valid: bool
    calibration_accepted: bool
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


class LearningConfidenceCalibrationRuntime:
    """Calibrate research confidence without adaptive or execution authority."""

    def evaluate_many(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        minimum_report_count: int = 3,
        minimum_total_sample_count: int = 120,
        minimum_calibrated_confidence: float = 60.0,
        maximum_realized_r_drift_for_full_score: float = 0.35,
        maximum_generalization_gap_drift_for_full_score: float = 0.30,
        maximum_positive_window_rate_drift_for_full_score: float = 0.35,
    ) -> LearningConfidenceCalibrationReport:
        rows = [dict(row) for row in records]
        ids = tuple(str(row.get("drift_detection_id", "")).strip().upper() for row in rows)
        timestamps = [self._integer(row.get("calibration_timestamp", row.get("drift_window_timestamp", 0))) for row in rows]

        unique = bool(ids) and all(identifier.startswith("ODRF-") for identifier in ids) and len(ids) == len(set(ids))
        chronology = bool(rows) and all(ts > 0 for ts in timestamps) and timestamps == sorted(timestamps)
        pack_6_accepted = bool(rows) and all(
            str(row.get("status", "")).strip().upper() == "READY"
            and not bool(row.get("drift_detected", False))
            for row in rows
        )
        quality = bool(rows) and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = bool(rows) and all(bool(row.get("future_safe", False)) and not bool(row.get("future_leakage_detected", False)) for row in rows)

        metric_keys = (
            "baseline_sample_count", "recent_sample_count", "raw_confidence_score",
            "realized_r_drift", "generalization_gap_drift", "positive_window_rate_drift",
        )
        finite = all(isfinite(self._number(row.get(key, 0.0))) for row in rows for key in metric_keys)
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

        report_count = len(rows)
        total_samples = sum(max(0, self._integer(row.get("baseline_sample_count", 0))) + max(0, self._integer(row.get("recent_sample_count", 0))) for row in rows)
        report_count_met = report_count >= int(minimum_report_count)
        sample_count_met = total_samples >= int(minimum_total_sample_count)

        raw_confidence = self._weighted_mean(rows, "raw_confidence_score", "recent_sample_count")
        coverage_score = min(100.0, 100.0 * total_samples / max(1, int(minimum_total_sample_count)))
        drift_score = self._stability_score(rows, "realized_r_drift", maximum_realized_r_drift_for_full_score)
        gap_score = self._stability_score(rows, "generalization_gap_drift", maximum_generalization_gap_drift_for_full_score)
        positive_score = self._stability_score(rows, "positive_window_rate_drift", maximum_positive_window_rate_drift_for_full_score)

        calibrated = round(
            0.40 * raw_confidence
            + 0.20 * coverage_score
            + 0.15 * drift_score
            + 0.15 * gap_score
            + 0.10 * positive_score,
            8,
        )
        band = self._band(calibrated)

        checks = (
            (not rows, "confidence_evidence_missing"),
            (not unique, "duplicate_or_invalid_drift_detection_id"),
            (not chronology, "chronological_order_invalid"),
            (not pack_6_accepted, "pack_6_drift_not_accepted"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not finite, "non_finite_confidence_metric"),
            (not report_count_met, "minimum_report_count_not_met"),
            (not sample_count_met, "minimum_sample_count_not_met"),
            (calibrated < float(minimum_calibrated_confidence), "minimum_calibrated_confidence_not_met"),
            (not policies_valid, "locked_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        accepted = not blocked

        identity = {
            "ids": ids, "timestamps": timestamps, "blocked": blocked,
            "minimum_report_count": int(minimum_report_count),
            "minimum_total_sample_count": int(minimum_total_sample_count),
            "minimum_calibrated_confidence": float(minimum_calibrated_confidence),
            "calibrated_confidence_score": calibrated,
        }
        calibration_id = "OCAL-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()

        if accepted:
            reason = "LEARNING_CONFIDENCE_CALIBRATED_RESEARCH_ONLY"
            en = "Accepted Pack 6 drift evidence produced a deterministic research confidence calibration without adaptive, knowledge-promotion, or execution authority."
            th = "หลักฐาน Drift จาก Pack 6 ที่ผ่านแล้วถูกใช้ปรับเทียบความเชื่อมั่นเชิงวิจัยแบบ Deterministic โดยไม่มีสิทธิ์ Adaptive, เลื่อน Knowledge หรือ Execution"
            next_en = "Retain the accepted calibration for Milestone O Pack 8 learning validation governance."
            next_th = "เก็บผล Calibration ที่ผ่านสำหรับ Milestone O Pack 8 Learning Validation Governance"
        else:
            reason = "LEARNING_CONFIDENCE_CALIBRATION_BLOCKED"
            en = "Confidence calibration was blocked because lineage, chronology, quality, future safety, coverage, confidence, or locked policy validation failed."
            th = "การปรับเทียบความเชื่อมั่นถูกระงับเนื่องจาก Lineage, ลำดับเวลา, คุณภาพข้อมูล, Future Safety, Coverage, Confidence หรือนโยบายล็อกไม่ผ่าน"
            next_en = "Investigate the blocked research evidence; do not tune parameters or promote knowledge automatically."
            next_th = "ตรวจสอบหลักฐานวิจัยที่ถูกระงับ และห้ามปรับ Parameter หรือเลื่อน Knowledge อัตโนมัติ"

        return LearningConfidenceCalibrationReport(
            status="READY" if accepted else "BLOCKED", reason=reason, milestone="O", pack="7",
            confidence_calibration_id=calibration_id, drift_detection_ids=ids,
            report_count=report_count, total_sample_count=total_samples,
            raw_confidence_score=raw_confidence, evidence_coverage_score=round(coverage_score, 8),
            drift_stability_score=drift_score, generalization_stability_score=gap_score,
            positive_window_consistency_score=positive_score,
            calibrated_confidence_score=calibrated, confidence_band=band,
            minimum_report_count_met=report_count_met, minimum_sample_count_met=sample_count_met,
            pack_6_drift_accepted=pack_6_accepted, unique_drift_reports=unique,
            chronology_valid=chronology, data_quality_certified=quality, future_safe=future_safe,
            finite_metrics=finite, locked_policy_valid=policies_valid, calibration_accepted=accepted,
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

    def _weighted_mean(self, rows: list[dict[str, Any]], value_key: str, weight_key: str) -> float:
        weighted = 0.0
        weight_total = 0.0
        for row in rows:
            value = self._number(row.get(value_key, 0.0))
            weight = max(0.0, self._number(row.get(weight_key, 0.0)))
            weighted += value * weight
            weight_total += weight
        return round(weighted / weight_total, 8) if weight_total > 0 else 0.0

    def _stability_score(self, rows: list[dict[str, Any]], key: str, limit: float) -> float:
        if not rows or float(limit) <= 0:
            return 0.0
        mean_absolute = sum(abs(self._number(row.get(key, 0.0))) for row in rows) / len(rows)
        return round(max(0.0, 100.0 * (1.0 - min(1.0, mean_absolute / float(limit)))), 8)

    @staticmethod
    def _band(score: float) -> str:
        if score >= 85.0:
            return "HIGH"
        if score >= 70.0:
            return "MODERATE"
        if score >= 60.0:
            return "CAUTIOUS"
        return "INSUFFICIENT"
