"""Deterministic smart-exit planning for paper/demo simulation only."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

@dataclass(frozen=True)
class SmartExitReport:
    status: str
    reason: str
    exit_plan_status: str
    action: str
    current_units: int
    close_units: int
    remaining_units: int
    reference_price: float
    stop_loss_price: float
    take_profit_price: float
    unrealized_pnl: float
    simulation_instruction_ready: bool
    no_order_sent: bool
    block_reasons: tuple[str, ...]
    holding_reason_en: str
    holding_reason_th: str
    partial_close_reason_en: str
    partial_close_reason_th: str
    exit_reason_en: str
    exit_reason_th: str
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

class SmartExitRuntime:
    """Build an explainable exit instruction without changing a real position."""
    def evaluate_one(self, record: Mapping[str, Any]) -> SmartExitReport:
        now = record.get("current_time_utc") or datetime.now(timezone.utc)
        if not isinstance(now, datetime):
            now = datetime.fromisoformat(str(now).replace("Z", "+00:00"))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        decision = str(record.get("portfolio_decision", record.get("exit_action", "HOLD"))).strip().upper()
        action = decision if decision in {"HOLD", "PARTIAL_CLOSE", "EXIT"} else "HOLD"
        current_units = max(0, int(record.get("current_units", record.get("position_units", 0)) or 0))
        close_units = max(0, int(record.get("close_units", 1 if action == "PARTIAL_CLOSE" else current_units if action == "EXIT" else 0) or 0))
        reference = float(record.get("reference_price", record.get("market_price", 0.0)) or 0.0)
        stop = float(record.get("stop_loss_price", record.get("stop_loss", 0.0)) or 0.0)
        target = float(record.get("take_profit_price", record.get("take_profit", 0.0)) or 0.0)
        pnl = float(record.get("unrealized_pnl", 0.0) or 0.0)
        thesis_valid = bool(record.get("trade_thesis_valid", True))
        risk_allowed = bool(record.get("risk_allowed", True))
        timing_allowed = bool(record.get("timing_allowed", True))
        cost_allowed = bool(record.get("trading_cost_allowed", True))
        lot_per_unit = float(record.get("lot_per_unit", 0.01) or 0.01)
        live_requested = bool(record.get("live_execution_enabled", False) or record.get("direct_execution", False))
        blocks: list[str] = []
        checks = (
            (broker == "XM", "xm_only_policy"),
            (symbol == "GOLD#", "gold_only_policy"),
            (current_units > 0, "open_position_missing"),
            (abs(lot_per_unit - 0.01) <= 1e-12, "fixed_unit_policy"),
            (reference > 0, "reference_price_missing"),
            (risk_allowed, "risk_not_approved"),
            (timing_allowed, "timing_not_approved"),
            (cost_allowed or action == "HOLD", "trading_cost_not_approved"),
            (action != "PARTIAL_CLOSE" or current_units > 1, "partial_close_requires_multiple_units"),
            (action != "PARTIAL_CLOSE" or 0 < close_units < current_units, "partial_close_units_invalid"),
            (action != "EXIT" or close_units == current_units, "full_exit_units_invalid"),
            (not live_requested, "live_or_direct_execution_requested"),
        )
        for ok, reason in checks:
            if not ok:
                blocks.append(reason)
        if not thesis_valid and action == "HOLD":
            blocks.append("invalid_thesis_requires_exit_review")
        if blocks:
            status, plan, reason, ready = "BLOCKED", "EXIT_PLAN_BLOCKED", blocks[0], False
            hold_en, hold_th = "Hold is not approved while exit checks remain unresolved.", "ยังไม่อนุมัติให้ถือต่อ เนื่องจากเงื่อนไขการออกยังไม่ครบ"
            partial_en, partial_th = "No partial-close instruction was approved.", "ยังไม่มีการอนุมัติคำสั่งปิดบางส่วน"
            exit_en, exit_th = "No exit instruction was approved.", "ยังไม่มีการอนุมัติคำสั่งออกจากสถานะ"
            next_en, next_th = "Correct the listed block reasons and evaluate the exit plan again.", "แก้ไขเหตุผลที่ถูกบล็อก แล้วประเมินแผนออกอีกครั้ง"
        else:
            status, reason, ready = "READY", "smart_exit_plan_ready_for_simulation", True
            plan = f"SIMULATION_{action}_INSTRUCTION_READY"
            if action == "HOLD":
                hold_en, hold_th = "Hold remains valid because the trade thesis and risk controls remain acceptable.", "ถือต่อได้ เนื่องจากเหตุผลการเทรดและการควบคุมความเสี่ยงยังใช้ได้"
                partial_en, partial_th = "Partial close is not requested.", "ยังไม่มีคำขอปิดบางส่วน"
                exit_en, exit_th = "Full exit is not requested.", "ยังไม่มีคำขอออกทั้งหมด"
            elif action == "PARTIAL_CLOSE":
                hold_en, hold_th = "Retain the remaining units after the simulated partial close.", "ถือต่อเฉพาะ Unit ที่เหลือหลังการปิดบางส่วนแบบจำลอง"
                partial_en, partial_th = f"Prepare a simulated partial close of {close_units} unit(s) to reduce exposure.", f"เตรียมปิดบางส่วนแบบจำลองจำนวน {close_units} Unit เพื่อลดความเสี่ยง"
                exit_en, exit_th = "Full exit is not required.", "ยังไม่จำเป็นต้องออกทั้งหมด"
            else:
                hold_en, hold_th = "Holding is no longer selected.", "ไม่ได้เลือกถือต่อ"
                partial_en, partial_th = "Partial close is not selected.", "ไม่ได้เลือกปิดบางส่วน"
                exit_en, exit_th = f"Prepare a simulated full exit of {current_units} unit(s).", f"เตรียมออกจากสถานะทั้งหมดแบบจำลองจำนวน {current_units} Unit"
            next_en, next_th = "Pass the instruction to the paper/demo position adapter only.", "ส่งคำสั่งไปยัง Paper/Demo Position Adapter เท่านั้น"
        remaining = max(0, current_units - close_units) if action in {"PARTIAL_CLOSE", "EXIT"} else current_units
        return SmartExitReport(status, reason, plan, action, current_units, close_units, remaining, reference, stop, target, pnl, ready, True, tuple(blocks), hold_en, hold_th, partial_en, partial_th, exit_en, exit_th, next_en, next_th, (now.astimezone(timezone.utc)+timedelta(minutes=2)).isoformat(), broker=broker, symbol=symbol)

    def explain_one(self, record: Mapping[str, Any]) -> SmartExitReport:
        return self.evaluate_one(record)
