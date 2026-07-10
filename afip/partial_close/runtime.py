"""Deterministic partial-close intelligence for paper/demo simulation only."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class PartialCloseReport:
    status: str
    reason: str
    partial_close_readiness: str
    action: str
    position_side: str
    current_units: int
    requested_close_units: int
    approved_close_units: int
    remaining_units: int
    minimum_remaining_units: int
    close_ratio: float
    current_price: float
    entry_price: float
    open_profit_distance: float
    estimated_realized_profit: float
    estimated_net_realized_profit: float
    trading_cost: float
    profit_valid: bool
    unit_policy_valid: bool
    runner_policy_valid: bool
    risk_valid: bool
    timing_valid: bool
    market_structure_confirmed: bool
    trading_cost_valid: bool
    side_validation_passed: bool
    partial_close_approved: bool
    simulation_instruction_ready: bool
    no_order_sent: bool
    block_reasons: tuple[str, ...]
    holding_reason_en: str
    holding_reason_th: str
    partial_close_reason_en: str
    partial_close_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    confidence: float
    next_review_time_utc: str
    broker: str = "XM"
    symbol: str = "GOLD#"
    lot_per_unit: float = 0.01
    direct_execution: bool = False
    live_execution_enabled: bool = False
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    order_status: str = "NO_ORDER_SENT"
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class PartialCloseRuntime:
    """Validate a fixed-unit partial-close proposal without closing a live position."""

    def evaluate_one(self, record: Mapping[str, Any]) -> PartialCloseReport:
        now = self._utc_time(record.get("current_time_utc"))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        side = str(record.get("position_side", record.get("direction", "BUY"))).strip().upper()
        action = str(record.get("partial_close_action", "HOLD")).strip().upper()
        if action not in {"HOLD", "PARTIAL_CLOSE"}:
            action = "HOLD"

        current_units = max(0, self._integer(record.get("current_units", record.get("position_units", 0))))
        requested_units = max(0, self._integer(record.get("requested_close_units", record.get("partial_close_units", 0))))
        minimum_remaining = max(0, self._integer(record.get("minimum_remaining_units", 1)))
        lot_per_unit = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        entry = self._number(record.get("entry_price"))
        current = self._number(record.get("current_price", record.get("market_price")))
        trading_cost = max(0.0, self._number(record.get("trading_cost", record.get("spread_cost"))))
        maximum_cost = max(0.0, self._number(record.get("maximum_trading_cost", trading_cost)))
        minimum_profit = max(0.0, self._number(record.get("minimum_profit_distance", trading_cost)))
        risk_valid = bool(record.get("risk_allowed", record.get("risk_valid", True)))
        timing_valid = bool(record.get("timing_allowed", record.get("timing_valid", True)))
        structure_confirmed = bool(record.get("market_structure_confirmed", True))
        live_requested = bool(record.get("live_execution_enabled", False) or record.get("direct_execution", False))

        open_profit = self._directional_distance(side, entry, current)
        side_valid = side in {"BUY", "SELL"} and entry > 0 and current > 0
        profit_valid = open_profit >= minimum_profit and open_profit > 0
        unit_policy_valid = abs(lot_per_unit - 0.01) <= 1e-12
        remaining_units = current_units - requested_units
        runner_valid = requested_units > 0 and remaining_units >= minimum_remaining and requested_units < current_units
        cost_valid = trading_cost <= maximum_cost
        gross_realized = max(0.0, open_profit) * requested_units
        net_realized = max(0.0, gross_realized - trading_cost * requested_units)
        close_ratio = requested_units / current_units if current_units else 0.0

        blocks: list[str] = []
        checks = (
            (broker == "XM", "xm_only_policy"),
            (symbol == "GOLD#", "gold_only_policy"),
            (side in {"BUY", "SELL"}, "position_side_invalid"),
            (current_units > 1, "partial_close_requires_multiple_units"),
            (entry > 0, "entry_price_missing"),
            (current > 0, "current_price_missing"),
            (unit_policy_valid, "fixed_unit_policy"),
            (risk_valid, "risk_not_approved"),
            (timing_valid, "timing_not_approved"),
            (cost_valid, "trading_cost_not_approved"),
            (not live_requested, "live_or_direct_execution_requested"),
        )
        for passed, block_reason in checks:
            if not passed:
                blocks.append(block_reason)

        if action == "PARTIAL_CLOSE":
            if requested_units <= 0:
                blocks.append("requested_close_units_missing")
            if requested_units >= current_units and current_units > 0:
                blocks.append("partial_close_cannot_close_all_units")
            if remaining_units < minimum_remaining:
                blocks.append("minimum_runner_units_not_preserved")
            if not profit_valid:
                blocks.append("minimum_profit_not_confirmed")
            if not structure_confirmed:
                blocks.append("market_structure_not_confirmed")

        blocks = list(dict.fromkeys(blocks))
        approved_units = requested_units if action == "PARTIAL_CLOSE" and not blocks else 0
        approved = approved_units > 0
        confidence = self._confidence(
            side=side_valid,
            profit=profit_valid,
            units=unit_policy_valid and runner_valid,
            risk=risk_valid,
            timing=timing_valid,
            structure=structure_confirmed,
            cost=cost_valid,
            blocked=bool(blocks),
        )

        if blocks:
            status = "BLOCKED"
            reason = blocks[0]
            readiness = "NOT_READY"
            holding_en = "Keep all current Units open while the partial-close proposal is blocked."
            holding_th = "คง Unit ที่ถืออยู่ทั้งหมดไว้ก่อน ระหว่างที่ข้อเสนอ Partial Close ยังถูกบล็อก"
            partial_en = "The proposal must preserve the minimum runner and pass profit, cost, risk, timing, side, and market-structure validation."
            partial_th = "ข้อเสนอต้องเหลือ Runner ขั้นต่ำ และผ่านการตรวจผลกำไร ต้นทุน ความเสี่ยง เวลา ทิศทาง และโครงสร้างตลาด"
            next_en = "Correct the listed block reasons and evaluate the partial-close proposal again."
            next_th = "แก้ไขเหตุผลที่ถูกบล็อก แล้วประเมินข้อเสนอ Partial Close อีกครั้ง"
        elif action == "PARTIAL_CLOSE":
            status = "READY"
            reason = "partial_close_ready_for_simulation"
            readiness = "READY"
            holding_en = f"Keep {remaining_units} Unit(s) as the protected runner after the simulated reduction."
            holding_th = f"ถือ Runner ต่อจำนวน {remaining_units} Unit หลังลดสถานะแบบจำลอง"
            partial_en = (
                f"Close {approved_units} Unit(s) in paper/demo simulation only; "
                f"estimated net realized profit is {net_realized:.2f}."
            )
            partial_th = (
                f"ปิด {approved_units} Unit เฉพาะใน Paper/Demo Simulation "
                f"โดยคาดว่ากำไรสุทธิที่รับรู้จะเป็น {net_realized:.2f}"
            )
            next_en = "Pass the approved fixed-unit instruction to the paper/demo position adapter only, then review the remaining runner."
            next_th = "ส่งคำสั่งแบบ Fixed Unit ที่อนุมัติไปยัง Paper/Demo Position Adapter เท่านั้น แล้วทบทวน Runner ที่เหลือ"
        else:
            status = "READY"
            reason = "partial_close_not_requested"
            readiness = "MONITORING"
            holding_en = "Hold all current Units because no partial close is requested."
            holding_th = "ถือ Unit ปัจจุบันทั้งหมดต่อ เนื่องจากยังไม่มีคำขอ Partial Close"
            partial_en = "Monitor profit, trading cost, risk, timing, and market structure for a valid reduction opportunity."
            partial_th = "ติดตามกำไร ต้นทุน ความเสี่ยง เวลา และโครงสร้างตลาด เพื่อรอโอกาสลดสถานะที่เหมาะสม"
            next_en = "Review again when the profit objective or market structure changes."
            next_th = "ทบทวนอีกครั้งเมื่อเป้าหมายกำไรหรือโครงสร้างตลาดเปลี่ยน"

        review_seconds = max(30, self._integer(record.get("next_review_seconds", 120)) or 120)
        return PartialCloseReport(
            status=status,
            reason=reason,
            partial_close_readiness=readiness,
            action=action,
            position_side=side,
            current_units=current_units,
            requested_close_units=requested_units,
            approved_close_units=approved_units,
            remaining_units=max(0, remaining_units),
            minimum_remaining_units=minimum_remaining,
            close_ratio=round(close_ratio, 8),
            current_price=round(current, 8),
            entry_price=round(entry, 8),
            open_profit_distance=round(open_profit, 8),
            estimated_realized_profit=round(gross_realized, 8),
            estimated_net_realized_profit=round(net_realized, 8),
            trading_cost=round(trading_cost, 8),
            profit_valid=profit_valid,
            unit_policy_valid=unit_policy_valid,
            runner_policy_valid=runner_valid,
            risk_valid=risk_valid,
            timing_valid=timing_valid,
            market_structure_confirmed=structure_confirmed,
            trading_cost_valid=cost_valid,
            side_validation_passed=side_valid,
            partial_close_approved=approved,
            simulation_instruction_ready=approved,
            no_order_sent=True,
            block_reasons=tuple(blocks),
            holding_reason_en=holding_en,
            holding_reason_th=holding_th,
            partial_close_reason_en=partial_en,
            partial_close_reason_th=partial_th,
            expected_next_action_en=next_en,
            expected_next_action_th=next_th,
            confidence=confidence,
            next_review_time_utc=(now + timedelta(seconds=review_seconds)).isoformat(),
            broker=broker,
            symbol=symbol,
        )

    def explain_one(self, record: Mapping[str, Any]) -> PartialCloseReport:
        return self.evaluate_one(record)

    @staticmethod
    def _number(value: Any) -> float:
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _integer(value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _utc_time(value: Any) -> datetime:
        if isinstance(value, datetime):
            parsed = value
        elif value:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        else:
            parsed = datetime.now(timezone.utc)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _directional_distance(side: str, start: float, end: float) -> float:
        if start <= 0 or end <= 0:
            return 0.0
        if side == "BUY":
            return end - start
        if side == "SELL":
            return start - end
        return 0.0

    @staticmethod
    def _confidence(*, side: bool, profit: bool, units: bool, risk: bool, timing: bool, structure: bool, cost: bool, blocked: bool) -> float:
        score = sum((side, profit, units, risk, timing, structure, cost)) / 7 * 100.0
        if blocked:
            score = min(score, 49.0)
        return round(score, 2)
