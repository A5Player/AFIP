"""Deterministic take-profit review for paper/demo simulation only."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

@dataclass(frozen=True)
class DynamicTakeProfitReport:
    status: str
    reason: str
    action: str
    current_take_profit: float
    proposed_take_profit: float
    reference_price: float
    current_stop_loss: float
    reward_before: float
    reward_after: float
    reward_risk_before: float
    reward_risk_after: float
    change_approved: bool
    simulation_instruction_ready: bool
    no_order_sent: bool
    block_reasons: tuple[str, ...]
    take_profit_change_reason_en: str
    take_profit_change_reason_th: str
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

class DynamicTakeProfitRuntime:
    """Review a proposed take-profit change without modifying a real position."""
    def evaluate_one(self, record: Mapping[str, Any]) -> DynamicTakeProfitReport:
        now = record.get("current_time_utc") or datetime.now(timezone.utc)
        if not isinstance(now, datetime):
            now = datetime.fromisoformat(str(now).replace("Z", "+00:00"))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        side = str(record.get("position_side", record.get("direction", "BUY"))).strip().upper()
        action = str(record.get("take_profit_action", "HOLD")).strip().upper()
        if action not in {"HOLD", "CHANGE_TAKE_PROFIT"}:
            action = "HOLD"
        reference = float(record.get("reference_price", record.get("market_price", 0.0)) or 0.0)
        current_tp = float(record.get("current_take_profit", record.get("take_profit_price", 0.0)) or 0.0)
        proposed_tp = float(record.get("proposed_take_profit", current_tp) or 0.0)
        current_sl = float(record.get("current_stop_loss", record.get("stop_loss_price", 0.0)) or 0.0)
        current_units = max(0, int(record.get("current_units", record.get("position_units", 0)) or 0))
        risk_allowed = bool(record.get("risk_allowed", True))
        timing_allowed = bool(record.get("timing_allowed", True))
        structure_confirmed = bool(record.get("market_structure_confirmed", True))
        thesis_valid = bool(record.get("trade_thesis_valid", True))
        min_rr = float(record.get("minimum_reward_risk", 1.0) or 1.0)
        lot_per_unit = float(record.get("lot_per_unit", 0.01) or 0.01)
        live_requested = bool(record.get("live_execution_enabled", False) or record.get("direct_execution", False))
        risk_distance = abs(reference - current_sl) if reference > 0 and current_sl > 0 else 0.0
        reward_before = abs(current_tp - reference) if reference > 0 and current_tp > 0 else 0.0
        reward_after = abs(proposed_tp - reference) if reference > 0 and proposed_tp > 0 else 0.0
        rr_before = reward_before / risk_distance if risk_distance > 0 else 0.0
        rr_after = reward_after / risk_distance if risk_distance > 0 else 0.0
        blocks: list[str] = []
        checks = (
            (broker == "XM", "xm_only_policy"),
            (symbol == "GOLD#", "gold_only_policy"),
            (side in {"BUY", "SELL"}, "position_side_invalid"),
            (current_units > 0, "open_position_missing"),
            (reference > 0, "reference_price_missing"),
            (current_tp > 0, "current_take_profit_missing"),
            (current_sl > 0, "current_stop_loss_missing"),
            (abs(lot_per_unit - 0.01) <= 1e-12, "fixed_unit_policy"),
            (risk_allowed, "risk_not_approved"),
            (timing_allowed, "timing_not_approved"),
            (thesis_valid, "trade_thesis_invalid"),
            (not live_requested, "live_or_direct_execution_requested"),
        )
        for ok, reason in checks:
            if not ok:
                blocks.append(reason)
        if action == "CHANGE_TAKE_PROFIT":
            if proposed_tp <= 0:
                blocks.append("proposed_take_profit_missing")
            if side == "BUY" and not (proposed_tp > reference):
                blocks.append("buy_take_profit_invalid")
            if side == "SELL" and not (proposed_tp < reference):
                blocks.append("sell_take_profit_invalid")
            if rr_after < min_rr:
                blocks.append("reward_risk_below_minimum")
            if not structure_confirmed:
                blocks.append("market_structure_not_confirmed")
        if blocks:
            status, reason, approved, ready = "BLOCKED", blocks[0], False, False
            change_en = "The take-profit change is blocked until reward, risk, timing, and market-structure checks pass."
            change_th = "ยังไม่อนุมัติการเปลี่ยน Take Profit จนกว่าการตรวจผลตอบแทน ความเสี่ยง เวลา และโครงสร้างตลาดจะผ่านครบ"
            hold_en = "Keep the current take-profit unchanged while the proposal is under review."
            hold_th = "คง Take Profit เดิมไว้ระหว่างทบทวนข้อเสนอ"
            next_en = "Correct the listed block reasons and evaluate the take-profit proposal again."
            next_th = "แก้ไขเหตุผลที่ถูกบล็อก แล้วประเมินข้อเสนอ Take Profit อีกครั้ง"
        elif action == "CHANGE_TAKE_PROFIT":
            status, reason, approved, ready = "READY", "take_profit_change_ready_for_simulation", True, True
            change_en = f"Change the simulated take-profit from {current_tp:.2f} to {proposed_tp:.2f}; reward/risk becomes {rr_after:.2f}."
            change_th = f"เปลี่ยน Take Profit แบบจำลองจาก {current_tp:.2f} ไป {proposed_tp:.2f} โดย Reward/Risk เป็น {rr_after:.2f}"
            hold_en = "Hold the position with the revised simulated profit objective."
            hold_th = "ถือต่อด้วยเป้าหมายกำไรแบบจำลองที่ปรับใหม่"
            next_en = "Pass the instruction to the paper/demo position adapter only."
            next_th = "ส่งคำสั่งไปยัง Paper/Demo Position Adapter เท่านั้น"
        else:
            status, reason, approved, ready = "READY", "current_take_profit_remains_valid", False, False
            change_en = "No take-profit change is requested."
            change_th = "ยังไม่มีคำขอเปลี่ยน Take Profit"
            hold_en = "Keep the current take-profit because the existing objective remains valid."
            hold_th = "คง Take Profit เดิม เนื่องจากเป้าหมายปัจจุบันยังใช้ได้"
            next_en = "Review again when price structure, volatility, or the trade thesis changes."
            next_th = "ทบทวนอีกครั้งเมื่อโครงสร้างราคา ความผันผวน หรือเหตุผลของสถานะเปลี่ยนแปลง"
        return DynamicTakeProfitReport(
            status, reason, action, current_tp, proposed_tp, reference, current_sl,
            round(reward_before, 8), round(reward_after, 8), round(rr_before, 8), round(rr_after, 8),
            approved, ready, True, tuple(blocks), change_en, change_th, hold_en, hold_th,
            next_en, next_th, (now.astimezone(timezone.utc) + timedelta(minutes=2)).isoformat(),
            broker=broker, symbol=symbol,
        )

    def explain_one(self, record: Mapping[str, Any]) -> DynamicTakeProfitReport:
        return self.evaluate_one(record)
