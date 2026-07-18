"""Milestone N Pack 2: deterministic, research-only adaptive position sizing."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import floor, isfinite
from typing import Any, Mapping


@dataclass(frozen=True)
class AdaptivePositionSizingReport:
    status: str
    reason: str
    milestone: str
    pack: str
    sizing_id: str
    foundation_id: str
    profile_id: str
    market_regime: str
    equity: float
    free_margin: float
    risk_budget_percent: float
    risk_budget_amount: float
    stop_distance_points: float
    value_per_point_per_unit: float
    confidence_score: float
    confidence_multiplier: float
    raw_units: float
    capital_limit_units: int
    risk_limit_units: int
    margin_limit_units: int
    recommended_units: int
    recommended_lot: float
    maximum_units: int
    base_lot_per_unit: float
    minimum_capital_per_unit: float
    risk_budget_valid: bool
    stop_distance_valid: bool
    margin_capacity_valid: bool
    confidence_valid: bool
    market_regime_before_signal: bool
    independent_trade_plan_required: bool
    protected_runner_supported: bool
    adaptive_position_sizing_ready: bool
    research_only: bool
    production_knowledge_approved: bool
    block_reasons: tuple[str, ...]
    explanation_reason_en: str
    explanation_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    broker: str = "XM"
    symbol: str = "GOLD#"
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    direct_execution: bool = False
    live_execution_enabled: bool = False
    order_status: str = "NO_ORDER_SENT"
    broker_request_created: bool = False
    order_transmission_attempted: bool = False
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class AdaptivePositionSizingRuntime:
    """Produces a bounded sizing recommendation without execution authority."""

    def evaluate_one(self, record: Mapping[str, Any]) -> AdaptivePositionSizingReport:
        foundation_id = str(record.get("foundation_id", "")).strip()
        profile_id = str(record.get("profile_id", "")).strip()
        market_regime = str(record.get("market_regime", "")).strip().upper()
        equity = self._number(record.get("equity"), 0.0)
        free_margin = self._number(record.get("free_margin"), 0.0)
        risk_percent = self._number(record.get("risk_budget_percent"), 0.0)
        stop_points = self._number(record.get("stop_distance_points"), 0.0)
        value_per_point = self._number(record.get("value_per_point_per_unit"), 0.0)
        confidence = self._number(record.get("confidence_score"), 0.0)
        min_capital = self._number(record.get("minimum_capital_per_unit"), 1000.0)
        margin_per_unit = self._number(record.get("margin_required_per_unit"), 0.0)
        maximum_units = self._integer(record.get("maximum_units"), 3)
        base_lot = self._number(record.get("base_lot_per_unit"), 0.01)
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"

        risk_valid = 0.0 < risk_percent <= 5.0 and equity > 0.0
        stop_valid = stop_points > 0.0 and value_per_point > 0.0
        margin_valid = free_margin >= 0.0 and margin_per_unit > 0.0
        confidence_valid = 0.0 <= confidence <= 100.0
        regime_first = bool(record.get("market_regime_before_signal", True)) and bool(market_regime)
        lifecycle_valid = bool(record.get("independent_trade_plan_required", True))
        runner_supported = bool(record.get("protected_runner_supported", True))
        foundation_ready = bool(record.get("portfolio_intelligence_foundation_ready", False))
        data_quality = bool(record.get("data_quality_certified", False))
        future_safe = not bool(record.get("future_leakage_detected", False))

        if confidence >= 90.0:
            confidence_multiplier = 1.0
        elif confidence >= 75.0:
            confidence_multiplier = 0.75
        elif confidence >= 60.0:
            confidence_multiplier = 0.5
        else:
            confidence_multiplier = 0.0

        risk_budget_amount = equity * risk_percent / 100.0 if risk_valid else 0.0
        loss_per_unit = stop_points * value_per_point if stop_valid else 0.0
        raw_units = (risk_budget_amount / loss_per_unit) * confidence_multiplier if loss_per_unit > 0.0 else 0.0
        capital_limit = floor(equity / min_capital) if min_capital > 0.0 else 0
        risk_limit = floor(raw_units) if raw_units > 0.0 else 0
        margin_limit = floor(free_margin / margin_per_unit) if margin_valid else 0
        recommended = max(0, min(maximum_units, capital_limit, risk_limit, margin_limit))

        blocked: list[str] = []
        if not foundation_id: blocked.append("portfolio_foundation_lineage_missing")
        if not foundation_ready: blocked.append("portfolio_foundation_not_ready")
        if not profile_id: blocked.append("profile_id_missing")
        if not risk_valid: blocked.append("risk_budget_invalid")
        if not stop_valid: blocked.append("stop_distance_or_value_invalid")
        if not margin_valid: blocked.append("margin_capacity_invalid")
        if not confidence_valid: blocked.append("confidence_score_invalid")
        if confidence_multiplier == 0.0: blocked.append("confidence_below_sizing_threshold")
        if not regime_first: blocked.append("market_regime_sequence_invalid")
        if not lifecycle_valid: blocked.append("independent_trade_plan_required")
        if not runner_supported: blocked.append("protected_runner_policy_missing")
        if not data_quality: blocked.append("data_quality_not_certified")
        if not future_safe: blocked.append("future_leakage_detected")
        if min_capital <= 0.0: blocked.append("minimum_capital_per_unit_invalid")
        if maximum_units < 0 or maximum_units > 3: blocked.append("maximum_units_policy_violation")
        if abs(base_lot - 0.01) > 1e-12: blocked.append("base_unit_policy_violation")
        if broker != "XM": blocked.append("broker_policy_violation")
        if symbol != "GOLD#": blocked.append("symbol_policy_violation")
        if str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).upper() != "LOCKED_SIMULATION_ONLY":
            blocked.append("execution_lock_invalid")
        if str(record.get("order_status", "NO_ORDER_SENT")).upper() != "NO_ORDER_SENT":
            blocked.append("order_status_invalid")
        if bool(record.get("direct_execution", False)) or bool(record.get("live_execution_enabled", False)):
            blocked.append("execution_enablement_forbidden")
        if bool(record.get("broker_request_created", False)) or bool(record.get("order_transmission_attempted", False)):
            blocked.append("order_transmission_forbidden")

        ready = not blocked
        if not ready:
            recommended = 0
        identity = {
            "foundation_id": foundation_id,
            "profile_id": profile_id,
            "market_regime": market_regime,
            "equity": round(equity, 8),
            "free_margin": round(free_margin, 8),
            "risk_percent": round(risk_percent, 8),
            "stop_points": round(stop_points, 8),
            "value_per_point": round(value_per_point, 8),
            "confidence": round(confidence, 8),
            "minimum_capital_per_unit": round(min_capital, 8),
            "margin_required_per_unit": round(margin_per_unit, 8),
            "maximum_units": maximum_units,
            "recommended_units": recommended,
            "blocked": sorted(set(blocked)),
        }
        sizing_id = "APS-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()

        return AdaptivePositionSizingReport(
            status="READY" if ready else "BLOCKED",
            reason="Adaptive position sizing recommendation is ready under research-only authority." if ready else "Adaptive position sizing is blocked by portfolio, risk, margin, confidence, policy or safety controls.",
            milestone="N", pack="2", sizing_id=sizing_id, foundation_id=foundation_id,
            profile_id=profile_id, market_regime=market_regime, equity=round(equity, 8),
            free_margin=round(free_margin, 8), risk_budget_percent=round(risk_percent, 8),
            risk_budget_amount=round(risk_budget_amount, 8), stop_distance_points=round(stop_points, 8),
            value_per_point_per_unit=round(value_per_point, 8), confidence_score=round(confidence, 8),
            confidence_multiplier=confidence_multiplier, raw_units=round(raw_units, 8),
            capital_limit_units=max(0, capital_limit), risk_limit_units=max(0, risk_limit),
            margin_limit_units=max(0, margin_limit), recommended_units=recommended,
            recommended_lot=round(recommended * base_lot, 8), maximum_units=maximum_units,
            base_lot_per_unit=base_lot, minimum_capital_per_unit=min_capital,
            risk_budget_valid=risk_valid, stop_distance_valid=stop_valid,
            margin_capacity_valid=margin_valid, confidence_valid=confidence_valid,
            market_regime_before_signal=regime_first,
            independent_trade_plan_required=lifecycle_valid, protected_runner_supported=runner_supported,
            adaptive_position_sizing_ready=ready, research_only=True,
            production_knowledge_approved=False, block_reasons=tuple(sorted(set(blocked))),
            explanation_reason_en="Calculates a bounded unit recommendation from capital, risk, stop distance, margin capacity and confidence while preserving independent position lifecycles." if ready else "No units are recommended until all portfolio, risk, confidence, lineage and safety gates pass.",
            explanation_reason_th="คำนวณจำนวน Unit แบบมีขอบเขตจากทุน ความเสี่ยง ระยะ Stop Loss ความสามารถด้าน Margin และ Confidence โดยรักษาวงจรชีวิต Position แยกอิสระ" if ready else "ไม่แนะนำ Unit จนกว่าเกณฑ์ Portfolio, Risk, Confidence, Lineage และ Safety จะผ่านครบ",
            expected_next_action_en="Continue to Milestone N Pack 3 — Portfolio Risk Engine." if ready else "Correct blocked sizing evidence and evaluate again.",
            expected_next_action_th="ดำเนินการต่อ Milestone N Pack 3 — Portfolio Risk Engine" if ready else "แก้หลักฐาน Sizing ที่ถูกบล็อกแล้วประเมินใหม่",
            broker=broker, symbol=symbol,
        )

    @staticmethod
    def _number(value: Any, default: float) -> float:
        try:
            number = float(value)
            return number if isfinite(number) else default
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _integer(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
