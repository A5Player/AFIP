"""Milestone P Pack 5: deterministic market behaviour stability validation.

Validates certified Pack 4 transition-statistics reports across chronological
research windows. The runtime has no adaptive, production, position, broker,
or order-transmission authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
from statistics import pstdev
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class MarketBehaviourStabilityReport:
    report_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    validation_timestamp: int
    window_count: int
    total_sequence_report_count: int
    total_transition_count: int
    mean_persistence_ratio: float
    persistence_standard_deviation: float
    mean_regime_change_rate: float
    regime_change_rate_standard_deviation: float
    mean_behaviour_change_rate: float
    behaviour_change_rate_standard_deviation: float
    dominant_regime_consistency_rate: float
    dominant_behaviour_consistency_rate: float
    stable_window_rate: float
    source_report_ids: tuple[str, ...]
    schema_version: str
    data_quality_certified: bool
    future_safe: bool
    chronology_valid: bool
    market_regime_before_behaviour: bool
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


class MarketBehaviourStabilityValidationRuntime:
    """Validate Pack 4 behaviour statistics without execution authority."""

    def evaluate_many(
        self,
        reports: Iterable[Mapping[str, Any]],
        *,
        validation_timestamp: int,
        min_window_count: int = 3,
        min_total_transition_count: int = 9,
        max_persistence_std: float = 0.20,
        max_change_rate_std: float = 0.25,
        min_consistency_rate: float = 0.60,
        min_stable_window_rate: float = 0.67,
    ) -> MarketBehaviourStabilityReport:
        rows = [dict(item) for item in reports]
        ids = tuple(str(row.get("report_id", "")).strip().upper() for row in rows)
        timestamps = tuple(self._integer(row.get("statistics_timestamp", 0)) for row in rows)
        validation_ts = self._integer(validation_timestamp)

        source_ready = bool(rows) and all(
            str(row.get("status", "")).strip().upper() == "READY"
            and str(row.get("schema_version", "")).strip().upper()
            == "AFIP_MARKET_BEHAVIOUR_TRANSITION_STATISTICS_V1"
            and report_id.startswith("PBTS-")
            for row, report_id in zip(rows, ids)
        )
        unique = len(ids) == len(set(ids))
        chronology = (
            bool(rows)
            and all(ts > 0 for ts in timestamps)
            and tuple(sorted(timestamps)) == timestamps
            and validation_ts >= max(timestamps)
        )
        quality = bool(rows) and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = bool(rows) and all(bool(row.get("future_safe", False)) for row in rows)
        regime_first = bool(rows) and all(bool(row.get("market_regime_before_behaviour", False)) for row in rows)
        policy_valid = bool(rows) and all(self._policy_valid(row) for row in rows)

        transition_counts = tuple(max(0, self._integer(row.get("total_transition_count", 0))) for row in rows)
        persistence = tuple(self._number(row.get("weighted_persistence_ratio", float("nan"))) for row in rows)
        regime_rates = tuple(self._number(row.get("regime_change_rate", float("nan"))) for row in rows)
        behaviour_rates = tuple(self._number(row.get("behaviour_change_rate", float("nan"))) for row in rows)
        metrics_valid = bool(rows) and all(
            count > 0
            and self._unit_interval(p)
            and self._unit_interval(r)
            and self._unit_interval(b)
            for count, p, r, b in zip(transition_counts, persistence, regime_rates, behaviour_rates)
        )

        persistence_std = self._std(persistence) if metrics_valid else 0.0
        regime_std = self._std(regime_rates) if metrics_valid else 0.0
        behaviour_std = self._std(behaviour_rates) if metrics_valid else 0.0
        regimes = tuple(str(row.get("dominant_market_regime", "UNAVAILABLE")).strip().upper() for row in rows)
        behaviours = tuple(str(row.get("dominant_behaviour_state", "UNAVAILABLE")).strip().upper() for row in rows)
        regime_consistency = self._consistency(regimes)
        behaviour_consistency = self._consistency(behaviours)
        stable_flags = tuple(
            abs(p - self._mean(persistence)) <= max_persistence_std
            and abs(r - self._mean(regime_rates)) <= max_change_rate_std
            and abs(b - self._mean(behaviour_rates)) <= max_change_rate_std
            for p, r, b in zip(persistence, regime_rates, behaviour_rates)
        ) if metrics_valid else ()
        stable_rate = round(sum(stable_flags) / max(1, len(stable_flags)), 6)
        total_transitions = sum(transition_counts)

        checks = (
            (not source_ready, "pack_4_transition_statistics_lineage_invalid"),
            (not unique, "duplicate_transition_statistics_report_id_detected"),
            (len(rows) < max(1, self._integer(min_window_count)), "insufficient_stability_window_coverage"),
            (total_transitions < max(1, self._integer(min_total_transition_count)), "insufficient_transition_sample_coverage"),
            (not chronology, "market_behaviour_stability_chronology_invalid"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not regime_first, "market_regime_not_evaluated_before_behaviour"),
            (not metrics_valid, "transition_statistics_metrics_invalid"),
            (metrics_valid and persistence_std > self._number(max_persistence_std), "persistence_variability_exceeds_limit"),
            (metrics_valid and (regime_std > self._number(max_change_rate_std) or behaviour_std > self._number(max_change_rate_std)), "change_rate_variability_exceeds_limit"),
            (metrics_valid and (regime_consistency < self._number(min_consistency_rate) or behaviour_consistency < self._number(min_consistency_rate)), "dominant_state_consistency_below_minimum"),
            (metrics_valid and stable_rate < self._number(min_stable_window_rate), "stable_window_rate_below_minimum"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        ready = not blocked

        identity = {
            "ids": ids,
            "timestamps": timestamps,
            "validation_timestamp": validation_ts,
            "thresholds": [min_window_count, min_total_transition_count, max_persistence_std, max_change_rate_std, min_consistency_rate, min_stable_window_rate],
            "blocked": blocked,
        }
        report_id = "PBST-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        if ready:
            reason = "MARKET_BEHAVIOUR_STABILITY_VALIDATION_READY"
            en = "Certified Pack 4 transition statistics are stable across chronological research windows."
            th = "สถิติการเปลี่ยนผ่านจาก Pack 4 ที่ผ่านการรับรองมีเสถียรภาพข้ามช่วงเวลาวิจัยตามลำดับเวลา"
        else:
            reason = "MARKET_BEHAVIOUR_STABILITY_VALIDATION_BLOCKED"
            en = "Market behaviour stability was blocked by lineage, coverage, chronology, data, variability, consistency, or frozen-policy validation."
            th = "การตรวจเสถียรภาพพฤติกรรมตลาดถูกระงับจาก lineage ความครอบคลุม ลำดับเวลา ข้อมูล ความแปรปรวน ความสอดคล้อง หรือนโยบายล็อก"

        return MarketBehaviourStabilityReport(
            report_id=report_id,
            status="READY" if ready else "BLOCKED",
            reason=reason,
            milestone="P",
            pack="5",
            validation_timestamp=validation_ts,
            window_count=len(rows),
            total_sequence_report_count=sum(max(0, self._integer(row.get("sequence_report_count", 0))) for row in rows),
            total_transition_count=total_transitions,
            mean_persistence_ratio=self._mean(persistence) if metrics_valid else 0.0,
            persistence_standard_deviation=persistence_std,
            mean_regime_change_rate=self._mean(regime_rates) if metrics_valid else 0.0,
            regime_change_rate_standard_deviation=regime_std,
            mean_behaviour_change_rate=self._mean(behaviour_rates) if metrics_valid else 0.0,
            behaviour_change_rate_standard_deviation=behaviour_std,
            dominant_regime_consistency_rate=regime_consistency,
            dominant_behaviour_consistency_rate=behaviour_consistency,
            stable_window_rate=stable_rate,
            source_report_ids=ids,
            schema_version="AFIP_MARKET_BEHAVIOUR_STABILITY_VALIDATION_V1",
            data_quality_certified=quality,
            future_safe=future_safe,
            chronology_valid=chronology,
            market_regime_before_behaviour=regime_first,
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
    def _policy_valid(row: Mapping[str, Any]) -> bool:
        return (
            str(row.get("broker", "")).strip().upper() == "XM"
            and str(row.get("symbol", "")).strip().upper() == "GOLD#"
            and abs(float(row.get("base_lot_per_unit", 0.0)) - 0.01) < 1e-12
            and str(row.get("execution_status", "")).strip().upper() == "LOCKED_SIMULATION_ONLY"
            and str(row.get("order_status", "")).strip().upper() == "NO_ORDER_SENT"
            and not bool(row.get("direct_execution", True))
            and not bool(row.get("live_execution_enabled", True))
            and not bool(row.get("automatic_parameter_update_allowed", True))
            and not bool(row.get("trading_logic_change_allowed", True))
            and not bool(row.get("production_knowledge_allowed", True))
        )

    @staticmethod
    def _integer(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError, OverflowError):
            return 0

    @staticmethod
    def _number(value: Any) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            return float("nan")
        return number

    @staticmethod
    def _unit_interval(value: float) -> bool:
        return math.isfinite(value) and 0.0 <= value <= 1.0

    @staticmethod
    def _mean(values: tuple[float, ...]) -> float:
        return round(sum(values) / max(1, len(values)), 6)

    @staticmethod
    def _std(values: tuple[float, ...]) -> float:
        return round(pstdev(values), 6) if len(values) > 1 else 0.0

    @staticmethod
    def _consistency(values: tuple[str, ...]) -> float:
        clean = tuple(value for value in values if value and value != "UNAVAILABLE")
        if not clean:
            return 0.0
        counts = {value: clean.count(value) for value in set(clean)}
        return round(max(counts.values()) / len(clean), 6)
