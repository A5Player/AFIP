"""Milestone P Pack 7: deterministic market behaviour confidence calibration.

Calibrates research confidence from accepted Pack 6 behaviour-drift reports.
The runtime is research-only and cannot update parameters, alter trading logic,
promote knowledge, modify positions, create broker requests, or transmit orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class MarketBehaviourConfidenceCalibrationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    calibration_id: str
    drift_report_ids: tuple[str, ...]
    calibration_timestamp: int
    report_count: int
    total_transition_count: int
    raw_confidence_score: float
    evidence_coverage_score: float
    persistence_stability_score: float
    regime_change_stability_score: float
    behaviour_change_stability_score: float
    stable_window_consistency_score: float
    calibrated_confidence_score: float
    confidence_band: str
    minimum_report_count_met: bool
    minimum_transition_count_met: bool
    pack_6_drift_accepted: bool
    unique_drift_reports: bool
    chronology_valid: bool
    data_quality_certified: bool
    future_safe: bool
    market_regime_before_behaviour: bool
    finite_metrics: bool
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


class MarketBehaviourConfidenceCalibrationRuntime:
    """Calibrate behaviour confidence without adaptive or execution authority."""

    def evaluate_many(
        self,
        reports: Iterable[Mapping[str, Any]],
        *,
        calibration_timestamp: int,
        minimum_report_count: int = 3,
        minimum_total_transition_count: int = 150,
        minimum_calibrated_confidence: float = 60.0,
        maximum_persistence_drift_for_full_score: float = 0.20,
        maximum_change_rate_drift_for_full_score: float = 0.25,
        maximum_stable_window_rate_drift_for_full_score: float = 0.35,
    ) -> MarketBehaviourConfidenceCalibrationReport:
        rows = [dict(row) for row in reports]
        ids = tuple(str(row.get("report_id", "")).strip().upper() for row in rows)
        source_timestamps = tuple(self._integer(row.get("detection_timestamp", 0)) for row in rows)
        calibration_ts = self._integer(calibration_timestamp)

        unique = bool(ids) and all(identifier.startswith("PBDR-") for identifier in ids) and len(ids) == len(set(ids))
        chronology = (
            bool(rows)
            and all(ts > 0 for ts in source_timestamps)
            and tuple(sorted(source_timestamps)) == source_timestamps
            and calibration_ts >= max(source_timestamps)
        )
        pack_6_accepted = bool(rows) and all(
            str(row.get("status", "")).strip().upper() == "READY"
            and str(row.get("schema_version", "")).strip().upper() == "AFIP_MARKET_BEHAVIOUR_DRIFT_DETECTION_V1"
            and not bool(row.get("drift_detected", False))
            for row in rows
        )
        quality = bool(rows) and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = bool(rows) and all(bool(row.get("future_safe", False)) for row in rows)
        regime_first = bool(rows) and all(bool(row.get("market_regime_before_behaviour", False)) for row in rows)
        policy_valid = bool(rows) and all(self._policy_valid(row) for row in rows)

        metric_keys = (
            "baseline_transition_count", "recent_transition_count",
            "persistence_drift", "regime_change_rate_drift",
            "behaviour_change_rate_drift", "stable_window_rate_drift",
        )
        finite = bool(rows) and all(isfinite(self._number(row.get(key, 0.0))) for row in rows for key in metric_keys)

        report_count = len(rows)
        total_transitions = sum(
            max(0, self._integer(row.get("baseline_transition_count", 0)))
            + max(0, self._integer(row.get("recent_transition_count", 0)))
            for row in rows
        )
        report_count_met = report_count >= max(1, self._integer(minimum_report_count))
        transition_count_met = total_transitions >= max(1, self._integer(minimum_total_transition_count))

        raw_confidence = self._raw_confidence(rows) if finite else 0.0
        coverage_score = min(100.0, 100.0 * total_transitions / max(1, self._integer(minimum_total_transition_count)))
        persistence_score = self._stability_score(rows, "persistence_drift", maximum_persistence_drift_for_full_score) if finite else 0.0
        regime_score = self._stability_score(rows, "regime_change_rate_drift", maximum_change_rate_drift_for_full_score) if finite else 0.0
        behaviour_score = self._stability_score(rows, "behaviour_change_rate_drift", maximum_change_rate_drift_for_full_score) if finite else 0.0
        stable_score = self._stability_score(rows, "stable_window_rate_drift", maximum_stable_window_rate_drift_for_full_score) if finite else 0.0

        calibrated = round(
            0.30 * raw_confidence
            + 0.20 * coverage_score
            + 0.15 * persistence_score
            + 0.125 * regime_score
            + 0.125 * behaviour_score
            + 0.10 * stable_score,
            8,
        )
        band = self._band(calibrated)

        checks = (
            (not rows, "behaviour_confidence_evidence_missing"),
            (not unique, "duplicate_or_invalid_drift_report_id"),
            (not chronology, "market_behaviour_confidence_chronology_invalid"),
            (not pack_6_accepted, "pack_6_drift_not_accepted"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not regime_first, "market_regime_not_evaluated_before_behaviour"),
            (not finite, "non_finite_behaviour_confidence_metric"),
            (not report_count_met, "minimum_report_count_not_met"),
            (not transition_count_met, "minimum_transition_count_not_met"),
            (calibrated < self._number(minimum_calibrated_confidence), "minimum_calibrated_confidence_not_met"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        accepted = not blocked

        identity = {
            "ids": ids,
            "source_timestamps": source_timestamps,
            "calibration_timestamp": calibration_ts,
            "minimum_report_count": minimum_report_count,
            "minimum_total_transition_count": minimum_total_transition_count,
            "minimum_calibrated_confidence": minimum_calibrated_confidence,
            "calibrated": calibrated,
            "blocked": blocked,
        }
        calibration_id = "PBCF-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()

        if accepted:
            reason = "MARKET_BEHAVIOUR_CONFIDENCE_CALIBRATED_RESEARCH_ONLY"
            en = "Accepted Pack 6 drift reports produced deterministic market-behaviour confidence calibration without adaptive, production, or execution authority."
            th = "รายงาน Drift จาก Pack 6 ที่ผ่านแล้วถูกใช้ปรับเทียบความเชื่อมั่นของพฤติกรรมตลาดแบบ Deterministic โดยไม่มีสิทธิ์ Adaptive, Production หรือ Execution"
        else:
            reason = "MARKET_BEHAVIOUR_CONFIDENCE_CALIBRATION_BLOCKED"
            en = "Behaviour confidence calibration was blocked by lineage, chronology, quality, coverage, confidence, metric, or frozen-policy validation."
            th = "การปรับเทียบความเชื่อมั่นของพฤติกรรมตลาดถูกระงับจาก Lineage, ลำดับเวลา, คุณภาพข้อมูล, Coverage, Confidence, Metric หรือนโยบายล็อก"

        return MarketBehaviourConfidenceCalibrationReport(
            status="READY" if accepted else "BLOCKED", reason=reason, milestone="P", pack="7",
            calibration_id=calibration_id, drift_report_ids=ids, calibration_timestamp=calibration_ts,
            report_count=report_count, total_transition_count=total_transitions,
            raw_confidence_score=raw_confidence, evidence_coverage_score=round(coverage_score, 8),
            persistence_stability_score=persistence_score, regime_change_stability_score=regime_score,
            behaviour_change_stability_score=behaviour_score, stable_window_consistency_score=stable_score,
            calibrated_confidence_score=calibrated, confidence_band=band,
            minimum_report_count_met=report_count_met, minimum_transition_count_met=transition_count_met,
            pack_6_drift_accepted=pack_6_accepted, unique_drift_reports=unique,
            chronology_valid=chronology, data_quality_certified=quality, future_safe=future_safe,
            market_regime_before_behaviour=regime_first, finite_metrics=finite,
            locked_policy_valid=policy_valid, calibration_accepted=accepted,
            immutable_record=True, research_only=True, automatic_parameter_update_allowed=False,
            trading_logic_change_allowed=False, production_knowledge_allowed=False,
            production_certification_granted=False, block_reasons=blocked,
            explanation_reason_en=en, explanation_reason_th=th,
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

    def _raw_confidence(self, rows: list[dict[str, Any]]) -> float:
        if not rows:
            return 0.0
        values = []
        for row in rows:
            max_drift = max(
                abs(self._number(row.get("persistence_drift", 0.0))) / 0.20,
                abs(self._number(row.get("regime_change_rate_drift", 0.0))) / 0.25,
                abs(self._number(row.get("behaviour_change_rate_drift", 0.0))) / 0.25,
                abs(self._number(row.get("stable_window_rate_drift", 0.0))) / 0.35,
            )
            values.append(max(0.0, 100.0 * (1.0 - min(1.0, max_drift))))
        return round(sum(values) / len(values), 8)

    def _stability_score(self, rows: list[dict[str, Any]], key: str, limit: float) -> float:
        if not rows or self._number(limit) <= 0:
            return 0.0
        mean_absolute = sum(abs(self._number(row.get(key, 0.0))) for row in rows) / len(rows)
        return round(max(0.0, 100.0 * (1.0 - min(1.0, mean_absolute / self._number(limit)))), 8)

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
        )
