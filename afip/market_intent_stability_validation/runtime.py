"""Milestone Q Pack 5: deterministic Market Intent stability validation.

Validates the stability of accepted Pack 4 Market Intent statistics across
strictly ordered research windows. This module has no execution, broker,
position, parameter, or trading-logic authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class MarketIntentStabilityValidationReport:
    validation_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    source_statistics_ids: tuple[str, ...]
    validation_start_timestamp: int
    validation_end_timestamp: int
    statistics_window_count: int
    total_sequence_count: int
    total_transition_count: int
    weighted_persistence_mean: float
    weighted_intensity_mean: float
    persistence_range: float
    intensity_range: float
    intent_change_rate_range: float
    direction_change_rate_range: float
    regime_change_rate_range: float
    behaviour_change_rate_range: float
    dominant_pattern_consistency: float
    stable_window_ratio: float
    stability_score: float
    stability_band: str
    chronology_valid: bool
    lineage_valid: bool
    metrics_valid: bool
    stability_thresholds_valid: bool
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


class MarketIntentStabilityValidationRuntime:
    """Validate stability across accepted Pack 4 statistical windows."""

    PATTERNS = {
        "PERSISTENT_INTENT",
        "INTENT_REVERSAL_SEQUENCE",
        "BREAKOUT_DEVELOPMENT_SEQUENCE",
        "LIQUIDITY_SEEKING_SEQUENCE",
        "OSCILLATING_INTENT",
        "MIXED_INTENT_SEQUENCE",
    }
    MAX_PERSISTENCE_RANGE = 0.35
    MAX_INTENSITY_RANGE = 0.30
    MAX_CHANGE_RATE_RANGE = 0.40
    MIN_PATTERN_CONSISTENCY = 2.0 / 3.0
    MIN_STABLE_WINDOW_RATIO = 2.0 / 3.0

    def evaluate(self, reports: Iterable[Mapping[str, Any]]) -> MarketIntentStabilityValidationReport:
        rows = tuple(dict(item) for item in reports)
        ids = tuple(str(row.get("statistics_id", "")).strip().upper() for row in rows)
        starts = tuple(self._integer(row.get("sample_start_timestamp", 0)) for row in rows)
        ends = tuple(self._integer(row.get("sample_end_timestamp", 0)) for row in rows)
        sequence_counts = tuple(self._integer(row.get("sequence_count", 0)) for row in rows)
        transition_counts = tuple(self._integer(row.get("total_transition_count", 0)) for row in rows)
        persistence = tuple(self._number(row.get("weighted_persistence_ratio", 0.0)) for row in rows)
        intensity = tuple(self._number(row.get("weighted_average_intent_intensity", 0.0)) for row in rows)
        intent_rates = tuple(self._number(row.get("intent_change_rate", 0.0)) for row in rows)
        direction_rates = tuple(self._number(row.get("direction_change_rate", 0.0)) for row in rows)
        regime_rates = tuple(self._number(row.get("regime_change_rate", 0.0)) for row in rows)
        behaviour_rates = tuple(self._number(row.get("behaviour_change_rate", 0.0)) for row in rows)
        patterns = tuple(str(row.get("dominant_sequence_pattern", "")).strip().upper() for row in rows)

        enough = len(rows) >= 3
        lineage = enough and all(
            str(row.get("status", "")).strip().upper() == "READY"
            and statistics_id.startswith("QSTA-")
            and str(row.get("milestone", "Q")).strip().upper() == "Q"
            and str(row.get("pack", "4")).strip() == "4"
            for row, statistics_id in zip(rows, ids)
        )
        chronology = enough and len(set(ids)) == len(ids) and all(
            start > 0 and end >= start for start, end in zip(starts, ends)
        ) and all(left < right for left, right in zip(ends, starts[1:]))
        counts_valid = enough and all(sequence >= 3 and transition > 0 for sequence, transition in zip(sequence_counts, transition_counts))
        metric_values = persistence + intensity + intent_rates + direction_rates + regime_rates + behaviour_rates
        metrics_valid = enough and counts_valid and all(isfinite(value) and 0.0 <= value <= 1.0 for value in metric_values) and all(
            pattern in self.PATTERNS for pattern in patterns
        )
        quality = enough and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = enough and all(bool(row.get("future_safe", False)) for row in rows)
        regime_first = enough and all(bool(row.get("market_regime_before_intent", False)) for row in rows)
        behaviour_first = enough and all(bool(row.get("market_behaviour_before_intent", False)) for row in rows)
        policy_valid = enough and all(self._policy_valid(row) for row in rows)

        if enough and metrics_valid:
            persistence_range = self._range(persistence)
            intensity_range = self._range(intensity)
            intent_range = self._range(intent_rates)
            direction_range = self._range(direction_rates)
            regime_range = self._range(regime_rates)
            behaviour_range = self._range(behaviour_rates)
            pattern_consistency = self._dominant_consistency(patterns)
            stable_flags = tuple(
                abs(persistence[index] - persistence[index - 1]) <= self.MAX_PERSISTENCE_RANGE
                and abs(intensity[index] - intensity[index - 1]) <= self.MAX_INTENSITY_RANGE
                and abs(intent_rates[index] - intent_rates[index - 1]) <= self.MAX_CHANGE_RATE_RANGE
                and abs(direction_rates[index] - direction_rates[index - 1]) <= self.MAX_CHANGE_RATE_RANGE
                and abs(regime_rates[index] - regime_rates[index - 1]) <= self.MAX_CHANGE_RATE_RANGE
                and abs(behaviour_rates[index] - behaviour_rates[index - 1]) <= self.MAX_CHANGE_RATE_RANGE
                for index in range(1, len(rows))
            )
            stable_window_ratio = round(sum(stable_flags) / len(stable_flags), 6)
            threshold_valid = (
                persistence_range <= self.MAX_PERSISTENCE_RANGE
                and intensity_range <= self.MAX_INTENSITY_RANGE
                and max(intent_range, direction_range, regime_range, behaviour_range) <= self.MAX_CHANGE_RATE_RANGE
                and pattern_consistency >= self.MIN_PATTERN_CONSISTENCY
                and stable_window_ratio >= self.MIN_STABLE_WINDOW_RATIO
            )
        else:
            persistence_range = intensity_range = 0.0
            intent_range = direction_range = regime_range = behaviour_range = 0.0
            pattern_consistency = stable_window_ratio = 0.0
            threshold_valid = False

        checks = (
            (not enough, "insufficient_stability_sample"),
            (not lineage, "pack_4_statistics_lineage_invalid"),
            (not chronology, "stability_chronology_invalid"),
            (not counts_valid, "statistics_coverage_invalid"),
            (not metrics_valid, "stability_metrics_invalid"),
            (metrics_valid and not threshold_valid, "market_intent_stability_threshold_not_met"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not regime_first, "market_regime_not_evaluated_before_intent"),
            (not behaviour_first, "market_behaviour_not_evaluated_before_intent"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        ready = not blocked

        if ready:
            persistence_mean = self._weighted_mean(persistence, transition_counts)
            intensity_mean = self._weighted_mean(intensity, transition_counts)
            range_component = max(0.0, 1.0 - (
                persistence_range + intensity_range + intent_range + direction_range + regime_range + behaviour_range
            ) / 6.0)
            stability_score = round((range_component + pattern_consistency + stable_window_ratio) / 3.0, 6)
            stability_band = "HIGH" if stability_score >= 0.85 else "MODERATE"
        else:
            persistence_mean = intensity_mean = stability_score = 0.0
            stability_band = "UNAVAILABLE"

        identity = {"ids": ids, "starts": starts, "ends": ends, "blocked": blocked}
        validation_id = "QSTB-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if ready:
            reason = "MARKET_INTENT_STABILITY_VALIDATED"
            en = "Accepted Pack 4 statistics were validated as stable across deterministic research windows."
            th = "สถิติ Market Intent จาก Pack 4 ที่ผ่านเกณฑ์ได้รับการยืนยันความเสถียรข้ามช่วงวิจัยแบบ deterministic"
        else:
            reason = "MARKET_INTENT_STABILITY_BLOCKED"
            en = "Stability validation was blocked by sample, lineage, chronology, metric, threshold, data, prerequisite, or frozen-policy controls."
            th = "การยืนยันความเสถียรของ Market Intent ถูกระงับจากการตรวจตัวอย่าง lineage ลำดับเวลา ค่าตัวชี้วัด เกณฑ์ ข้อมูล เงื่อนไขก่อนหน้า หรือนโยบายล็อก"

        return MarketIntentStabilityValidationReport(
            validation_id=validation_id,
            status="READY" if ready else "BLOCKED",
            reason=reason,
            milestone="Q",
            pack="5",
            source_statistics_ids=ids,
            validation_start_timestamp=starts[0] if starts else 0,
            validation_end_timestamp=ends[-1] if ends else 0,
            statistics_window_count=len(rows),
            total_sequence_count=sum(sequence_counts) if ready else 0,
            total_transition_count=sum(transition_counts) if ready else 0,
            weighted_persistence_mean=persistence_mean,
            weighted_intensity_mean=intensity_mean,
            persistence_range=persistence_range if metrics_valid else 0.0,
            intensity_range=intensity_range if metrics_valid else 0.0,
            intent_change_rate_range=intent_range if metrics_valid else 0.0,
            direction_change_rate_range=direction_range if metrics_valid else 0.0,
            regime_change_rate_range=regime_range if metrics_valid else 0.0,
            behaviour_change_rate_range=behaviour_range if metrics_valid else 0.0,
            dominant_pattern_consistency=pattern_consistency,
            stable_window_ratio=stable_window_ratio,
            stability_score=stability_score,
            stability_band=stability_band,
            chronology_valid=chronology,
            lineage_valid=lineage,
            metrics_valid=metrics_valid,
            stability_thresholds_valid=threshold_valid,
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
    def _range(values: tuple[float, ...]) -> float:
        return round(max(values) - min(values), 6)

    @staticmethod
    def _dominant_consistency(values: tuple[str, ...]) -> float:
        return round(max(values.count(value) for value in set(values)) / len(values), 6)

    @staticmethod
    def _weighted_mean(values: tuple[float, ...], weights: tuple[int, ...]) -> float:
        total = sum(weights)
        return round(sum(value * weight for value, weight in zip(values, weights)) / total, 6) if total else 0.0

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
