"""Deterministic smart-entry planning for paper/demo simulation only."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class SmartEntryReport:
    status: str
    reason: str
    entry_plan_status: str
    order_side: str
    order_type: str
    reference_price: float
    stop_loss_price: float
    take_profit_price: float
    risk_distance: float
    reward_distance: float
    reward_risk_ratio: float
    unit_count: int
    total_lot: float
    simulation_instruction_ready: bool
    no_order_sent: bool
    block_reasons: tuple[str, ...]
    entry_reason_en: str
    entry_reason_th: str
    waiting_reason_en: str
    waiting_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    next_review_time_utc: str
    broker: str = "XM"
    symbol: str = "GOLD#"
    lot_per_unit: float = 0.01
    direct_execution: bool = False
    live_execution_enabled: bool = False
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class SmartEntryRuntime:
    """Build an explainable entry instruction without sending an order."""

    def evaluate_one(self, record: Mapping[str, Any]) -> SmartEntryReport:
        now = record.get("current_time_utc") or datetime.now(timezone.utc)
        if not isinstance(now, datetime):
            now = datetime.fromisoformat(str(now).replace("Z", "+00:00"))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        readiness = str(record.get("execution_readiness", "WAITING_FOR_VALIDATION")).strip().upper()
        portfolio_decision = str(record.get("portfolio_decision", "WAIT")).strip().upper()
        direction = str(record.get("direction", record.get("entry_direction", portfolio_decision))).strip().upper()
        units = max(0, int(record.get("approved_units", record.get("unit_count", 0)) or 0))
        lot_per_unit = float(record.get("lot_per_unit", 0.01) or 0.01)
        reference = float(record.get("reference_price", record.get("entry_price", record.get("market_price", 0.0))) or 0.0)
        stop = float(record.get("stop_loss_price", record.get("stop_loss", 0.0)) or 0.0)
        target = float(record.get("take_profit_price", record.get("take_profit", 0.0)) or 0.0)
        order_type = str(record.get("order_type", "MARKET")).strip().upper() or "MARKET"
        live_requested = bool(record.get("live_execution_enabled", False))
        direct_requested = bool(record.get("direct_execution", False))

        side = "BUY" if direction in {"BUY", "LONG", "ENTER_BUY"} else "SELL" if direction in {"SELL", "SHORT", "ENTER_SELL"} else "WAIT"
        risk_distance = abs(reference - stop) if reference > 0 and stop > 0 else 0.0
        reward_distance = abs(target - reference) if reference > 0 and target > 0 else 0.0
        ratio = round(reward_distance / risk_distance, 4) if risk_distance > 0 else 0.0

        blocks: list[str] = []
        checks = (
            (broker == "XM", "xm_only_policy"),
            (symbol == "GOLD#", "gold_only_policy"),
            (readiness == "READY_FOR_SIMULATION", "execution_not_ready_for_simulation"),
            (portfolio_decision in {"ENTER", "BUY", "SELL"}, "portfolio_decision_not_entry"),
            (side in {"BUY", "SELL"}, "entry_direction_missing"),
            (units > 0, "approved_units_missing"),
            (abs(lot_per_unit - 0.01) <= 1e-12, "fixed_unit_policy"),
            (reference > 0, "reference_price_missing"),
            (stop > 0 and target > 0, "protective_prices_missing"),
            (side != "BUY" or (stop < reference < target), "buy_price_structure_invalid"),
            (side != "SELL" or (target < reference < stop), "sell_price_structure_invalid"),
            (ratio >= float(record.get("minimum_reward_risk_ratio", 1.0) or 1.0), "reward_risk_below_minimum"),
            (order_type in {"MARKET", "LIMIT", "STOP"}, "unsupported_order_type"),
            (not live_requested and not direct_requested, "live_or_direct_execution_requested"),
        )
        for ok, reason in checks:
            if not ok:
                blocks.append(reason)

        if blocks:
            status = "BLOCKED"
            plan_status = "ENTRY_PLAN_BLOCKED"
            reason = blocks[0]
            ready = False
            entry_en = "No entry instruction was approved."
            entry_th = "ยังไม่มีการอนุมัติคำสั่งจำลองสำหรับจุดเข้า"
            wait_en = "Smart Entry is waiting because one or more entry protection or policy checks failed."
            wait_th = "Smart Entry กำลังรอ เนื่องจากเงื่อนไขด้านการป้องกันความเสี่ยงหรือนโยบายบางข้อไม่ผ่าน"
            next_en = "Correct the listed block reasons and evaluate the entry plan again."
            next_th = "แก้ไขเหตุผลที่ถูกบล็อก แล้วประเมินแผนจุดเข้าอีกครั้ง"
        else:
            status = "READY"
            plan_status = "SIMULATION_ENTRY_INSTRUCTION_READY"
            reason = "smart_entry_plan_ready_for_simulation"
            ready = True
            entry_en = f"Prepare a {order_type} {side} simulation instruction for {units} fixed unit(s) with validated stop loss and take profit."
            entry_th = f"เตรียมคำสั่งจำลอง {order_type} ฝั่ง {side} จำนวน {units} Unit คงที่ พร้อม Stop Loss และ Take Profit ที่ผ่านการตรวจสอบ"
            wait_en = "No entry-planning wait remains; live order transmission remains disabled."
            wait_th = "ไม่มีเงื่อนไขที่ต้องรอสำหรับแผนจุดเข้า แต่การส่งคำสั่งจริงยังปิดอยู่"
            next_en = "Pass the simulation instruction to the paper/demo order adapter only."
            next_th = "ส่งคำสั่งจำลองไปยัง Paper/Demo Order Adapter เท่านั้น"

        return SmartEntryReport(
            status=status,
            reason=reason,
            entry_plan_status=plan_status,
            order_side=side,
            order_type=order_type,
            reference_price=reference,
            stop_loss_price=stop,
            take_profit_price=target,
            risk_distance=round(risk_distance, 6),
            reward_distance=round(reward_distance, 6),
            reward_risk_ratio=ratio,
            unit_count=units,
            total_lot=round(units * 0.01, 2),
            simulation_instruction_ready=ready,
            no_order_sent=True,
            block_reasons=tuple(blocks),
            entry_reason_en=entry_en,
            entry_reason_th=entry_th,
            waiting_reason_en=wait_en,
            waiting_reason_th=wait_th,
            expected_next_action_en=next_en,
            expected_next_action_th=next_th,
            next_review_time_utc=(now.astimezone(timezone.utc) + timedelta(minutes=2)).isoformat(),
            broker=broker,
            symbol=symbol,
            lot_per_unit=0.01,
        )

    def explain_one(self, record: Mapping[str, Any]) -> SmartEntryReport:
        return self.evaluate_one(record)
