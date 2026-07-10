"""Deterministic trailing-stop intelligence for paper/demo simulation only."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class TrailingStopReport:
    status: str
    reason: str
    trailing_stop_readiness: str
    action: str
    position_side: str
    break_even_detected: bool
    profit_lock_active: bool
    trailing_stage: int
    trailing_stage_name: str
    current_price: float
    entry_price: float
    current_stop_loss: float
    proposed_trailing_stop: float
    minimum_locked_profit: float
    estimated_locked_profit: float
    trading_cost: float
    risk_valid: bool
    timing_valid: bool
    market_structure_confirmed: bool
    trading_cost_valid: bool
    side_validation_passed: bool
    change_approved: bool
    simulation_instruction_ready: bool
    no_order_sent: bool
    block_reasons: tuple[str, ...]
    holding_reason_en: str
    holding_reason_th: str
    trailing_stop_reason_en: str
    trailing_stop_reason_th: str
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


class TrailingStopRuntime:
    """Evaluate a multi-stage trailing-stop proposal without changing a live position."""

    def evaluate_one(self, record: Mapping[str, Any]) -> TrailingStopReport:
        now = self._utc_time(record.get("current_time_utc"))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        side = str(record.get("position_side", record.get("direction", "BUY"))).strip().upper()
        action = str(record.get("trailing_stop_action", "TRAIL_STOP")).strip().upper()
        if action not in {"HOLD", "TRAIL_STOP"}:
            action = "HOLD"

        entry = self._number(record.get("entry_price"))
        current = self._number(record.get("current_price", record.get("market_price")))
        current_sl = self._number(record.get("current_stop_loss", record.get("stop_loss_price")))
        proposed = self._number(record.get("proposed_trailing_stop", current_sl))
        minimum_locked = max(0.0, self._number(record.get("minimum_locked_profit")))
        trading_cost = max(0.0, self._number(record.get("trading_cost", record.get("spread_cost"))))
        maximum_cost = max(0.0, self._number(record.get("maximum_trading_cost", trading_cost)))
        units = max(0, int(record.get("current_units", record.get("position_units", 0)) or 0))
        lot_per_unit = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        risk_valid = bool(record.get("risk_allowed", record.get("risk_valid", True)))
        timing_valid = bool(record.get("timing_allowed", record.get("timing_valid", True)))
        structure_confirmed = bool(record.get("market_structure_confirmed", True))
        live_requested = bool(record.get("live_execution_enabled", False) or record.get("direct_execution", False))

        open_profit = self._directional_distance(side, entry, current)
        current_locked = self._directional_distance(side, entry, current_sl)
        proposed_locked = self._directional_distance(side, entry, proposed)
        break_even_buffer = max(trading_cost, self._number(record.get("break_even_buffer", trading_cost)))
        break_even_detected = open_profit >= break_even_buffer and open_profit > 0
        estimated_locked = max(0.0, proposed_locked - trading_cost)
        profit_lock_active = proposed_locked > trading_cost and estimated_locked >= minimum_locked
        cost_valid = trading_cost <= maximum_cost
        side_valid = self._side_geometry_valid(side, current, current_sl, proposed)
        stage, stage_name = self._stage(record, open_profit, break_even_detected, profit_lock_active)

        blocks: list[str] = []
        checks = (
            (broker == "XM", "xm_only_policy"),
            (symbol == "GOLD#", "gold_only_policy"),
            (side in {"BUY", "SELL"}, "position_side_invalid"),
            (units > 0, "open_position_missing"),
            (entry > 0, "entry_price_missing"),
            (current > 0, "current_price_missing"),
            (current_sl > 0, "current_stop_loss_missing"),
            (abs(lot_per_unit - 0.01) <= 1e-12, "fixed_unit_policy"),
            (risk_valid, "risk_not_approved"),
            (timing_valid, "timing_not_approved"),
            (cost_valid, "trading_cost_not_approved"),
            (not live_requested, "live_or_direct_execution_requested"),
        )
        for passed, block_reason in checks:
            if not passed:
                blocks.append(block_reason)

        if action == "TRAIL_STOP":
            if proposed <= 0:
                blocks.append("proposed_trailing_stop_missing")
            if not break_even_detected:
                blocks.append("break_even_not_detected")
            if not side_valid:
                blocks.append("buy_trailing_stop_invalid" if side == "BUY" else "sell_trailing_stop_invalid")
            if side == "BUY" and proposed <= current_sl:
                blocks.append("trailing_stop_does_not_reduce_buy_risk")
            if side == "SELL" and proposed >= current_sl:
                blocks.append("trailing_stop_does_not_reduce_sell_risk")
            if estimated_locked < minimum_locked:
                blocks.append("minimum_locked_profit_not_met")
            if not structure_confirmed:
                blocks.append("market_structure_not_confirmed")

        blocks = list(dict.fromkeys(blocks))
        confidence = self._confidence(
            side_valid=side_valid,
            break_even=break_even_detected,
            profit_lock=profit_lock_active,
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
            approved = False
            simulation_ready = False
            holding_en = "Keep the current stop loss unchanged while the trailing-stop proposal is blocked."
            holding_th = "คง Stop Loss ปัจจุบันไว้ก่อน ระหว่างที่ข้อเสนอ Trailing Stop ยังถูกบล็อก"
            trail_en = "The proposal must pass break-even, profit-lock, cost, risk, timing, side, and market-structure validation."
            trail_th = "ข้อเสนอต้องผ่านการตรวจ Break-even การล็อกกำไร ต้นทุน ความเสี่ยง เวลา ทิศทาง และโครงสร้างตลาด"
            next_en = "Correct the listed block reasons and evaluate the trailing-stop proposal again."
            next_th = "แก้ไขเหตุผลที่ถูกบล็อก แล้วประเมินข้อเสนอ Trailing Stop อีกครั้ง"
        elif action == "TRAIL_STOP":
            status = "READY"
            reason = "trailing_stop_ready_for_simulation"
            readiness = "READY"
            approved = True
            simulation_ready = True
            holding_en = f"Hold the position while protecting profit with trailing stage {stage}."
            holding_th = f"ถือต่อพร้อมปกป้องกำไรด้วย Trailing Stop ระยะที่ {stage}"
            trail_en = (
                f"Move the simulated stop loss from {current_sl:.2f} to {proposed:.2f}; "
                f"estimated locked profit is {estimated_locked:.2f} after trading cost."
            )
            trail_th = (
                f"เลื่อน Stop Loss แบบจำลองจาก {current_sl:.2f} ไป {proposed:.2f} "
                f"โดยคาดว่าจะล็อกกำไรหลังหักต้นทุน {estimated_locked:.2f}"
            )
            next_en = "Pass the approved instruction to the paper/demo position adapter only and review the next stage on schedule."
            next_th = "ส่งคำสั่งที่อนุมัติไปยัง Paper/Demo Position Adapter เท่านั้น และทบทวนระยะถัดไปตามเวลา"
        else:
            status = "READY"
            reason = "current_stop_loss_remains_valid"
            readiness = "MONITORING"
            approved = False
            simulation_ready = False
            holding_en = "Hold the position with the current stop loss because no trailing change is requested."
            holding_th = "ถือต่อด้วย Stop Loss ปัจจุบัน เนื่องจากยังไม่มีคำขอเลื่อน Trailing Stop"
            trail_en = "Monitor price, trading cost, and market structure for the next valid trailing stage."
            trail_th = "ติดตามราคา ต้นทุน และโครงสร้างตลาด เพื่อรอ Trailing Stop ระยะถัดไปที่เหมาะสม"
            next_en = "Review again when price advances or the market structure changes."
            next_th = "ทบทวนอีกครั้งเมื่อราคาเคลื่อนไปข้างหน้าหรือโครงสร้างตลาดเปลี่ยน"

        review_seconds = max(30, int(record.get("next_review_seconds", 120) or 120))
        return TrailingStopReport(
            status=status,
            reason=reason,
            trailing_stop_readiness=readiness,
            action=action,
            position_side=side,
            break_even_detected=break_even_detected,
            profit_lock_active=profit_lock_active,
            trailing_stage=stage,
            trailing_stage_name=stage_name,
            current_price=round(current, 8),
            entry_price=round(entry, 8),
            current_stop_loss=round(current_sl, 8),
            proposed_trailing_stop=round(proposed, 8),
            minimum_locked_profit=round(minimum_locked, 8),
            estimated_locked_profit=round(estimated_locked, 8),
            trading_cost=round(trading_cost, 8),
            risk_valid=risk_valid,
            timing_valid=timing_valid,
            market_structure_confirmed=structure_confirmed,
            trading_cost_valid=cost_valid,
            side_validation_passed=side_valid,
            change_approved=approved,
            simulation_instruction_ready=simulation_ready,
            no_order_sent=True,
            block_reasons=tuple(blocks),
            holding_reason_en=holding_en,
            holding_reason_th=holding_th,
            trailing_stop_reason_en=trail_en,
            trailing_stop_reason_th=trail_th,
            expected_next_action_en=next_en,
            expected_next_action_th=next_th,
            confidence=confidence,
            next_review_time_utc=(now + timedelta(seconds=review_seconds)).isoformat(),
            broker=broker,
            symbol=symbol,
        )

    def explain_one(self, record: Mapping[str, Any]) -> TrailingStopReport:
        return self.evaluate_one(record)

    @staticmethod
    def _number(value: Any) -> float:
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

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
        return end - start if side == "BUY" else start - end

    @staticmethod
    def _side_geometry_valid(side: str, current: float, current_sl: float, proposed: float) -> bool:
        if min(current, current_sl, proposed) <= 0:
            return False
        if side == "BUY":
            return current_sl < proposed < current
        if side == "SELL":
            return current < proposed < current_sl
        return False

    @staticmethod
    def _stage(record: Mapping[str, Any], open_profit: float, break_even: bool, profit_lock: bool) -> tuple[int, str]:
        requested = int(record.get("trailing_stage", 0) or 0)
        if requested > 0:
            stage = min(4, requested)
        elif profit_lock and open_profit > 0:
            stage = 3
        elif break_even:
            stage = 2
        elif open_profit > 0:
            stage = 1
        else:
            stage = 0
        names = {
            0: "PRE_BREAK_EVEN",
            1: "PROFIT_MONITORING",
            2: "BREAK_EVEN_PROTECTION",
            3: "PROFIT_LOCK",
            4: "STRUCTURE_TRAILING",
        }
        return stage, names[stage]

    @staticmethod
    def _confidence(**checks: bool) -> float:
        blocked = bool(checks.pop("blocked", False))
        total = len(checks)
        score = 100.0 * sum(bool(value) for value in checks.values()) / total if total else 0.0
        if blocked:
            score = min(score, 49.0)
        return round(score, 2)
