"""Milestone Q Pack 7: deterministic Market Intent confidence calibration.

Calibrates research confidence from accepted Pack 6 Market Intent drift reports.
The runtime is immutable, research-only, and has no parameter, trading-logic,
position, broker, order, or production-certification authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class MarketIntentConfidenceCalibrationReport:
    calibration_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    source_drift_ids: tuple[str, ...]
    calibration_timestamp: int
    report_count: int
    total_validation_window_count: int
    raw_drift_confidence_score: float
    evidence_coverage_score: float
    persistence_consistency_score: float
    intensity_consistency_score: float
    stability_consistency_score: float
    pattern_consistency_score: float
    calibrated_confidence_score: float
    confidence_band: str
    minimum_report_count_met: bool
    minimum_validation_window_count_met: bool
    pack_6_drift_accepted: bool
    unique_drift_reports: bool
    chronology_valid: bool
    metrics_valid: bool
    data_quality_certified: bool
    future_safe: bool
    market_regime_before_intent: bool
    market_behaviour_before_intent: bool
    locked_policy_valid: bool
    calibration_accepted: bool
    immutable_record: bool
    research_only: bool
    automatic_parameter_update_allowed: bool
    trading_logic_change_allowed: bool
    production_knowledge_allowed: bool
    production_certification_granted: bool
    block_reasons: tuple[str, ...]
    explanation_reason_en: str
    explanation_reason_th: str
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


class MarketIntentConfidenceCalibrationRuntime:
    """Calibrate deterministic Market Intent confidence without authority escalation."""

    DRIFT_FULL_SCALE = 0.35
    COMPONENT_FULL_SCALE = 0.35

    def evaluate_many(
        self,
        reports: Iterable[Mapping[str, Any]],
        *,
        calibration_timestamp: int,
        minimum_report_count: int = 3,
        minimum_total_validation_window_count: int = 9,
        minimum_calibrated_confidence: float = 60.0,
    ) -> MarketIntentConfidenceCalibrationReport:
        rows = tuple(dict(item) for item in reports)
        ids = tuple(str(row.get("drift_id", "")).strip().upper() for row in rows)
        end_timestamps = tuple(self._integer(row.get("detection_end_timestamp", 0)) for row in rows)
        calibration_ts = self._integer(calibration_timestamp)

        unique = bool(rows) and all(identifier.startswith("QDRF-") for identifier in ids) and len(ids) == len(set(ids))
        chronology = (
            bool(rows)
            and all(timestamp > 0 for timestamp in end_timestamps)
            and tuple(sorted(end_timestamps)) == end_timestamps
            and len(set(end_timestamps)) == len(end_timestamps)
            and calibration_ts >= max(end_timestamps)
        )
        pack_6_accepted = bool(rows) and all(
            str(row.get("status", "")).strip().upper() == "READY"
            and str(row.get("milestone", "Q")).strip().upper() == "Q"
            and str(row.get("pack", "6")).strip() == "6"
            and not bool(row.get("drift_detected", False))
            and not bool(row.get("review_required", False))
            for row in rows
        )
        quality = bool(rows) and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = bool(rows) and all(bool(row.get("future_safe", False)) for row in rows)
        regime_first = bool(rows) and all(bool(row.get("market_regime_before_intent", False)) for row in rows)
        behaviour_first = bool(rows) and all(bool(row.get("market_behaviour_before_intent", False)) for row in rows)
        policy_valid = bool(rows) and all(self._policy_valid(row) for row in rows)

        metric_keys = (
            "drift_score", "persistence_mean_delta", "intensity_mean_delta",
            "stability_score_delta", "stable_window_ratio_delta", "pattern_consistency_delta",
        )
        metrics_valid = bool(rows) and all(
            isfinite(self._number(row.get(key, 0.0))) for row in rows for key in metric_keys
        ) and all(
            0.0 <= self._number(row.get("drift_score", 0.0)) <= 1.0
            and self._integer(row.get("validation_window_count", 0)) > 0
            for row in rows
        )

        report_count = len(rows)
        total_windows = sum(max(0, self._integer(row.get("validation_window_count", 0))) for row in rows)
        report_count_met = report_count >= max(1, self._integer(minimum_report_count))
        window_count_met = total_windows >= max(1, self._integer(minimum_total_validation_window_count))

        if metrics_valid:
            raw_confidence = self._inverse_mean_score(rows, "drift_score", self.DRIFT_FULL_SCALE)
            persistence_score = self._inverse_mean_score(rows, "persistence_mean_delta", self.COMPONENT_FULL_SCALE)
            intensity_score = self._inverse_mean_score(rows, "intensity_mean_delta", self.COMPONENT_FULL_SCALE)
            stability_score = self._combined_stability_score(rows)
            pattern_score = self._inverse_mean_score(rows, "pattern_consistency_delta", self.COMPONENT_FULL_SCALE)
        else:
            raw_confidence = persistence_score = intensity_score = stability_score = pattern_score = 0.0

        coverage_score = round(min(
            100.0,
            100.0 * total_windows / max(1, self._integer(minimum_total_validation_window_count)),
        ), 8)
        calibrated = round(
            0.35 * raw_confidence
            + 0.15 * coverage_score
            + 0.15 * persistence_score
            + 0.15 * intensity_score
            + 0.10 * stability_score
            + 0.10 * pattern_score,
            8,
        )
        band = self._band(calibrated)

        checks = (
            (not rows, "market_intent_confidence_evidence_missing"),
            (not unique, "duplicate_or_invalid_pack_6_drift_id"),
            (not chronology, "market_intent_confidence_chronology_invalid"),
            (not pack_6_accepted, "pack_6_drift_not_accepted"),
            (not metrics_valid, "market_intent_confidence_metrics_invalid"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not regime_first, "market_regime_not_evaluated_before_intent"),
            (not behaviour_first, "market_behaviour_not_evaluated_before_intent"),
            (not report_count_met, "minimum_report_count_not_met"),
            (not window_count_met, "minimum_validation_window_count_not_met"),
            (calibrated < self._number(minimum_calibrated_confidence), "minimum_calibrated_confidence_not_met"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        accepted = not blocked

        identity = {
            "ids": ids,
            "ends": end_timestamps,
            "calibration_timestamp": calibration_ts,
            "minimum_report_count": minimum_report_count,
            "minimum_total_validation_window_count": minimum_total_validation_window_count,
            "minimum_calibrated_confidence": minimum_calibrated_confidence,
            "calibrated": calibrated,
            "blocked": blocked,
        }
        calibration_id = "QCNF-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if accepted:
            reason = "MARKET_INTENT_CONFIDENCE_CALIBRATED_RESEARCH_ONLY"
            en = "Accepted Pack 6 drift reports produced deterministic Market Intent confidence calibration without adaptive, production, or execution authority."
            th = "รายงาน Drift จาก Pack 6 ที่ผ่านแล้วถูกใช้ปรับเทียบความเชื่อมั่นของ Market Intent แบบ deterministic โดยไม่มีสิทธิ์ adaptive, production หรือ execution"
        else:
            reason = "MARKET_INTENT_CONFIDENCE_CALIBRATION_BLOCKED"
            en = "Market Intent confidence calibration was blocked by lineage, chronology, drift acceptance, metrics, quality, coverage, confidence, prerequisite, or frozen-policy controls."
            th = "การปรับเทียบความเชื่อมั่นของ Market Intent ถูกระงับจาก lineage ลำดับเวลา การยอมรับ drift ค่าตัวชี้วัด คุณภาพข้อมูล coverage ความเชื่อมั่น เงื่อนไขก่อนหน้า หรือนโยบายล็อก"

        return MarketIntentConfidenceCalibrationReport(
            calibration_id=calibration_id,
            status="READY" if accepted else "BLOCKED",
            reason=reason,
            milestone="Q",
            pack="7",
            source_drift_ids=ids,
            calibration_timestamp=calibration_ts,
            report_count=report_count,
            total_validation_window_count=total_windows,
            raw_drift_confidence_score=raw_confidence,
            evidence_coverage_score=coverage_score,
            persistence_consistency_score=persistence_score,
            intensity_consistency_score=intensity_score,
            stability_consistency_score=stability_score,
            pattern_consistency_score=pattern_score,
            calibrated_confidence_score=calibrated,
            confidence_band=band,
            minimum_report_count_met=report_count_met,
            minimum_validation_window_count_met=window_count_met,
            pack_6_drift_accepted=pack_6_accepted,
            unique_drift_reports=unique,
            chronology_valid=chronology,
            metrics_valid=metrics_valid,
            data_quality_certified=quality,
            future_safe=future_safe,
            market_regime_before_intent=regime_first,
            market_behaviour_before_intent=behaviour_first,
            locked_policy_valid=policy_valid,
            calibration_accepted=accepted,
            immutable_record=True,
            research_only=True,
            automatic_parameter_update_allowed=False,
            trading_logic_change_allowed=False,
            production_knowledge_allowed=False,
            production_certification_granted=False,
            block_reasons=blocked,
            explanation_reason_en=en,
            explanation_reason_th=th,
        )

    def _inverse_mean_score(self, rows: tuple[dict[str, Any], ...], key: str, full_scale: float) -> float:
        mean_absolute = sum(abs(self._number(row.get(key, 0.0))) for row in rows) / len(rows)
        return round(max(0.0, 100.0 * (1.0 - min(1.0, mean_absolute / full_scale))), 8)

    def _combined_stability_score(self, rows: tuple[dict[str, Any], ...]) -> float:
        score_delta = self._inverse_mean_score(rows, "stability_score_delta", self.COMPONENT_FULL_SCALE)
        stable_ratio_delta = self._inverse_mean_score(rows, "stable_window_ratio_delta", self.COMPONENT_FULL_SCALE)
        return round((score_delta + stable_ratio_delta) / 2.0, 8)

    @staticmethod
    def _band(score: float) -> str:
        if score >= 85.0:
            return "HIGH"
        if score >= 70.0:
            return "MODERATE"
        if score >= 60.0:
            return "CAUTIOUS"
        return "INSUFFICIENT"

    def _policy_valid(self, row: Mapping[str, Any]) -> bool:
        return (
            str(row.get("policy_version", "")).strip().upper() == "AFIP_V1_FEATURE_FREEZE"
            and str(row.get("broker", "XM")).strip().upper() == "XM"
            and str(row.get("symbol", "GOLD#")).strip().upper() == "GOLD#"
            and abs(self._number(row.get("base_lot_per_unit", 0.01)) - 0.01) <= 1e-12
            and str(row.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper() == "LOCKED_SIMULATION_ONLY"
            and str(row.get("order_status", "NO_ORDER_SENT")).strip().upper() == "NO_ORDER_SENT"
            and not bool(row.get("direct_execution", False))
            and not bool(row.get("live_execution_enabled", False))
            and not bool(row.get("automatic_parameter_update_allowed", False))
            and not bool(row.get("trading_logic_change_allowed", False))
            and not bool(row.get("production_knowledge_allowed", False))
        )

    @staticmethod
    def _integer(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _number(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float("nan")
