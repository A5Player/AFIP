"""Deterministic stop-loss review for paper/demo simulation only."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

@dataclass(frozen=True)
class DynamicStopLossReport:
    status: str
    reason: str
    action: str
    current_stop_loss: float
    proposed_stop_loss: float
    reference_price: float
    risk_distance_before: float
    risk_distance_after: float
    risk_reduction: float
    move_approved: bool
    simulation_instruction_ready: bool
    no_order_sent: bool
    block_reasons: tuple[str, ...]
    stop_loss_move_reason_en: str
    stop_loss_move_reason_th: str
    holding_reason_en: str
    holding_reason_th: str
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

class DynamicStopLossRuntime:
    """Review a proposed stop-loss move without modifying a real position."""
    def evaluate_one(self, record: Mapping[str, Any]) -> DynamicStopLossReport:
        now = record.get("current_time_utc") or datetime.now(timezone.utc)
        if not isinstance(now, datetime):
            now = datetime.fromisoformat(str(now).replace("Z", "+00:00"))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        side = str(record.get("position_side", record.get("direction", "BUY"))).strip().upper()
        action = str(record.get("stop_loss_action", "HOLD")).strip().upper()
        if action not in {"HOLD", "MOVE_STOP_LOSS"}:
            action = "HOLD"
        reference = float(record.get("reference_price", record.get("market_price", 0.0)) or 0.0)
        current = float(record.get("current_stop_loss", record.get("stop_loss_price", 0.0)) or 0.0)
        proposed = float(record.get("proposed_stop_loss", current) or 0.0)
        current_units = max(0, int(record.get("current_units", record.get("position_units", 0)) or 0))
        risk_allowed = bool(record.get("risk_allowed", True))
        timing_allowed = bool(record.get("timing_allowed", True))
        structure_confirmed = bool(record.get("market_structure_confirmed", True))
        lot_per_unit = float(record.get("lot_per_unit", 0.01) or 0.01)
        live_requested = bool(record.get("live_execution_enabled", False) or record.get("direct_execution", False))
        before = abs(reference - current) if reference > 0 and current > 0 else 0.0
        after = abs(reference - proposed) if reference > 0 and proposed > 0 else 0.0
        reduction = before - after
        blocks: list[str] = []
        checks = (
            (broker == "XM", "xm_only_policy"),
            (symbol == "GOLD#", "gold_only_policy"),
            (side in {"BUY", "SELL"}, "position_side_invalid"),
            (current_units > 0, "open_position_missing"),
            (reference > 0, "reference_price_missing"),
            (current > 0, "current_stop_loss_missing"),
            (abs(lot_per_unit - 0.01) <= 1e-12, "fixed_unit_policy"),
            (risk_allowed, "risk_not_approved"),
            (timing_allowed, "timing_not_approved"),
            (not live_requested, "live_or_direct_execution_requested"),
        )
        for ok, reason in checks:
            if not ok:
                blocks.append(reason)
        if action == "MOVE_STOP_LOSS":
            if proposed <= 0:
                blocks.append("proposed_stop_loss_missing")
            if side == "BUY" and not (current < proposed < reference):
                blocks.append("buy_stop_loss_move_invalid")
            if side == "SELL" and not (reference < proposed < current):
                blocks.append("sell_stop_loss_move_invalid")
            if reduction <= 0:
                blocks.append("stop_loss_move_must_reduce_risk")
            if not structure_confirmed:
                blocks.append("market_structure_not_confirmed")
        if blocks:
            status, reason, approved, ready = "BLOCKED", blocks[0], False, False
            move_en = "The stop-loss move is blocked until all risk and structure checks pass."
            move_th = "ยังไม่อนุมัติการเลื่อน Stop Loss จนกว่าการตรวจความเสี่ยงและโครงสร้างตลาดจะผ่านครบ"
            hold_en = "Keep the current stop-loss unchanged while the proposal is under review."
            hold_th = "คง Stop Loss เดิมไว้ระหว่างทบทวนข้อเสนอ"
            next_en = "Correct the listed block reasons and evaluate the stop-loss proposal again."
            next_th = "แก้ไขเหตุผลที่ถูกบล็อก แล้วประเมินข้อเสนอ Stop Loss อีกครั้ง"
        elif action == "MOVE_STOP_LOSS":
            status, reason, approved, ready = "READY", "stop_loss_move_ready_for_simulation", True, True
            move_en = f"Move the simulated stop-loss from {current:.2f} to {proposed:.2f}; risk distance decreases by {reduction:.2f}."
            move_th = f"เลื่อน Stop Loss แบบจำลองจาก {current:.2f} ไป {proposed:.2f} โดยระยะความเสี่ยงลดลง {reduction:.2f}"
            hold_en = "Hold the position with the tighter simulated protection after the move."
            hold_th = "ถือต่อด้วยการป้องกันความเสี่ยงแบบจำลองที่กระชับขึ้นหลังเลื่อน Stop Loss"
            next_en = "Pass the instruction to the paper/demo position adapter only."
            next_th = "ส่งคำสั่งไปยัง Paper/Demo Position Adapter เท่านั้น"
        else:
            status, reason, approved, ready = "READY", "current_stop_loss_remains_valid", False, False
            move_en = "No stop-loss move is requested."
            move_th = "ยังไม่มีคำขอเลื่อน Stop Loss"
            hold_en = "Keep the current stop-loss because the existing protection remains valid."
            hold_th = "คง Stop Loss เดิม เนื่องจากการป้องกันความเสี่ยงปัจจุบันยังใช้ได้"
            next_en = "Review again when price structure, volatility, or risk changes."
            next_th = "ทบทวนอีกครั้งเมื่อโครงสร้างราคา ความผันผวน หรือความเสี่ยงเปลี่ยนแปลง"
        return DynamicStopLossReport(
            status, reason, action, current, proposed, reference, round(before, 8), round(after, 8), round(reduction, 8),
            approved, ready, True, tuple(blocks), move_en, move_th, hold_en, hold_th, next_en, next_th,
            (now.astimezone(timezone.utc) + timedelta(minutes=2)).isoformat(), broker=broker, symbol=symbol,
        )

    def explain_one(self, record: Mapping[str, Any]) -> DynamicStopLossReport:
        return self.evaluate_one(record)
