"""Milestone Q Pack 3: deterministic Market Intent sequence analysis.

Analyzes an ordered collection of accepted Pack 2 normalized states without
changing trading logic, parameters, execution state, positions, or broker
connectivity. Market Regime and Market Behaviour remain prerequisites to Intent.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class MarketIntentSequenceReport:
    sequence_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    source_state_ids: tuple[str, ...]
    sequence_start_timestamp: int
    sequence_end_timestamp: int
    observation_count: int
    transition_count: int
    intent_change_count: int
    direction_change_count: int
    regime_change_count: int
    behaviour_change_count: int
    dominant_intent_state: str
    dominant_direction: str
    sequence_pattern: str
    persistence_ratio: float
    average_intent_intensity: float
    intensity_change: float
    continuation_reversal_balance_change: float
    chronology_valid: bool
    lineage_valid: bool
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


class MarketIntentSequenceAnalysisRuntime:
    """Analyze certified Pack 2 states as one immutable sequence."""

    INTENT_STATES = {
        "BUYING_PRESSURE", "SELLING_PRESSURE", "LIQUIDITY_SEEKING",
        "BREAKOUT_ATTEMPT", "REVERSAL_ATTEMPT", "BALANCED_INTENT",
    }
    DIRECTIONS = {"BUY", "SELL", "FLAT"}
    REGIMES = {"TREND", "RANGE", "TRANSITION", "HIGH_VOLATILITY", "LOW_VOLATILITY"}
    BEHAVIOURS = {
        "DIRECTIONAL_PERSISTENCE", "RANGE_ROTATION", "REGIME_TRANSITION",
        "VOLATILITY_EXPANSION", "VOLATILITY_COMPRESSION", "BALANCED_BEHAVIOUR",
    }

    def evaluate(self, states: Iterable[Mapping[str, Any]]) -> MarketIntentSequenceReport:
        rows = tuple(dict(item) for item in states)
        ids = tuple(str(row.get("state_id", "")).strip().upper() for row in rows)
        timestamps = tuple(self._integer(row.get("normalized_timestamp", 0)) for row in rows)
        intents = tuple(str(row.get("intent_state", "")).strip().upper() for row in rows)
        directions = tuple(str(row.get("direction", "FLAT")).strip().upper() for row in rows)
        regimes = tuple(str(row.get("market_regime", "")).strip().upper() for row in rows)
        behaviours = tuple(str(row.get("market_behaviour", "")).strip().upper() for row in rows)
        intensities = tuple(self._number(row.get("intent_intensity", 0.0)) for row in rows)
        balances = tuple(self._number(row.get("continuation_reversal_balance", 0.0)) for row in rows)

        enough = len(rows) >= 2
        lineage = enough and all(
            str(row.get("status", "")).strip().upper() == "READY"
            and state_id.startswith("QINS-")
            and str(row.get("schema_version", "")).strip().upper() == "AFIP_MARKET_INTENT_STATE_V1"
            for row, state_id in zip(rows, ids)
        )
        chronology = enough and all(ts > 0 for ts in timestamps) and all(
            left < right for left, right in zip(timestamps, timestamps[1:])
        ) and len(set(ids)) == len(ids)
        labels_valid = enough and all(intent in self.INTENT_STATES for intent in intents) and all(
            direction in self.DIRECTIONS for direction in directions
        ) and all(regime in self.REGIMES for regime in regimes) and all(
            behaviour in self.BEHAVIOURS for behaviour in behaviours
        )
        metrics_valid = enough and all(isfinite(value) and 0.0 <= value <= 1.0 for value in intensities) and all(
            isfinite(value) and -1.0 <= value <= 1.0 for value in balances
        )
        quality = enough and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = enough and all(
            bool(row.get("future_safe", False)) and not bool(row.get("future_leakage_detected", False))
            for row in rows
        )
        regime_first = enough and all(bool(row.get("market_regime_before_intent", False)) for row in rows)
        behaviour_first = enough and all(bool(row.get("market_behaviour_before_intent", False)) for row in rows)
        policy_valid = enough and all(self._policy_valid(row) for row in rows)

        checks = (
            (not enough, "insufficient_sequence_length"),
            (not lineage, "pack_2_state_lineage_invalid"),
            (not chronology, "sequence_chronology_invalid"),
            (not labels_valid, "sequence_labels_invalid"),
            (not metrics_valid, "sequence_metrics_invalid"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not regime_first, "market_regime_not_evaluated_before_intent"),
            (not behaviour_first, "market_behaviour_not_evaluated_before_intent"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        ready = not blocked

        transitions = max(len(rows) - 1, 0)
        intent_changes = self._changes(intents)
        direction_changes = self._changes(directions)
        regime_changes = self._changes(regimes)
        behaviour_changes = self._changes(behaviours)
        if ready:
            dominant_intent = self._mode(intents)
            dominant_direction = self._mode(directions)
            persistence = round((transitions - intent_changes) / transitions, 6)
            average_intensity = round(sum(intensities) / len(intensities), 6)
            intensity_change = round(intensities[-1] - intensities[0], 6)
            balance_change = round(balances[-1] - balances[0], 6)
            pattern = self._pattern(intents, directions, intent_changes, direction_changes, persistence)
        else:
            dominant_intent = "UNAVAILABLE"
            dominant_direction = "UNAVAILABLE"
            persistence = 0.0
            average_intensity = 0.0
            intensity_change = 0.0
            balance_change = 0.0
            pattern = "UNAVAILABLE"

        identity = {
            "ids": ids, "timestamps": timestamps, "intents": intents,
            "directions": directions, "intensities": intensities,
            "balances": balances, "blocked": blocked,
        }
        sequence_id = "QSEQ-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()
        if ready:
            reason = "MARKET_INTENT_SEQUENCE_ANALYZED"
            en = "Accepted Pack 2 states were analyzed as a chronological immutable research sequence."
            th = "Market Intent State จาก Pack 2 ที่ผ่านเกณฑ์ถูกวิเคราะห์เป็นลำดับเวลาแบบ immutable สำหรับงานวิจัย"
        else:
            reason = "MARKET_INTENT_SEQUENCE_ANALYSIS_BLOCKED"
            en = "Sequence analysis was blocked by lineage, chronology, data, prerequisite, metric, or frozen-policy validation."
            th = "การวิเคราะห์ลำดับ Market Intent ถูกระงับจากการตรวจ lineage ลำดับเวลา ข้อมูล เงื่อนไขก่อนหน้า ค่าตัวชี้วัด หรือนโยบายล็อก"

        return MarketIntentSequenceReport(
            sequence_id=sequence_id,
            status="READY" if ready else "BLOCKED",
            reason=reason,
            milestone="Q",
            pack="3",
            source_state_ids=ids,
            sequence_start_timestamp=timestamps[0] if timestamps else 0,
            sequence_end_timestamp=timestamps[-1] if timestamps else 0,
            observation_count=len(rows),
            transition_count=transitions,
            intent_change_count=intent_changes,
            direction_change_count=direction_changes,
            regime_change_count=regime_changes,
            behaviour_change_count=behaviour_changes,
            dominant_intent_state=dominant_intent,
            dominant_direction=dominant_direction,
            sequence_pattern=pattern,
            persistence_ratio=persistence,
            average_intent_intensity=average_intensity,
            intensity_change=intensity_change,
            continuation_reversal_balance_change=balance_change,
            chronology_valid=chronology,
            lineage_valid=lineage,
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
    def _changes(values: tuple[str, ...]) -> int:
        return sum(left != right for left, right in zip(values, values[1:]))

    @staticmethod
    def _mode(values: tuple[str, ...]) -> str:
        counts = {value: values.count(value) for value in set(values)}
        return sorted(counts, key=lambda value: (-counts[value], value))[0]

    @staticmethod
    def _pattern(intents: tuple[str, ...], directions: tuple[str, ...], intent_changes: int, direction_changes: int, persistence: float) -> str:
        if direction_changes >= 2 or intent_changes >= max(2, len(intents) // 2):
            return "OSCILLATING_INTENT"
        if persistence >= 0.75:
            return "PERSISTENT_INTENT"
        if intents[-1] == "REVERSAL_ATTEMPT" or direction_changes == 1:
            return "INTENT_REVERSAL_SEQUENCE"
        if intents[-1] == "BREAKOUT_ATTEMPT":
            return "BREAKOUT_DEVELOPMENT_SEQUENCE"
        if intents[-1] == "LIQUIDITY_SEEKING":
            return "LIQUIDITY_SEEKING_SEQUENCE"
        return "MIXED_INTENT_SEQUENCE"

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
