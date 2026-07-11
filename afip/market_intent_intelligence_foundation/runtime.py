"""Milestone Q Pack 1: deterministic Market Intent Intelligence foundation.

Creates immutable, research-only market-intent observations from certified
market-regime and market-behaviour evidence. The runtime interprets intent only;
it cannot change trading logic, parameters, positions, broker settings, or send
orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping


@dataclass(frozen=True)
class MarketIntentObservation:
    observation_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    observed_timestamp: int
    source_timestamp: int
    market_regime: str
    market_behaviour: str
    intent_state: str
    direction: str
    directional_pressure: float
    liquidity_pressure: float
    breakout_pressure: float
    reversal_pressure: float
    participation_strength: float
    data_quality_certified: bool
    future_safe: bool
    chronology_valid: bool
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


class MarketIntentIntelligenceFoundationRuntime:
    """Build immutable intent observations without execution authority."""

    REGIMES = {"TREND", "RANGE", "TRANSITION", "HIGH_VOLATILITY", "LOW_VOLATILITY"}
    BEHAVIOURS = {
        "DIRECTIONAL_PERSISTENCE",
        "RANGE_ROTATION",
        "REGIME_TRANSITION",
        "VOLATILITY_EXPANSION",
        "VOLATILITY_COMPRESSION",
        "BALANCED_BEHAVIOUR",
    }
    DIRECTIONS = {"BUY", "SELL", "FLAT"}

    def evaluate_one(self, payload: Mapping[str, Any]) -> MarketIntentObservation:
        data = dict(payload)
        observed_ts = self._integer(data.get("observed_timestamp", 0))
        source_ts = self._integer(data.get("source_timestamp", 0))
        regime = str(data.get("market_regime", "")).strip().upper()
        behaviour = str(data.get("market_behaviour", "")).strip().upper()
        direction = str(data.get("direction", "FLAT")).strip().upper()
        directional_pressure = self._number(data.get("directional_pressure", 0.0))
        liquidity_pressure = self._number(data.get("liquidity_pressure", 0.0))
        breakout_pressure = self._number(data.get("breakout_pressure", 0.0))
        reversal_pressure = self._number(data.get("reversal_pressure", 0.0))
        participation_strength = self._number(data.get("participation_strength", 0.0))

        quality = bool(data.get("data_quality_certified", False))
        future_safe = bool(data.get("future_safe", False)) and not bool(data.get("future_leakage_detected", False))
        chronology = source_ts > 0 and observed_ts >= source_ts
        regime_first = bool(data.get("market_regime_evaluated_first", False))
        behaviour_first = bool(data.get("market_behaviour_evaluated_first", False))
        policy_valid = (
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
        metrics = (
            directional_pressure,
            liquidity_pressure,
            breakout_pressure,
            reversal_pressure,
            participation_strength,
        )
        metrics_valid = all(isfinite(value) and 0.0 <= value <= 1.0 for value in metrics)
        checks = (
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not chronology, "intent_observation_chronology_invalid"),
            (not regime_first, "market_regime_not_evaluated_before_intent"),
            (not behaviour_first, "market_behaviour_not_evaluated_before_intent"),
            (regime not in self.REGIMES, "market_regime_invalid"),
            (behaviour not in self.BEHAVIOURS, "market_behaviour_invalid"),
            (direction not in self.DIRECTIONS, "direction_invalid"),
            (not metrics_valid, "intent_metrics_invalid"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        ready = not blocked
        intent_state = (
            self._classify(
                behaviour=behaviour,
                direction=direction,
                directional_pressure=directional_pressure,
                liquidity_pressure=liquidity_pressure,
                breakout_pressure=breakout_pressure,
                reversal_pressure=reversal_pressure,
                participation_strength=participation_strength,
            )
            if ready
            else "UNAVAILABLE"
        )
        identity = {
            "source_timestamp": source_ts,
            "observed_timestamp": observed_ts,
            "regime": regime,
            "behaviour": behaviour,
            "direction": direction,
            "metrics": list(metrics),
            "blocked": blocked,
        }
        observation_id = "QINT-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()
        if ready:
            reason = "MARKET_INTENT_OBSERVATION_READY"
            explanation_en = (
                "Certified regime and behaviour evidence was converted into an immutable "
                "research-only market intent observation."
            )
            explanation_th = (
                "หลักฐาน Market Regime และ Market Behaviour ที่ผ่านการรับรองถูกแปลงเป็น "
                "Market Intent Observation แบบ immutable สำหรับงานวิจัยเท่านั้น"
            )
        else:
            reason = "MARKET_INTENT_OBSERVATION_BLOCKED"
            explanation_en = (
                "Market intent observation was blocked by data, chronology, required evaluation order, "
                "metric, or frozen-policy validation."
            )
            explanation_th = (
                "Market Intent Observation ถูกระงับจากการตรวจข้อมูล ลำดับเวลา ลำดับการประเมิน "
                "ค่าตัวชี้วัด หรือนโยบายล็อก"
            )
        return MarketIntentObservation(
            observation_id=observation_id,
            status="READY" if ready else "BLOCKED",
            reason=reason,
            milestone="Q",
            pack="1",
            observed_timestamp=observed_ts,
            source_timestamp=source_ts,
            market_regime=regime,
            market_behaviour=behaviour,
            intent_state=intent_state,
            direction=direction,
            directional_pressure=directional_pressure,
            liquidity_pressure=liquidity_pressure,
            breakout_pressure=breakout_pressure,
            reversal_pressure=reversal_pressure,
            participation_strength=participation_strength,
            data_quality_certified=quality,
            future_safe=future_safe,
            chronology_valid=chronology,
            market_regime_before_intent=regime_first,
            market_behaviour_before_intent=behaviour_first,
            immutable_record=True,
            research_only=True,
            automatic_parameter_update_allowed=False,
            trading_logic_change_allowed=False,
            production_knowledge_allowed=False,
            production_certification_granted=False,
            block_reasons=blocked,
            explanation_reason_en=explanation_en,
            explanation_reason_th=explanation_th,
        )

    @staticmethod
    def _classify(
        *,
        behaviour: str,
        direction: str,
        directional_pressure: float,
        liquidity_pressure: float,
        breakout_pressure: float,
        reversal_pressure: float,
        participation_strength: float,
    ) -> str:
        if reversal_pressure >= 0.75 and reversal_pressure > breakout_pressure:
            return "REVERSAL_ATTEMPT"
        if breakout_pressure >= 0.75 and participation_strength >= 0.55:
            return "BREAKOUT_ATTEMPT"
        if liquidity_pressure >= 0.75 and directional_pressure < 0.65:
            return "LIQUIDITY_SEEKING"
        if (
            direction == "BUY"
            and behaviour == "DIRECTIONAL_PERSISTENCE"
            and directional_pressure >= 0.65
        ):
            return "BUYING_PRESSURE"
        if (
            direction == "SELL"
            and behaviour == "DIRECTIONAL_PERSISTENCE"
            and directional_pressure >= 0.65
        ):
            return "SELLING_PRESSURE"
        return "BALANCED_INTENT"

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
