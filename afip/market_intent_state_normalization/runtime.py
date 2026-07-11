"""Milestone Q Pack 2: deterministic Market Intent state normalization.

Normalizes accepted Pack 1 observations into one canonical immutable research
schema. Market Regime and Market Behaviour must precede Intent. This runtime
cannot adapt parameters, change trading logic, modify positions, contact a
broker, or transmit orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping


@dataclass(frozen=True)
class NormalizedMarketIntentState:
    state_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    source_observation_id: str
    source_timestamp: int
    normalized_timestamp: int
    market_regime: str
    market_behaviour: str
    intent_state: str
    direction: str
    directional_pressure: float
    continuation_pressure: float
    reversal_pressure: float
    liquidity_seeking_pressure: float
    breakout_pressure: float
    dominant_pressure: str
    intent_intensity: float
    intensity_band: str
    continuation_reversal_balance: float
    directional_alignment: str
    schema_version: str
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


class MarketIntentStateNormalizationRuntime:
    """Normalize certified Pack 1 Market Intent observations safely."""

    REGIMES = {"TREND", "RANGE", "TRANSITION", "HIGH_VOLATILITY", "LOW_VOLATILITY"}
    BEHAVIOURS = {
        "DIRECTIONAL_PERSISTENCE",
        "RANGE_ROTATION",
        "REGIME_TRANSITION",
        "VOLATILITY_EXPANSION",
        "VOLATILITY_COMPRESSION",
        "BALANCED_BEHAVIOUR",
    }
    INTENT_STATES = {
        "BUYING_PRESSURE",
        "SELLING_PRESSURE",
        "LIQUIDITY_SEEKING",
        "BREAKOUT_ATTEMPT",
        "REVERSAL_ATTEMPT",
        "BALANCED_INTENT",
    }
    DIRECTIONS = {"BUY", "SELL", "FLAT"}

    def evaluate_one(self, payload: Mapping[str, Any]) -> NormalizedMarketIntentState:
        data = dict(payload)
        source_id = str(data.get("observation_id", "")).strip().upper()
        source_ts = self._integer(data.get("observed_timestamp", 0))
        normalized_ts = self._integer(data.get("normalized_timestamp", 0))
        regime = str(data.get("market_regime", "")).strip().upper()
        behaviour = str(data.get("market_behaviour", "")).strip().upper()
        intent = str(data.get("intent_state", "")).strip().upper()
        direction = str(data.get("direction", "FLAT")).strip().upper()
        directional = self._number(data.get("directional_pressure", 0.0))
        continuation = self._number(data.get("continuation_pressure", 0.0))
        reversal = self._number(data.get("reversal_pressure", 0.0))
        liquidity = self._number(data.get("liquidity_seeking_pressure", 0.0))
        breakout = self._number(data.get("breakout_pressure", 0.0))

        source_ready = (
            str(data.get("status", "")).strip().upper() == "READY"
            and source_id.startswith("QINT-")
        )
        quality = bool(data.get("data_quality_certified", False))
        future_safe = bool(data.get("future_safe", False)) and not bool(
            data.get("future_leakage_detected", False)
        )
        chronology = source_ts > 0 and normalized_ts >= source_ts
        regime_first = bool(data.get("market_regime_before_intent", False))
        behaviour_first = bool(data.get("market_behaviour_before_intent", False))
        labels_valid = (
            regime in self.REGIMES
            and behaviour in self.BEHAVIOURS
            and intent in self.INTENT_STATES
            and direction in self.DIRECTIONS
            and self._intent_direction_valid(intent, direction)
        )
        pressures = (directional, continuation, reversal, liquidity, breakout)
        metrics_valid = all(isfinite(value) and 0.0 <= value <= 1.0 for value in pressures)
        policy_valid = (
            str(data.get("policy_version", "")).strip().upper() == "AFIP_V1_FEATURE_FREEZE"
            and str(data.get("broker", "XM")).strip().upper() == "XM"
            and str(data.get("symbol", "GOLD#")).strip().upper() == "GOLD#"
            and abs(self._number(data.get("base_lot_per_unit", 0.01)) - 0.01) <= 1e-12
            and str(data.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
            == "LOCKED_SIMULATION_ONLY"
            and str(data.get("order_status", "NO_ORDER_SENT")).strip().upper()
            == "NO_ORDER_SENT"
            and not bool(data.get("direct_execution", False))
            and not bool(data.get("live_execution_enabled", False))
            and not bool(data.get("automatic_parameter_update_allowed", False))
            and not bool(data.get("trading_logic_change_allowed", False))
            and not bool(data.get("production_knowledge_allowed", False))
        )
        checks = (
            (not source_ready, "pack_1_observation_not_ready"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not chronology, "normalization_chronology_invalid"),
            (not regime_first, "market_regime_not_evaluated_before_intent"),
            (not behaviour_first, "market_behaviour_not_evaluated_before_intent"),
            (not labels_valid, "intent_labels_invalid"),
            (not metrics_valid, "intent_metrics_invalid"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        ready = not blocked

        if metrics_valid:
            named_pressures = {
                "DIRECTIONAL": directional,
                "CONTINUATION": continuation,
                "REVERSAL": reversal,
                "LIQUIDITY_SEEKING": liquidity,
                "BREAKOUT": breakout,
            }
            dominant = sorted(named_pressures.items(), key=lambda item: (-item[1], item[0]))[0][0]
            intensity = round(max(pressures), 6)
            balance = round(continuation - reversal, 6)
            band = self._intensity_band(intensity)
            alignment = self._directional_alignment(intent, direction, directional)
        else:
            dominant = "UNAVAILABLE"
            intensity = 0.0
            balance = 0.0
            band = "UNAVAILABLE"
            alignment = "UNAVAILABLE"

        identity = {
            "source": source_id,
            "timestamp": normalized_ts,
            "labels": [regime, behaviour, intent, direction],
            "pressures": pressures,
            "blocked": blocked,
        }
        state_id = "QINS-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if ready:
            reason = "MARKET_INTENT_STATE_NORMALIZED"
            en = (
                "Accepted Pack 1 Market Intent evidence was normalized into the "
                "canonical immutable research schema."
            )
            th = (
                "หลักฐาน Market Intent จาก Pack 1 ที่ผ่านเกณฑ์ถูกทำให้เป็นมาตรฐานใน "
                "schema กลางแบบ immutable สำหรับงานวิจัย"
            )
        else:
            reason = "MARKET_INTENT_STATE_NORMALIZATION_BLOCKED"
            en = (
                "Normalization was blocked by source lineage, data, chronology, "
                "prerequisite order, labels, metrics, or frozen-policy validation."
            )
            th = (
                "การทำ Market Intent State ให้เป็นมาตรฐานถูกระงับจากการตรวจ lineage "
                "ข้อมูล ลำดับเวลา ลำดับเงื่อนไข ป้ายกำกับ ค่าตัวชี้วัด หรือนโยบายล็อก"
            )

        return NormalizedMarketIntentState(
            state_id=state_id,
            status="READY" if ready else "BLOCKED",
            reason=reason,
            milestone="Q",
            pack="2",
            source_observation_id=source_id,
            source_timestamp=source_ts,
            normalized_timestamp=normalized_ts,
            market_regime=regime,
            market_behaviour=behaviour,
            intent_state=intent,
            direction=direction,
            directional_pressure=directional,
            continuation_pressure=continuation,
            reversal_pressure=reversal,
            liquidity_seeking_pressure=liquidity,
            breakout_pressure=breakout,
            dominant_pressure=dominant,
            intent_intensity=intensity,
            intensity_band=band,
            continuation_reversal_balance=balance,
            directional_alignment=alignment,
            schema_version="AFIP_MARKET_INTENT_STATE_V1",
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
            explanation_reason_en=en,
            explanation_reason_th=th,
        )

    @staticmethod
    def _intent_direction_valid(intent: str, direction: str) -> bool:
        if intent == "BUYING_PRESSURE":
            return direction == "BUY"
        if intent == "SELLING_PRESSURE":
            return direction == "SELL"
        return True

    @staticmethod
    def _intensity_band(value: float) -> str:
        if value >= 0.80:
            return "HIGH"
        if value >= 0.60:
            return "MODERATE"
        return "LOW"

    @staticmethod
    def _directional_alignment(intent: str, direction: str, pressure: float) -> str:
        if intent == "BUYING_PRESSURE" and direction == "BUY" and pressure >= 0.60:
            return "ALIGNED"
        if intent == "SELLING_PRESSURE" and direction == "SELL" and pressure >= 0.60:
            return "ALIGNED"
        if intent in {"BUYING_PRESSURE", "SELLING_PRESSURE"}:
            return "MISALIGNED"
        return "NEUTRAL"

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
