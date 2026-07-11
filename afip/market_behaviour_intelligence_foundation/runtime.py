"""Milestone P Pack 1: deterministic Market Behaviour Intelligence foundation.

Creates immutable research-only market-behaviour observations from certified,
chronologically safe inputs. This runtime classifies behaviour evidence only; it
cannot change trading logic, position state, parameters, broker settings, or
transmit orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping


@dataclass(frozen=True)
class MarketBehaviourObservation:
    observation_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    observed_timestamp: int
    source_timestamp: int
    market_regime: str
    behaviour_state: str
    direction: str
    trend_efficiency: float
    volatility_ratio: float
    range_position: float
    momentum_persistence: float
    liquidity_condition: str
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


class MarketBehaviourIntelligenceFoundationRuntime:
    """Build immutable behaviour observations without execution authority."""

    REGIMES = {"TREND", "RANGE", "TRANSITION", "HIGH_VOLATILITY", "LOW_VOLATILITY"}
    DIRECTIONS = {"BUY", "SELL", "FLAT"}
    LIQUIDITY = {"NORMAL", "THIN", "EXPANDING", "CONTRACTING", "UNKNOWN"}

    def evaluate_one(self, payload: Mapping[str, Any]) -> MarketBehaviourObservation:
        data = dict(payload)
        observed_ts = self._integer(data.get("observed_timestamp", 0))
        source_ts = self._integer(data.get("source_timestamp", 0))
        regime = str(data.get("market_regime", "")).strip().upper()
        direction = str(data.get("direction", "FLAT")).strip().upper()
        liquidity = str(data.get("liquidity_condition", "UNKNOWN")).strip().upper()
        trend_efficiency = self._number(data.get("trend_efficiency", 0.0))
        volatility_ratio = self._number(data.get("volatility_ratio", 1.0))
        range_position = self._number(data.get("range_position", 0.5))
        momentum_persistence = self._number(data.get("momentum_persistence", 0.0))

        quality = bool(data.get("data_quality_certified", False))
        future_safe = bool(data.get("future_safe", False)) and not bool(data.get("future_leakage_detected", False))
        chronology = source_ts > 0 and observed_ts >= source_ts
        regime_first = bool(data.get("market_regime_evaluated_first", False))
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
        metrics_valid = (
            all(isfinite(v) for v in (trend_efficiency, volatility_ratio, range_position, momentum_persistence))
            and 0.0 <= trend_efficiency <= 1.0
            and 0.0 <= volatility_ratio <= 10.0
            and 0.0 <= range_position <= 1.0
            and -1.0 <= momentum_persistence <= 1.0
        )
        checks = (
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not chronology, "behaviour_observation_chronology_invalid"),
            (not regime_first, "market_regime_not_evaluated_before_behaviour"),
            (regime not in self.REGIMES, "market_regime_invalid"),
            (direction not in self.DIRECTIONS, "direction_invalid"),
            (liquidity not in self.LIQUIDITY, "liquidity_condition_invalid"),
            (not metrics_valid, "behaviour_metrics_invalid"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        ready = not blocked
        behaviour = self._classify(regime, direction, trend_efficiency, volatility_ratio, momentum_persistence) if ready else "UNAVAILABLE"
        identity = {
            "source_timestamp": source_ts,
            "observed_timestamp": observed_ts,
            "regime": regime,
            "direction": direction,
            "liquidity": liquidity,
            "metrics": [trend_efficiency, volatility_ratio, range_position, momentum_persistence],
            "blocked": blocked,
        }
        observation_id = "PBEH-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        if ready:
            reason = "MARKET_BEHAVIOUR_OBSERVATION_READY"
            en = "Certified market data was converted into an immutable research-only market behaviour observation."
            th = "ข้อมูลตลาดที่ผ่านการรับรองถูกแปลงเป็น Market Behaviour Observation แบบ immutable สำหรับงานวิจัยเท่านั้น"
        else:
            reason = "MARKET_BEHAVIOUR_OBSERVATION_BLOCKED"
            en = "Market behaviour observation was blocked by data, chronology, regime-order, metric, or frozen-policy validation."
            th = "Market Behaviour Observation ถูกระงับจากการตรวจข้อมูล ลำดับเวลา ลำดับ Market Regime ค่าตัวชี้วัด หรือนโยบายล็อก"
        return MarketBehaviourObservation(
            observation_id=observation_id,
            status="READY" if ready else "BLOCKED",
            reason=reason,
            milestone="P",
            pack="1",
            observed_timestamp=observed_ts,
            source_timestamp=source_ts,
            market_regime=regime,
            behaviour_state=behaviour,
            direction=direction,
            trend_efficiency=trend_efficiency,
            volatility_ratio=volatility_ratio,
            range_position=range_position,
            momentum_persistence=momentum_persistence,
            liquidity_condition=liquidity,
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
    def _classify(regime: str, direction: str, trend_efficiency: float, volatility_ratio: float, momentum: float) -> str:
        if volatility_ratio >= 2.0:
            return "VOLATILITY_EXPANSION"
        if regime == "RANGE" and trend_efficiency <= 0.35:
            return "RANGE_ROTATION"
        if regime == "TRANSITION":
            return "REGIME_TRANSITION"
        if direction in {"BUY", "SELL"} and trend_efficiency >= 0.65 and abs(momentum) >= 0.5:
            return "DIRECTIONAL_PERSISTENCE"
        if volatility_ratio <= 0.6:
            return "VOLATILITY_COMPRESSION"
        return "BALANCED_BEHAVIOUR"

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
