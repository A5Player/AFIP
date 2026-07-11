"""Milestone Q Pack 4: deterministic Market Intent statistics.

Aggregates accepted Pack 3 sequence reports into one immutable research-only
statistical record. This module has no execution, broker, position, parameter,
or trading-logic authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite, sqrt
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class MarketIntentStatisticsReport:
    statistics_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    source_sequence_ids: tuple[str, ...]
    sample_start_timestamp: int
    sample_end_timestamp: int
    sequence_count: int
    total_observation_count: int
    total_transition_count: int
    total_intent_change_count: int
    total_direction_change_count: int
    total_regime_change_count: int
    total_behaviour_change_count: int
    weighted_persistence_ratio: float
    weighted_average_intent_intensity: float
    intent_change_rate: float
    direction_change_rate: float
    regime_change_rate: float
    behaviour_change_rate: float
    mean_intensity_change: float
    mean_continuation_reversal_balance_change: float
    intensity_change_standard_deviation: float
    dominant_sequence_pattern: str
    sequence_pattern_distribution: tuple[tuple[str, int], ...]
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


class MarketIntentStatisticsRuntime:
    """Aggregate accepted Pack 3 reports into deterministic statistics."""

    PATTERNS = {
        "PERSISTENT_INTENT",
        "INTENT_REVERSAL_SEQUENCE",
        "BREAKOUT_DEVELOPMENT_SEQUENCE",
        "LIQUIDITY_SEEKING_SEQUENCE",
        "OSCILLATING_INTENT",
        "MIXED_INTENT_SEQUENCE",
    }

    def evaluate(self, reports: Iterable[Mapping[str, Any]]) -> MarketIntentStatisticsReport:
        rows = tuple(dict(item) for item in reports)
        ids = tuple(str(row.get("sequence_id", "")).strip().upper() for row in rows)
        starts = tuple(self._integer(row.get("sequence_start_timestamp", 0)) for row in rows)
        ends = tuple(self._integer(row.get("sequence_end_timestamp", 0)) for row in rows)
        observations = tuple(self._integer(row.get("observation_count", 0)) for row in rows)
        transitions = tuple(self._integer(row.get("transition_count", 0)) for row in rows)
        intent_changes = tuple(self._integer(row.get("intent_change_count", 0)) for row in rows)
        direction_changes = tuple(self._integer(row.get("direction_change_count", 0)) for row in rows)
        regime_changes = tuple(self._integer(row.get("regime_change_count", 0)) for row in rows)
        behaviour_changes = tuple(self._integer(row.get("behaviour_change_count", 0)) for row in rows)
        persistence = tuple(self._number(row.get("persistence_ratio", 0.0)) for row in rows)
        intensities = tuple(self._number(row.get("average_intent_intensity", 0.0)) for row in rows)
        intensity_changes = tuple(self._number(row.get("intensity_change", 0.0)) for row in rows)
        balance_changes = tuple(
            self._number(row.get("continuation_reversal_balance_change", 0.0)) for row in rows
        )
        patterns = tuple(str(row.get("sequence_pattern", "")).strip().upper() for row in rows)

        enough = len(rows) >= 3
        lineage = enough and all(
            str(row.get("status", "")).strip().upper() == "READY"
            and sequence_id.startswith("QSEQ-")
            and str(row.get("milestone", "Q")).strip().upper() == "Q"
            and str(row.get("pack", "3")).strip() == "3"
            for row, sequence_id in zip(rows, ids)
        )
        chronology = enough and all(start > 0 and end >= start for start, end in zip(starts, ends)) and all(
            left < right for left, right in zip(ends, ends[1:])
        ) and len(set(ids)) == len(ids)
        counts_valid = enough and all(
            observation >= 2
            and transition == observation - 1
            and 0 <= intent <= transition
            and 0 <= direction <= transition
            and 0 <= regime <= transition
            and 0 <= behaviour <= transition
            for observation, transition, intent, direction, regime, behaviour in zip(
                observations, transitions, intent_changes, direction_changes, regime_changes, behaviour_changes
            )
        )
        metrics_valid = enough and counts_valid and all(
            isfinite(value) and 0.0 <= value <= 1.0 for value in persistence + intensities
        ) and all(
            isfinite(value) and -1.0 <= value <= 1.0 for value in intensity_changes + balance_changes
        ) and all(pattern in self.PATTERNS for pattern in patterns)
        quality = enough and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = enough and all(bool(row.get("future_safe", False)) for row in rows)
        regime_first = enough and all(bool(row.get("market_regime_before_intent", False)) for row in rows)
        behaviour_first = enough and all(bool(row.get("market_behaviour_before_intent", False)) for row in rows)
        policy_valid = enough and all(self._policy_valid(row) for row in rows)

        checks = (
            (not enough, "insufficient_statistical_sample"),
            (not lineage, "pack_3_sequence_lineage_invalid"),
            (not chronology, "statistics_chronology_invalid"),
            (not counts_valid, "sequence_count_metrics_invalid"),
            (not metrics_valid, "sequence_statistics_metrics_invalid"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not regime_first, "market_regime_not_evaluated_before_intent"),
            (not behaviour_first, "market_behaviour_not_evaluated_before_intent"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        ready = not blocked

        total_observations = sum(observations) if ready else 0
        total_transitions = sum(transitions) if ready else 0
        total_intent_changes = sum(intent_changes) if ready else 0
        total_direction_changes = sum(direction_changes) if ready else 0
        total_regime_changes = sum(regime_changes) if ready else 0
        total_behaviour_changes = sum(behaviour_changes) if ready else 0
        if ready:
            weighted_persistence = self._weighted_mean(persistence, transitions)
            weighted_intensity = self._weighted_mean(intensities, observations)
            intent_rate = self._rate(total_intent_changes, total_transitions)
            direction_rate = self._rate(total_direction_changes, total_transitions)
            regime_rate = self._rate(total_regime_changes, total_transitions)
            behaviour_rate = self._rate(total_behaviour_changes, total_transitions)
            mean_intensity_change = round(sum(intensity_changes) / len(intensity_changes), 6)
            mean_balance_change = round(sum(balance_changes) / len(balance_changes), 6)
            intensity_std = self._population_std(intensity_changes)
            distribution = self._distribution(patterns)
            dominant_pattern = distribution[0][0]
        else:
            weighted_persistence = weighted_intensity = 0.0
            intent_rate = direction_rate = regime_rate = behaviour_rate = 0.0
            mean_intensity_change = mean_balance_change = intensity_std = 0.0
            distribution = tuple()
            dominant_pattern = "UNAVAILABLE"

        identity = {
            "ids": ids,
            "starts": starts,
            "ends": ends,
            "observations": observations,
            "transitions": transitions,
            "patterns": patterns,
            "blocked": blocked,
        }
        statistics_id = "QSTA-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if ready:
            reason = "MARKET_INTENT_STATISTICS_CALCULATED"
            en = "Accepted Pack 3 sequence reports were aggregated into deterministic immutable research statistics."
            th = "รายงานลำดับ Market Intent จาก Pack 3 ที่ผ่านเกณฑ์ถูกสรุปเป็นสถิติ deterministic แบบ immutable สำหรับงานวิจัย"
        else:
            reason = "MARKET_INTENT_STATISTICS_BLOCKED"
            en = "Statistical aggregation was blocked by sample, lineage, chronology, metric, data, prerequisite, or frozen-policy validation."
            th = "การสรุปสถิติ Market Intent ถูกระงับจากการตรวจขนาดตัวอย่าง lineage ลำดับเวลา ค่าตัวชี้วัด ข้อมูล เงื่อนไขก่อนหน้า หรือนโยบายล็อก"

        return MarketIntentStatisticsReport(
            statistics_id=statistics_id,
            status="READY" if ready else "BLOCKED",
            reason=reason,
            milestone="Q",
            pack="4",
            source_sequence_ids=ids,
            sample_start_timestamp=starts[0] if starts else 0,
            sample_end_timestamp=ends[-1] if ends else 0,
            sequence_count=len(rows),
            total_observation_count=total_observations,
            total_transition_count=total_transitions,
            total_intent_change_count=total_intent_changes,
            total_direction_change_count=total_direction_changes,
            total_regime_change_count=total_regime_changes,
            total_behaviour_change_count=total_behaviour_changes,
            weighted_persistence_ratio=weighted_persistence,
            weighted_average_intent_intensity=weighted_intensity,
            intent_change_rate=intent_rate,
            direction_change_rate=direction_rate,
            regime_change_rate=regime_rate,
            behaviour_change_rate=behaviour_rate,
            mean_intensity_change=mean_intensity_change,
            mean_continuation_reversal_balance_change=mean_balance_change,
            intensity_change_standard_deviation=intensity_std,
            dominant_sequence_pattern=dominant_pattern,
            sequence_pattern_distribution=distribution,
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
    def _weighted_mean(values: tuple[float, ...], weights: tuple[int, ...]) -> float:
        total_weight = sum(weights)
        return round(sum(value * weight for value, weight in zip(values, weights)) / total_weight, 6)

    @staticmethod
    def _rate(numerator: int, denominator: int) -> float:
        return round(numerator / denominator, 6) if denominator else 0.0

    @staticmethod
    def _population_std(values: tuple[float, ...]) -> float:
        mean = sum(values) / len(values)
        return round(sqrt(sum((value - mean) ** 2 for value in values) / len(values)), 6)

    @staticmethod
    def _distribution(values: tuple[str, ...]) -> tuple[tuple[str, int], ...]:
        counts = {value: values.count(value) for value in set(values)}
        return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0])))

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
