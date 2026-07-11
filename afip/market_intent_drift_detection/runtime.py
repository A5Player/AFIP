"""Milestone Q Pack 6: deterministic Market Intent drift detection.

Detects bounded change across accepted Pack 5 stability reports. This module is
immutable, research-only, and has no broker, execution, position, parameter, or
trading-logic authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class MarketIntentDriftDetectionReport:
    drift_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    source_validation_ids: tuple[str, ...]
    detection_start_timestamp: int
    detection_end_timestamp: int
    validation_window_count: int
    persistence_mean_delta: float
    intensity_mean_delta: float
    stability_score_delta: float
    stable_window_ratio_delta: float
    pattern_consistency_delta: float
    maximum_adjacent_stability_score_delta: float
    maximum_adjacent_intensity_delta: float
    drift_score: float
    drift_band: str
    drift_detected: bool
    review_required: bool
    chronology_valid: bool
    lineage_valid: bool
    metrics_valid: bool
    data_quality_certified: bool
    future_safe: bool
    market_regime_before_intent: bool
    market_behaviour_before_intent: bool
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


class MarketIntentDriftDetectionRuntime:
    """Detect deterministic drift across accepted Pack 5 reports."""

    MODERATE_DRIFT_THRESHOLD = 0.20
    HIGH_DRIFT_THRESHOLD = 0.35

    def evaluate(self, reports: Iterable[Mapping[str, Any]]) -> MarketIntentDriftDetectionReport:
        rows = tuple(dict(item) for item in reports)
        ids = tuple(str(row.get("validation_id", "")).strip().upper() for row in rows)
        starts = tuple(self._integer(row.get("validation_start_timestamp", 0)) for row in rows)
        ends = tuple(self._integer(row.get("validation_end_timestamp", 0)) for row in rows)
        persistence = tuple(self._number(row.get("weighted_persistence_mean", 0.0)) for row in rows)
        intensity = tuple(self._number(row.get("weighted_intensity_mean", 0.0)) for row in rows)
        scores = tuple(self._number(row.get("stability_score", 0.0)) for row in rows)
        stable_ratios = tuple(self._number(row.get("stable_window_ratio", 0.0)) for row in rows)
        pattern_consistency = tuple(self._number(row.get("dominant_pattern_consistency", 0.0)) for row in rows)

        enough = len(rows) >= 3
        lineage = enough and all(
            str(row.get("status", "")).strip().upper() == "READY"
            and validation_id.startswith("QSTB-")
            and str(row.get("milestone", "Q")).strip().upper() == "Q"
            and str(row.get("pack", "5")).strip() == "5"
            for row, validation_id in zip(rows, ids)
        )
        chronology = enough and len(set(ids)) == len(ids) and all(
            start > 0 and end >= start for start, end in zip(starts, ends)
        ) and all(left < right for left, right in zip(ends, starts[1:]))
        values = persistence + intensity + scores + stable_ratios + pattern_consistency
        metrics_valid = enough and all(isfinite(value) and 0.0 <= value <= 1.0 for value in values)
        quality = enough and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = enough and all(bool(row.get("future_safe", False)) for row in rows)
        regime_first = enough and all(bool(row.get("market_regime_before_intent", False)) for row in rows)
        behaviour_first = enough and all(bool(row.get("market_behaviour_before_intent", False)) for row in rows)
        policy_valid = enough and all(self._policy_valid(row) for row in rows)

        checks = (
            (not enough, "insufficient_drift_sample"),
            (not lineage, "pack_5_stability_lineage_invalid"),
            (not chronology, "drift_chronology_invalid"),
            (not metrics_valid, "drift_metrics_invalid"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not regime_first, "market_regime_not_evaluated_before_intent"),
            (not behaviour_first, "market_behaviour_not_evaluated_before_intent"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        ready = not blocked

        if ready:
            persistence_delta = self._delta(persistence)
            intensity_delta = self._delta(intensity)
            score_delta = self._delta(scores)
            stable_ratio_delta = self._delta(stable_ratios)
            pattern_delta = self._delta(pattern_consistency)
            max_score_delta = self._maximum_adjacent_delta(scores)
            max_intensity_delta = self._maximum_adjacent_delta(intensity)
            drift_score = round((
                abs(persistence_delta) + abs(intensity_delta) + abs(score_delta)
                + abs(stable_ratio_delta) + abs(pattern_delta)
                + max_score_delta + max_intensity_delta
            ) / 7.0, 6)
            if drift_score >= self.HIGH_DRIFT_THRESHOLD:
                band = "HIGH"
            elif drift_score >= self.MODERATE_DRIFT_THRESHOLD:
                band = "MODERATE"
            elif drift_score > 0.0:
                band = "LOW"
            else:
                band = "NONE"
            detected = band in {"MODERATE", "HIGH"}
            review_required = detected
        else:
            persistence_delta = intensity_delta = score_delta = 0.0
            stable_ratio_delta = pattern_delta = 0.0
            max_score_delta = max_intensity_delta = drift_score = 0.0
            band = "UNAVAILABLE"
            detected = review_required = False

        identity = {"ids": ids, "starts": starts, "ends": ends, "blocked": blocked}
        drift_id = "QDRF-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if ready and detected:
            reason = "MARKET_INTENT_DRIFT_DETECTED"
            en = "Accepted Pack 5 stability reports show deterministic Market Intent drift requiring research review."
            th = "รายงานความเสถียรจาก Pack 5 แสดง Market Intent drift แบบ deterministic และต้องได้รับการทบทวนเชิงวิจัย"
        elif ready:
            reason = "MARKET_INTENT_DRIFT_WITHIN_TOLERANCE"
            en = "Accepted Pack 5 stability reports remain within deterministic Market Intent drift tolerance."
            th = "รายงานความเสถียรจาก Pack 5 ยังอยู่ภายในขอบเขต Market Intent drift ที่ยอมรับได้แบบ deterministic"
        else:
            reason = "MARKET_INTENT_DRIFT_DETECTION_BLOCKED"
            en = "Drift detection was blocked by sample, lineage, chronology, metric, data, prerequisite, or frozen-policy controls."
            th = "การตรวจจับ Market Intent drift ถูกระงับจากการตรวจตัวอย่าง lineage ลำดับเวลา ค่าตัวชี้วัด ข้อมูล เงื่อนไขก่อนหน้า หรือนโยบายล็อก"

        return MarketIntentDriftDetectionReport(
            drift_id=drift_id,
            status="READY" if ready else "BLOCKED",
            reason=reason,
            milestone="Q",
            pack="6",
            source_validation_ids=ids,
            detection_start_timestamp=starts[0] if starts else 0,
            detection_end_timestamp=ends[-1] if ends else 0,
            validation_window_count=len(rows),
            persistence_mean_delta=persistence_delta,
            intensity_mean_delta=intensity_delta,
            stability_score_delta=score_delta,
            stable_window_ratio_delta=stable_ratio_delta,
            pattern_consistency_delta=pattern_delta,
            maximum_adjacent_stability_score_delta=max_score_delta,
            maximum_adjacent_intensity_delta=max_intensity_delta,
            drift_score=drift_score,
            drift_band=band,
            drift_detected=detected,
            review_required=review_required,
            chronology_valid=chronology,
            lineage_valid=lineage,
            metrics_valid=metrics_valid,
            data_quality_certified=quality,
            future_safe=future_safe,
            market_regime_before_intent=regime_first,
            market_behaviour_before_intent=behaviour_first,
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

    @staticmethod
    def _delta(values: tuple[float, ...]) -> float:
        return round(values[-1] - values[0], 6)

    @staticmethod
    def _maximum_adjacent_delta(values: tuple[float, ...]) -> float:
        return round(max(abs(right - left) for left, right in zip(values, values[1:])), 6)

    def _policy_valid(self, data: Mapping[str, Any]) -> bool:
        return (
            str(data.get("policy_version", "")).strip().upper() == "AFIP_V1_FEATURE_FREEZE"
            and str(data.get("broker", "XM")).strip().upper() == "XM"
            and str(data.get("symbol", "GOLD#")).strip().upper() == "GOLD#"
            and abs(self._number(data.get("base_lot_per_unit", 0.01)) - 0.01) <= 1e-12
            and str(data.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper() == "LOCKED_SIMULATION_ONLY"
            and str(data.get("order_status", "NO_ORDER_SENT")).strip().upper() == "NO_ORDER_SENT"
            and not bool(data.get("direct_execution", False))
            and not bool(data.get("live_execution_enabled", False))
            and not bool(data.get("automatic_parameter_update_allowed", False))
            and not bool(data.get("trading_logic_change_allowed", False))
            and not bool(data.get("production_knowledge_allowed", False))
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
