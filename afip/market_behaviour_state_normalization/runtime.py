"""Milestone P Pack 2: deterministic market behaviour state normalization.

Normalizes accepted Pack 1 observations into one canonical research schema. It
has no authority to adapt parameters, change trading logic, modify positions,
or transmit orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping


@dataclass(frozen=True)
class NormalizedMarketBehaviourState:
    state_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    source_observation_id: str
    source_timestamp: int
    normalized_timestamp: int
    market_regime: str
    behaviour_state: str
    direction: str
    liquidity_condition: str
    trend_efficiency: float
    volatility_ratio: float
    range_position: float
    momentum_persistence: float
    directional_strength: float
    volatility_state: str
    range_zone: str
    momentum_state: str
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


class MarketBehaviourStateNormalizationRuntime:
    """Normalize certified Pack 1 observations without execution authority."""

    REGIMES = {"TREND", "RANGE", "TRANSITION", "HIGH_VOLATILITY", "LOW_VOLATILITY"}
    STATES = {"DIRECTIONAL_PERSISTENCE", "RANGE_ROTATION", "REGIME_TRANSITION", "VOLATILITY_EXPANSION", "VOLATILITY_COMPRESSION", "BALANCED_BEHAVIOUR"}
    DIRECTIONS = {"BUY", "SELL", "FLAT"}
    LIQUIDITY = {"NORMAL", "THIN", "EXPANDING", "CONTRACTING", "UNKNOWN"}

    def evaluate_one(self, payload: Mapping[str, Any]) -> NormalizedMarketBehaviourState:
        data = dict(payload)
        source_id = str(data.get("observation_id", "")).strip().upper()
        source_ts = self._integer(data.get("observed_timestamp", 0))
        normalized_ts = self._integer(data.get("normalized_timestamp", 0))
        regime = str(data.get("market_regime", "")).strip().upper()
        behaviour = str(data.get("behaviour_state", "")).strip().upper()
        direction = str(data.get("direction", "FLAT")).strip().upper()
        liquidity = str(data.get("liquidity_condition", "UNKNOWN")).strip().upper()
        trend = self._number(data.get("trend_efficiency", 0.0))
        volatility = self._number(data.get("volatility_ratio", 1.0))
        range_position = self._number(data.get("range_position", 0.5))
        momentum = self._number(data.get("momentum_persistence", 0.0))

        source_ready = str(data.get("status", "")).strip().upper() == "READY" and source_id.startswith("PBEH-")
        quality = bool(data.get("data_quality_certified", False))
        future_safe = bool(data.get("future_safe", False)) and not bool(data.get("future_leakage_detected", False))
        chronology = source_ts > 0 and normalized_ts >= source_ts
        regime_first = bool(data.get("market_regime_before_behaviour", False))
        metrics_valid = (
            all(isfinite(v) for v in (trend, volatility, range_position, momentum))
            and 0.0 <= trend <= 1.0 and 0.0 <= volatility <= 10.0
            and 0.0 <= range_position <= 1.0 and -1.0 <= momentum <= 1.0
        )
        labels_valid = regime in self.REGIMES and behaviour in self.STATES and direction in self.DIRECTIONS and liquidity in self.LIQUIDITY
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
        checks = (
            (not source_ready, "pack_1_observation_not_ready"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not chronology, "normalization_chronology_invalid"),
            (not regime_first, "market_regime_not_evaluated_before_behaviour"),
            (not labels_valid, "behaviour_labels_invalid"),
            (not metrics_valid, "behaviour_metrics_invalid"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        ready = not blocked
        directional_strength = round(trend * abs(momentum), 6) if metrics_valid else 0.0
        volatility_state = self._volatility_state(volatility) if metrics_valid else "UNAVAILABLE"
        range_zone = self._range_zone(range_position) if metrics_valid else "UNAVAILABLE"
        momentum_state = self._momentum_state(momentum) if metrics_valid else "UNAVAILABLE"
        identity = {"source": source_id, "timestamp": normalized_ts, "labels": [regime, behaviour, direction, liquidity], "metrics": [trend, volatility, range_position, momentum], "blocked": blocked}
        state_id = "PBNS-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        if ready:
            reason = "MARKET_BEHAVIOUR_STATE_NORMALIZED"
            en = "Accepted Pack 1 behaviour evidence was normalized into the canonical immutable research schema."
            th = "หลักฐานพฤติกรรมตลาดจาก Pack 1 ที่ผ่านเกณฑ์ถูกทำให้เป็นมาตรฐานใน schema กลางแบบ immutable สำหรับงานวิจัย"
        else:
            reason = "MARKET_BEHAVIOUR_STATE_NORMALIZATION_BLOCKED"
            en = "Normalization was blocked by source lineage, data, chronology, labels, metrics, or frozen-policy validation."
            th = "การทำ Market Behaviour State ให้เป็นมาตรฐานถูกระงับจากการตรวจ lineage ข้อมูล ลำดับเวลา ป้ายกำกับ ค่าตัวชี้วัด หรือนโยบายล็อก"
        return NormalizedMarketBehaviourState(
            state_id=state_id, status="READY" if ready else "BLOCKED", reason=reason,
            milestone="P", pack="2", source_observation_id=source_id,
            source_timestamp=source_ts, normalized_timestamp=normalized_ts,
            market_regime=regime, behaviour_state=behaviour, direction=direction,
            liquidity_condition=liquidity, trend_efficiency=trend,
            volatility_ratio=volatility, range_position=range_position,
            momentum_persistence=momentum, directional_strength=directional_strength,
            volatility_state=volatility_state, range_zone=range_zone,
            momentum_state=momentum_state, schema_version="AFIP_MARKET_BEHAVIOUR_STATE_V1",
            data_quality_certified=quality, future_safe=future_safe,
            chronology_valid=chronology, market_regime_before_behaviour=regime_first,
            immutable_record=True, research_only=True,
            automatic_parameter_update_allowed=False, trading_logic_change_allowed=False,
            production_knowledge_allowed=False, production_certification_granted=False,
            block_reasons=blocked, explanation_reason_en=en, explanation_reason_th=th,
        )

    @staticmethod
    def _volatility_state(value: float) -> str:
        if value >= 2.0: return "EXPANDING"
        if value <= 0.6: return "COMPRESSED"
        return "NORMAL"

    @staticmethod
    def _range_zone(value: float) -> str:
        if value <= 0.33: return "LOWER"
        if value >= 0.67: return "UPPER"
        return "MIDDLE"

    @staticmethod
    def _momentum_state(value: float) -> str:
        if value >= 0.5: return "BULLISH_PERSISTENT"
        if value <= -0.5: return "BEARISH_PERSISTENT"
        return "NEUTRAL"

    @staticmethod
    def _integer(value: Any) -> int:
        try: return int(value)
        except (TypeError, ValueError): return 0

    @staticmethod
    def _number(value: Any) -> float:
        try: return float(value)
        except (TypeError, ValueError): return float("nan")
