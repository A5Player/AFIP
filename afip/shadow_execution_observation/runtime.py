"""Deterministic shadow-execution observation for Milestone L Pack 7."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Any, Mapping


@dataclass(frozen=True)
class ShadowExecutionObservationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    observation_readiness: str
    shadow_observation_id: str
    performance_certification_status: str
    performance_certification_id: str
    certified_for_shadow_observation: bool
    decision_id: str
    approved_action: str
    position_state: str
    direction: str
    requested_units: int
    intended_entry_price: float
    observed_market_price: float
    intended_stop_loss: float
    intended_take_profit: float
    observed_spread_points: float
    maximum_spread_points: float
    spread_valid: bool
    observed_latency_ms: float
    maximum_latency_ms: float
    latency_valid: bool
    market_data_fresh: bool
    market_session_open: bool
    action_geometry_valid: bool
    risk_validation_valid: bool
    timing_validation_valid: bool
    market_structure_confirmed: bool
    independent_trade_plan_valid: bool
    protected_runner_exposure_included: bool
    traditional_dca_disabled: bool
    averaging_down_disabled: bool
    shadow_instruction_created: bool
    broker_request_created: bool
    order_transmission_attempted: bool
    block_reasons: tuple[str, ...]
    observation_reason_en: str
    observation_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    confidence: float
    next_review_time_utc: str
    broker: str = "XM"
    symbol: str = "GOLD#"
    lot_per_unit: float = 0.01
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    direct_execution: bool = False
    live_execution_enabled: bool = False
    order_status: str = "NO_ORDER_SENT"
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ShadowExecutionObservationRuntime:
    """Observe a certified execution decision without creating a broker request."""

    _ACTIONS = {"ENTRY", "HOLD", "MOVE_STOP_LOSS", "CHANGE_TAKE_PROFIT", "TRAILING_STOP", "PARTIAL_CLOSE", "FULL_EXIT"}

    def evaluate_one(self, record: Mapping[str, Any]) -> ShadowExecutionObservationReport:
        now = self._utc_time(record.get("current_time_utc"))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        certification_status = str(record.get("performance_certification_status", "BLOCKED")).strip().upper()
        certification_id = str(record.get("performance_certification_id", "")).strip()
        certified_shadow = bool(record.get("certified_for_shadow_observation", False))
        decision_id = str(record.get("decision_id", "")).strip()
        action = str(record.get("approved_action", "HOLD")).strip().upper() or "HOLD"
        position_state = str(record.get("position_state", "FLAT")).strip().upper() or "FLAT"
        direction = str(record.get("direction", "NONE")).strip().upper() or "NONE"
        units = max(0, self._integer(record.get("requested_units", 0)))
        intended_entry = self._number(record.get("intended_entry_price", 0.0))
        market_price = self._number(record.get("observed_market_price", 0.0))
        stop = self._number(record.get("intended_stop_loss", 0.0))
        target = self._number(record.get("intended_take_profit", 0.0))
        spread = max(0.0, self._number(record.get("observed_spread_points", 0.0)))
        max_spread = max(0.0, self._number(record.get("maximum_spread_points", 80.0)) or 80.0)
        latency = max(0.0, self._number(record.get("observed_latency_ms", 0.0)))
        max_latency = max(1.0, self._number(record.get("maximum_latency_ms", 500.0)) or 500.0)
        spread_valid = spread <= max_spread
        latency_valid = latency <= max_latency
        market_data_fresh = bool(record.get("market_data_fresh", True))
        market_session_open = bool(record.get("market_session_open", True))
        risk_valid = bool(record.get("risk_validation_valid", True))
        timing_valid = bool(record.get("timing_validation_valid", True))
        structure_valid = bool(record.get("market_structure_confirmed", True))
        independent_plan = bool(record.get("independent_trade_plan_valid", True))
        runner_exposure = bool(record.get("protected_runner_exposure_included", True))
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()

        geometry_valid = self._geometry_valid(action, position_state, direction, units, intended_entry, stop, target)
        checks = {
            "performance_certification_not_ready": certification_status == "READY",
            "performance_certification_id_missing": bool(certification_id),
            "shadow_certification_missing": certified_shadow,
            "decision_id_missing": bool(decision_id),
            "approved_action_invalid": action in self._ACTIONS,
            "action_geometry_invalid": geometry_valid,
            "market_data_stale": market_data_fresh,
            "market_session_closed": market_session_open,
            "spread_above_limit": spread_valid,
            "latency_above_limit": latency_valid,
            "risk_validation_failed": risk_valid,
            "timing_validation_failed": timing_valid,
            "market_structure_unconfirmed": structure_valid,
            "independent_trade_plan_invalid": independent_plan,
            "protected_runner_exposure_excluded": runner_exposure,
            "traditional_dca_enabled": not bool(record.get("traditional_dca_enabled", False)),
            "averaging_down_enabled": not bool(record.get("averaging_down_enabled", False)),
            "xm_only_policy": broker == "XM",
            "gold_only_policy": symbol == "GOLD#",
            "fixed_unit_policy": abs(lot - 0.01) <= 1e-12,
            "simulation_lock_missing": execution_status == "LOCKED_SIMULATION_ONLY",
            "direct_execution_requested": not bool(record.get("direct_execution", False)),
            "live_execution_requested": not bool(record.get("live_execution_enabled", False)),
            "order_status_not_safe": order_status == "NO_ORDER_SENT",
            "broker_request_created": not bool(record.get("broker_request_created", False)),
            "order_transmission_attempted": not bool(record.get("order_transmission_attempted", False)),
        }
        blocks = tuple(name for name, passed in checks.items() if not passed)
        payload = {
            "certification_id": certification_id, "decision_id": decision_id,
            "action": action, "position_state": position_state, "direction": direction,
            "units": units, "prices": [intended_entry, market_price, stop, target],
            "execution_quality": [spread, max_spread, latency, max_latency], "checks": checks,
        }
        observation_id = "L07-" + sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        ready = not blocks
        if ready:
            status, reason, readiness = "READY", "shadow_observation_recorded", "SHADOW_OBSERVATION_READY"
            en = "The certified decision was observed against current market, spread, latency, risk, timing, and structure conditions without creating a broker request."
            th = "บันทึกการสังเกต Decision ที่ผ่านการรับรองเทียบกับตลาด Spread, Latency, ความเสี่ยง เวลา และโครงสร้างปัจจุบัน โดยไม่สร้างคำขอไปยัง Broker"
            next_en = "Continue collecting shadow observations and compare intended decisions with chronological outcomes before demo certification."
            next_th = "เก็บ Shadow Observation ต่อเนื่องและเปรียบเทียบการตัดสินใจกับผลลัพธ์ตามลำดับเวลา ก่อนเข้าสู่การรับรอง Demo"
        else:
            status, reason, readiness = "BLOCKED", blocks[0], "SHADOW_OBSERVATION_BLOCKED"
            en = "Shadow observation was blocked because certification, market quality, policy, risk, or execution-safety requirements failed."
            th = "บล็อก Shadow Observation เพราะเงื่อนไขการรับรอง คุณภาพตลาด นโยบาย ความเสี่ยง หรือความปลอดภัยของ Execution ไม่ผ่าน"
            next_en = "Correct every block reason and re-evaluate the same decision without transmitting an order."
            next_th = "แก้ไข Block Reason ทั้งหมด แล้วประเมิน Decision เดิมใหม่โดยไม่ส่งคำสั่งซื้อขาย"
        passed = sum(1 for value in checks.values() if value)
        review = max(5, self._integer(record.get("next_review_seconds", 60)) or 60)
        return ShadowExecutionObservationReport(
            status=status, reason=reason, milestone="MILESTONE_L", pack="PACK_7",
            observation_readiness=readiness, shadow_observation_id=observation_id,
            performance_certification_status=certification_status, performance_certification_id=certification_id,
            certified_for_shadow_observation=certified_shadow, decision_id=decision_id,
            approved_action=action, position_state=position_state, direction=direction, requested_units=units,
            intended_entry_price=round(intended_entry, 6), observed_market_price=round(market_price, 6),
            intended_stop_loss=round(stop, 6), intended_take_profit=round(target, 6),
            observed_spread_points=round(spread, 6), maximum_spread_points=round(max_spread, 6), spread_valid=spread_valid,
            observed_latency_ms=round(latency, 6), maximum_latency_ms=round(max_latency, 6), latency_valid=latency_valid,
            market_data_fresh=market_data_fresh, market_session_open=market_session_open,
            action_geometry_valid=geometry_valid, risk_validation_valid=risk_valid,
            timing_validation_valid=timing_valid, market_structure_confirmed=structure_valid,
            independent_trade_plan_valid=independent_plan, protected_runner_exposure_included=runner_exposure,
            traditional_dca_disabled=checks["traditional_dca_enabled"], averaging_down_disabled=checks["averaging_down_enabled"],
            shadow_instruction_created=ready, broker_request_created=False, order_transmission_attempted=False,
            block_reasons=blocks, observation_reason_en=en, observation_reason_th=th,
            expected_next_action_en=next_en, expected_next_action_th=next_th,
            confidence=round(passed / len(checks) * 100.0, 2),
            next_review_time_utc=(now + timedelta(seconds=review)).isoformat(),
            broker=broker, symbol=symbol, lot_per_unit=lot, execution_status=execution_status, order_status=order_status,
        )

    @staticmethod
    def _geometry_valid(action: str, state: str, direction: str, units: int, entry: float, stop: float, target: float) -> bool:
        if action == "HOLD":
            return True
        if action == "ENTRY":
            if state != "FLAT" or direction not in {"BUY", "SELL"} or units < 1 or min(entry, stop, target) <= 0:
                return False
            return stop < entry < target if direction == "BUY" else target < entry < stop
        return state == "OPEN" and direction in {"BUY", "SELL"}

    @staticmethod
    def _number(value: Any) -> float:
        try: return float(value)
        except (TypeError, ValueError): return 0.0

    @staticmethod
    def _integer(value: Any) -> int:
        try: return int(value)
        except (TypeError, ValueError): return 0

    @staticmethod
    def _utc_time(value: Any) -> datetime:
        if isinstance(value, datetime): parsed = value
        elif value: parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        else: parsed = datetime.now(timezone.utc)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
