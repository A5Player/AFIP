"""Milestone P Pack 4: deterministic market behaviour transition statistics.

Aggregates certified Pack 3 sequence reports into immutable research-only
transition statistics. It cannot adapt parameters, change trading logic,
modify positions, or transmit orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class MarketBehaviourTransitionStatisticsReport:
    report_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    statistics_timestamp: int
    sequence_report_count: int
    total_state_count: int
    total_transition_count: int
    total_regime_change_count: int
    total_behaviour_change_count: int
    total_direction_change_count: int
    weighted_persistence_ratio: float
    regime_change_rate: float
    behaviour_change_rate: float
    direction_change_rate: float
    dominant_market_regime: str
    dominant_behaviour_state: str
    most_common_transition: str
    transition_frequencies: tuple[tuple[str, int], ...]
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


class MarketBehaviourTransitionStatisticsRuntime:
    """Aggregate Pack 3 reports without production or execution authority."""

    def evaluate_many(
        self,
        reports: Iterable[Mapping[str, Any]],
        *,
        statistics_timestamp: int,
    ) -> MarketBehaviourTransitionStatisticsReport:
        rows = [dict(item) for item in reports]
        ids = tuple(str(row.get("report_id", "")).strip().upper() for row in rows)
        starts = tuple(self._integer(row.get("sequence_start_timestamp", 0)) for row in rows)
        ends = tuple(self._integer(row.get("sequence_end_timestamp", 0)) for row in rows)
        statistics_ts = self._integer(statistics_timestamp)

        source_ready = bool(rows) and all(
            str(row.get("status", "")).strip().upper() == "READY"
            and str(row.get("schema_version", "")).strip().upper() == "AFIP_MARKET_BEHAVIOUR_SEQUENCE_V1"
            and report_id.startswith("PBSQ-")
            for row, report_id in zip(rows, ids)
        )
        unique = len(ids) == len(set(ids))
        chronology = (
            bool(rows)
            and all(start > 0 and end >= start for start, end in zip(starts, ends))
            and tuple(sorted(starts)) == starts
            and statistics_ts >= max(ends)
        )
        quality = bool(rows) and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = bool(rows) and all(bool(row.get("future_safe", False)) for row in rows)
        regime_first = bool(rows) and all(bool(row.get("market_regime_before_behaviour", False)) for row in rows)
        policy_valid = bool(rows) and all(self._policy_valid(row) for row in rows)

        state_counts = tuple(max(0, self._integer(row.get("state_count", 0))) for row in rows)
        transition_counts = tuple(max(0, self._integer(row.get("transition_count", 0))) for row in rows)
        metrics_valid = bool(rows) and all(
            state_count >= 3
            and transition_count == state_count - 1
            and 0.0 <= self._number(row.get("persistence_ratio", -1.0)) <= 1.0
            and self._integer(row.get("regime_change_count", -1)) >= 0
            and self._integer(row.get("behaviour_change_count", -1)) >= 0
            and self._integer(row.get("direction_change_count", -1)) >= 0
            for row, state_count, transition_count in zip(rows, state_counts, transition_counts)
        )

        checks = (
            (not source_ready, "pack_3_sequence_lineage_invalid"),
            (not unique, "duplicate_sequence_report_id_detected"),
            (len(rows) < 3, "insufficient_sequence_report_coverage"),
            (not chronology, "transition_statistics_chronology_invalid"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not regime_first, "market_regime_not_evaluated_before_behaviour"),
            (not metrics_valid, "sequence_metrics_invalid"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        ready = not blocked

        total_states = sum(state_counts)
        total_transitions = sum(transition_counts)
        regime_changes = sum(max(0, self._integer(row.get("regime_change_count", 0))) for row in rows)
        behaviour_changes = sum(max(0, self._integer(row.get("behaviour_change_count", 0))) for row in rows)
        direction_changes = sum(max(0, self._integer(row.get("direction_change_count", 0))) for row in rows)
        persistence_numerator = sum(
            self._number(row.get("persistence_ratio", 0.0)) * count
            for row, count in zip(rows, transition_counts)
        )
        weighted_persistence = round(persistence_numerator / max(1, total_transitions), 6)

        transitions: list[str] = []
        regimes: list[str] = []
        behaviours: list[str] = []
        for row in rows:
            transitions.extend(str(item).strip().upper() for item in row.get("transition_signature", ()) if str(item).strip())
            regimes.append(str(row.get("dominant_market_regime", "UNAVAILABLE")).strip().upper())
            behaviours.append(str(row.get("dominant_behaviour_state", "UNAVAILABLE")).strip().upper())
        transition_frequencies = self._frequencies(transitions)
        most_common = transition_frequencies[0][0] if transition_frequencies else "UNAVAILABLE"

        identity = {
            "ids": ids,
            "starts": starts,
            "ends": ends,
            "statistics_timestamp": statistics_ts,
            "transition_frequencies": transition_frequencies,
            "blocked": blocked,
        }
        report_id = "PBTS-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if ready:
            reason = "MARKET_BEHAVIOUR_TRANSITION_STATISTICS_READY"
            en = "Certified Pack 3 sequence reports were aggregated into immutable deterministic transition statistics."
            th = "รายงานลำดับจาก Pack 3 ที่ผ่านการรับรองถูกสรุปเป็นสถิติการเปลี่ยนผ่านแบบ immutable และ deterministic"
        else:
            reason = "MARKET_BEHAVIOUR_TRANSITION_STATISTICS_BLOCKED"
            en = "Transition statistics were blocked by lineage, duplication, coverage, chronology, data, metrics, or frozen-policy validation."
            th = "สถิติการเปลี่ยนผ่านถูกระงับจากการตรวจ lineage ข้อมูลซ้ำ ความครอบคลุม ลำดับเวลา ข้อมูล ค่าตัวชี้วัด หรือนโยบายล็อก"

        return MarketBehaviourTransitionStatisticsReport(
            report_id=report_id,
            status="READY" if ready else "BLOCKED",
            reason=reason,
            milestone="P",
            pack="4",
            statistics_timestamp=statistics_ts,
            sequence_report_count=len(rows),
            total_state_count=total_states,
            total_transition_count=total_transitions,
            total_regime_change_count=regime_changes,
            total_behaviour_change_count=behaviour_changes,
            total_direction_change_count=direction_changes,
            weighted_persistence_ratio=weighted_persistence,
            regime_change_rate=self._rate(regime_changes, total_transitions),
            behaviour_change_rate=self._rate(behaviour_changes, total_transitions),
            direction_change_rate=self._rate(direction_changes, total_transitions),
            dominant_market_regime=self._dominant(tuple(regimes)),
            dominant_behaviour_state=self._dominant(tuple(behaviours)),
            most_common_transition=most_common,
            transition_frequencies=transition_frequencies,
            source_report_ids=ids,
            schema_version="AFIP_MARKET_BEHAVIOUR_TRANSITION_STATISTICS_V1",
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
    def _frequencies(values: list[str]) -> tuple[tuple[str, int], ...]:
        counts = {value: values.count(value) for value in set(values)}
        return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0])))

    @staticmethod
    def _dominant(values: tuple[str, ...]) -> str:
        clean = tuple(value for value in values if value and value != "UNAVAILABLE")
        if not clean:
            return "UNAVAILABLE"
        counts = {value: clean.count(value) for value in set(clean)}
        return sorted(counts, key=lambda value: (-counts[value], value))[0]

    @staticmethod
    def _rate(numerator: int, denominator: int) -> float:
        return round(numerator / max(1, denominator), 6)

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
