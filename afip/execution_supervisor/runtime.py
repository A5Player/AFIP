"""Deterministic execution supervision for locked paper/demo simulation only."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

_ACTION_PRIORITY = {
    "EMERGENCY_EXIT": 700,
    "EXIT": 600,
    "PARTIAL_CLOSE": 500,
    "TRAIL_STOP": 400,
    "MOVE_STOP_LOSS": 300,
    "CHANGE_TAKE_PROFIT": 200,
    "ENTRY": 100,
    "HOLD": 0,
}


@dataclass(frozen=True)
class ExecutionSupervisorReport:
    status: str
    reason: str
    supervisor_readiness: str
    requested_actions: tuple[str, ...]
    approved_action: str
    rejected_actions: tuple[str, ...]
    conflict_detected: bool
    conflict_resolution: str
    position_state: str
    position_side: str
    current_units: int
    approved_units: int
    entry_allowed: bool
    position_management_allowed: bool
    risk_valid: bool
    timing_valid: bool
    trading_cost_valid: bool
    market_structure_confirmed: bool
    market_regime_confirmed: bool
    dependency_reports_valid: bool
    simulation_instruction_ready: bool
    no_order_sent: bool
    block_reasons: tuple[str, ...]
    supervision_reason_en: str
    supervision_reason_th: str
    holding_reason_en: str
    holding_reason_th: str
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


class ExecutionSupervisorRuntime:
    """Resolve execution-intelligence proposals into one non-executing instruction."""

    def evaluate_one(self, record: Mapping[str, Any]) -> ExecutionSupervisorReport:
        now = self._utc_time(record.get("current_time_utc"))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        side = str(record.get("position_side", record.get("direction", "BUY"))).strip().upper()
        state = str(record.get("position_state", "OPEN" if self._integer(record.get("current_units", 0)) > 0 else "FLAT")).strip().upper()
        current_units = max(0, self._integer(record.get("current_units", record.get("position_units", 0))))
        lot_per_unit = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        risk_valid = bool(record.get("risk_allowed", record.get("risk_valid", True)))
        timing_valid = bool(record.get("timing_allowed", record.get("timing_valid", True)))
        cost_valid = bool(record.get("trading_cost_valid", True))
        structure_valid = bool(record.get("market_structure_confirmed", True))
        regime_valid = bool(record.get("market_regime_confirmed", True))
        dependencies_valid = bool(record.get("dependency_reports_valid", True))
        live_requested = bool(record.get("live_execution_enabled", False) or record.get("direct_execution", False))

        requested = self._requested_actions(record)
        conflict = len([action for action in requested if action != "HOLD"]) > 1
        approved = max(requested, key=lambda item: _ACTION_PRIORITY[item]) if requested else "HOLD"
        rejected = tuple(action for action in requested if action != approved)

        blocks: list[str] = []
        checks = (
            (broker == "XM", "xm_only_policy"),
            (symbol == "GOLD#", "gold_only_policy"),
            (side in {"BUY", "SELL"}, "position_side_invalid"),
            (abs(lot_per_unit - 0.01) <= 1e-12, "fixed_unit_policy"),
            (risk_valid, "risk_not_approved"),
            (timing_valid, "timing_not_approved"),
            (cost_valid, "trading_cost_not_approved"),
            (structure_valid, "market_structure_not_confirmed"),
            (regime_valid, "market_regime_not_confirmed"),
            (dependencies_valid, "dependency_reports_invalid"),
            (not live_requested, "live_or_direct_execution_requested"),
        )
        for passed, reason in checks:
            if not passed:
                blocks.append(reason)

        entry_allowed = state == "FLAT" and current_units == 0
        management_allowed = state == "OPEN" and current_units > 0
        if approved == "ENTRY" and not entry_allowed:
            blocks.append("entry_requires_flat_position")
        if approved in {"EXIT", "EMERGENCY_EXIT", "PARTIAL_CLOSE", "TRAIL_STOP", "MOVE_STOP_LOSS", "CHANGE_TAKE_PROFIT"} and not management_allowed:
            blocks.append("position_management_requires_open_position")

        approved_units = 0
        if approved == "ENTRY":
            approved_units = max(0, self._integer(record.get("entry_units", record.get("approved_entry_units", 0))))
            if approved_units <= 0:
                blocks.append("entry_units_missing")
        elif approved == "PARTIAL_CLOSE":
            approved_units = max(0, self._integer(record.get("approved_close_units", record.get("requested_close_units", 0))))
            if approved_units <= 0 or approved_units >= current_units:
                blocks.append("partial_close_units_invalid")
        elif approved in {"EXIT", "EMERGENCY_EXIT"}:
            approved_units = current_units

        blocks = list(dict.fromkeys(blocks))
        instruction_ready = not blocks and approved != "HOLD"
        if blocks:
            status, reason, readiness = "BLOCKED", blocks[0], "NOT_READY"
            sup_en = "The supervisor blocked the proposal because at least one execution, policy, dependency, or position-state requirement failed."
            sup_th = "Execution Supervisor บล็อกข้อเสนอ เนื่องจากมีเงื่อนไขด้านการดำเนินการ นโยบาย ระบบที่เกี่ยวข้อง หรือสถานะ Position อย่างน้อยหนึ่งข้อไม่ผ่าน"
            hold_en = "Hold the current state and send no order while the blocking reasons remain."
            hold_th = "คงสถานะปัจจุบันและไม่ส่งคำสั่ง ระหว่างที่เหตุผลการบล็อกยังไม่ถูกแก้ไข"
            next_en = "Correct the blocking inputs and run supervision again."
            next_th = "แก้ไขข้อมูลที่ถูกบล็อก แล้วประเมินผ่าน Supervisor อีกครั้ง"
        elif approved == "HOLD":
            status, reason, readiness = "READY", "supervisor_monitoring_no_action", "MONITORING"
            sup_en = "All supervisory controls are available, but no executable simulation action has priority."
            sup_th = "ระบบควบคุมพร้อมใช้งาน แต่ยังไม่มี Action สำหรับการจำลองที่มีลำดับความสำคัญ"
            hold_en = "Maintain the current position state and continue monitoring."
            hold_th = "คงสถานะ Position ปัจจุบันและติดตามต่อ"
            next_en = "Review again when a validated execution-intelligence proposal changes."
            next_th = "ทบทวนอีกครั้งเมื่อข้อเสนอจาก Execution Intelligence ที่ผ่านการตรวจเปลี่ยนแปลง"
        else:
            status, reason, readiness = "READY", "simulation_instruction_supervised", "READY"
            sup_en = f"The supervisor selected {approved} as the single highest-priority paper/demo instruction."
            sup_th = f"Execution Supervisor เลือก {approved} เป็นคำแนะนำ Paper/Demo เพียงรายการเดียวที่มีลำดับความสำคัญสูงสุด"
            hold_en = "Do not perform any rejected or lower-priority action during this review cycle."
            hold_th = "ห้ามดำเนินการ Action ที่ถูกปฏิเสธหรือมีลำดับต่ำกว่าในรอบทบทวนนี้"
            next_en = "Pass the supervised instruction to the simulation adapter only; keep live execution disabled."
            next_th = "ส่งคำแนะนำที่ผ่าน Supervisor ไปยัง Simulation Adapter เท่านั้น และคงการปิด Live Execution"

        confidence = self._confidence(risk_valid, timing_valid, cost_valid, structure_valid, regime_valid, dependencies_valid, bool(blocks), conflict)
        review_seconds = max(30, self._integer(record.get("next_review_seconds", 60)) or 60)
        resolution = "highest_financial_risk_priority_selected" if conflict else "no_action_conflict"
        return ExecutionSupervisorReport(
            status=status, reason=reason, supervisor_readiness=readiness,
            requested_actions=requested or ("HOLD",), approved_action=approved,
            rejected_actions=rejected, conflict_detected=conflict,
            conflict_resolution=resolution, position_state=state, position_side=side,
            current_units=current_units, approved_units=approved_units,
            entry_allowed=entry_allowed, position_management_allowed=management_allowed,
            risk_valid=risk_valid, timing_valid=timing_valid, trading_cost_valid=cost_valid,
            market_structure_confirmed=structure_valid, market_regime_confirmed=regime_valid,
            dependency_reports_valid=dependencies_valid, simulation_instruction_ready=instruction_ready,
            no_order_sent=True, block_reasons=tuple(blocks),
            supervision_reason_en=sup_en, supervision_reason_th=sup_th,
            holding_reason_en=hold_en, holding_reason_th=hold_th,
            expected_next_action_en=next_en, expected_next_action_th=next_th,
            confidence=confidence, next_review_time_utc=(now + timedelta(seconds=review_seconds)).isoformat(),
            broker=broker, symbol=symbol,
        )

    def explain_one(self, record: Mapping[str, Any]) -> ExecutionSupervisorReport:
        return self.evaluate_one(record)

    @staticmethod
    def _requested_actions(record: Mapping[str, Any]) -> tuple[str, ...]:
        raw = record.get("requested_actions")
        values: list[str] = []
        if isinstance(raw, str):
            values.extend(part.strip().upper() for part in raw.split(",") if part.strip())
        elif isinstance(raw, (list, tuple, set)):
            values.extend(str(part).strip().upper() for part in raw if str(part).strip())
        field_map = {
            "entry_action": "ENTRY", "smart_entry_action": "ENTRY",
            "exit_action": "EXIT", "smart_exit_action": "EXIT",
            "partial_close_action": "PARTIAL_CLOSE", "trailing_stop_action": "TRAIL_STOP",
            "stop_loss_action": "MOVE_STOP_LOSS", "take_profit_action": "CHANGE_TAKE_PROFIT",
        }
        for field, normalized in field_map.items():
            value = str(record.get(field, "")).strip().upper()
            if value in {normalized, "READY", "APPROVED"}:
                values.append(normalized)
        normalized_values = [value for value in values if value in _ACTION_PRIORITY]
        return tuple(dict.fromkeys(normalized_values))

    @staticmethod
    def _number(value: Any) -> float:
        try: return float(value or 0.0)
        except (TypeError, ValueError): return 0.0

    @staticmethod
    def _integer(value: Any) -> int:
        try: return int(value or 0)
        except (TypeError, ValueError): return 0

    @staticmethod
    def _utc_time(value: Any) -> datetime:
        if isinstance(value, datetime): return value.astimezone(timezone.utc)
        if isinstance(value, str) and value.strip():
            try: return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
            except ValueError: pass
        return datetime.now(timezone.utc)

    @staticmethod
    def _confidence(risk: bool, timing: bool, cost: bool, structure: bool, regime: bool, dependencies: bool, blocked: bool, conflict: bool) -> float:
        score = sum((risk, timing, cost, structure, regime, dependencies)) / 6 * 100.0
        if blocked: score = min(score, 49.0)
        elif conflict: score = max(0.0, score - 5.0)
        return round(score, 2)
