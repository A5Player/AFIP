from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from .models import ExitValidation, ExitValidationReport


class ExitValidationRuntime:
    """Validate management and exit actions without modifying or closing positions."""

    ALLOWED_ACTIONS = {"HOLD", "PARTIAL_CLOSE", "MOVE_STOP_LOSS", "CHANGE_TAKE_PROFIT", "TRAIL_STOP", "EXIT"}

    @staticmethod
    def _bool(value: Any, default: bool = False) -> bool:
        if value is None:
            return default
        if isinstance(value, str):
            return value.strip().upper() in {"TRUE", "1", "YES", "READY", "APPROVED", "ALLOWED", "PASS"}
        return bool(value)

    @staticmethod
    def _integer(value: Any, default: int = 0) -> int:
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return default

    def evaluate_one(self, record: Mapping[str, Any]) -> ExitValidationReport:
        now = record.get("current_time_utc") or datetime.now(timezone.utc)
        if not isinstance(now, datetime):
            now = datetime.fromisoformat(str(now).replace("Z", "+00:00"))

        raw = record.get("open_positions") or record.get("positions") or ()
        if not isinstance(raw, (list, tuple)):
            raw = ()

        market_regime_ready = self._bool(record.get("market_regime_ready", True), True)
        risk_allowed = self._bool(record.get("risk_allowed", True), True)
        timing_allowed = self._bool(record.get("timing_allowed", True), True)
        spread_allowed = self._bool(record.get("spread_allowed", True), True)

        validations: list[ExitValidation] = []
        for index, item in enumerate(raw):
            if not isinstance(item, Mapping):
                continue
            position_id = str(item.get("position_id", item.get("ticket", f"POSITION_{index + 1}")))
            symbol = str(item.get("symbol", "GOLD#")).upper()
            direction = str(item.get("direction", item.get("side", "BUY"))).upper()
            units = self._integer(item.get("units", item.get("position_units", 1)), 1)
            requested = str(item.get("recommended_action", item.get("exit_action", "HOLD"))).upper()
            if requested not in self.ALLOWED_ACTIONS:
                requested = "HOLD"

            stop_protected = self._bool(item.get("stop_protected", item.get("stop_loss_present", True)), True)
            profit_protected = self._bool(item.get("profit_protected", item.get("take_profit_present", True)), True)
            regime_supports_position = self._bool(item.get("regime_supports_position", True), True)
            thesis_valid = self._bool(item.get("trade_thesis_valid", True), True)
            partial_close_available = units > 1 and self._bool(item.get("partial_close_available", True), True)
            new_stop_reduces_risk = self._bool(item.get("new_stop_reduces_risk", True), True)
            new_target_supported = self._bool(item.get("new_target_supported", True), True)
            trailing_supported = self._bool(item.get("trailing_supported", True), True)
            exit_triggered = self._bool(item.get("exit_triggered", not thesis_valid), not thesis_valid)

            hold_allowed = thesis_valid and regime_supports_position and risk_allowed
            partial_allowed = partial_close_available and risk_allowed
            stop_allowed = new_stop_reduces_risk and risk_allowed
            target_allowed = new_target_supported and market_regime_ready
            trail_allowed = trailing_supported and stop_protected and risk_allowed
            exit_allowed = exit_triggered or not thesis_valid or not risk_allowed

            allowed_map = {
                "HOLD": hold_allowed,
                "PARTIAL_CLOSE": partial_allowed,
                "MOVE_STOP_LOSS": stop_allowed,
                "CHANGE_TAKE_PROFIT": target_allowed,
                "TRAIL_STOP": trail_allowed,
                "EXIT": exit_allowed,
            }
            blocks: list[str] = []
            if symbol != "GOLD#":
                blocks.append("version1_gold_only_required")
            if direction not in {"BUY", "SELL"}:
                blocks.append("position_direction_invalid")
            if units <= 0:
                blocks.append("position_units_required")
            if requested in {"CHANGE_TAKE_PROFIT", "TRAIL_STOP"} and not timing_allowed:
                blocks.append("market_timing_blocks_position_change")
            if requested in {"PARTIAL_CLOSE", "EXIT"} and not spread_allowed:
                blocks.append("spread_or_trading_cost_blocks_close_action")
            if not allowed_map[requested]:
                blocks.append(f"{requested.lower()}_requirements_not_met")

            approved = not blocks
            approved_action = requested if approved else "HOLD"
            if approved:
                en = f"{requested} context approved for review; no position is modified or closed."
                th = f"อนุมัติบริบท {requested} สำหรับการตรวจสอบ โดยไม่มีการแก้ไขหรือปิดสถานะจริง"
            else:
                en = "Position action is waiting because: " + ", ".join(blocks) + "."
                th = "การดำเนินการกับสถานะยังรอเนื่องจาก: " + ", ".join(blocks)

            validations.append(ExitValidation(
                position_id=position_id,
                symbol=symbol,
                direction=direction,
                units=units,
                recommended_action=requested,
                hold_allowed=hold_allowed,
                partial_close_allowed=partial_allowed,
                stop_loss_move_allowed=stop_allowed,
                take_profit_change_allowed=target_allowed,
                trailing_stop_allowed=trail_allowed,
                full_exit_allowed=exit_allowed,
                approved_action=approved_action,
                action_approved=approved,
                block_reasons=tuple(blocks),
                explanation_en=en,
                explanation_th=th,
            ))

        validations.sort(key=lambda item: (not item.action_approved, item.position_id))
        selected = validations[0] if validations else None
        if selected:
            status = "READY" if selected.action_approved else "WAITING"
            reason = "exit_validation_ready" if selected.action_approved else "exit_validation_blocked_or_incomplete"
            action = selected.approved_action
            expected_en = f"Pass {action} context to paper/demo position-management review; do not modify a live position."
            expected_th = f"ส่งบริบท {action} ไปยังการตรวจสอบการจัดการสถานะแบบ paper/demo และห้ามแก้ไขสถานะจริง"
        else:
            status, reason, action = "WAITING", "exit_validation_no_open_position", "HOLD"
            expected_en = "Wait for an open paper/demo position before validating management or exit actions."
            expected_th = "รอสถานะ paper/demo ที่เปิดอยู่ก่อนตรวจสอบการจัดการหรือออกจากสถานะ"

        def active_reason(target: str, fallback_en: str, fallback_th: str) -> tuple[str, str]:
            match = next((item for item in validations if item.approved_action == target and item.action_approved), None)
            if match:
                return match.explanation_en, match.explanation_th
            return fallback_en, fallback_th

        hold_en, hold_th = active_reason("HOLD", "Holding is not currently approved or no open position is available.", "ยังไม่อนุมัติการถือสถานะหรือไม่มีสถานะเปิด")
        sl_en, sl_th = active_reason("MOVE_STOP_LOSS", "No approved stop-loss move is active.", "ยังไม่มีการอนุมัติเลื่อน Stop Loss")
        tp_en, tp_th = active_reason("CHANGE_TAKE_PROFIT", "No approved take-profit change is active.", "ยังไม่มีการอนุมัติเปลี่ยน Take Profit")
        trail_en, trail_th = active_reason("TRAIL_STOP", "No approved trailing-stop action is active.", "ยังไม่มีการอนุมัติ Trailing Stop")
        partial_en, partial_th = active_reason("PARTIAL_CLOSE", "No approved partial-close action is active.", "ยังไม่มีการอนุมัติปิดบางส่วน")
        exit_en, exit_th = active_reason("EXIT", "No approved full-exit action is active.", "ยังไม่มีการอนุมัติออกจากสถานะทั้งหมด")

        return ExitValidationReport(
            status=status,
            reason=reason,
            validations=tuple(validations),
            selected_position_id=selected.position_id if selected else "NONE",
            approved_action=action,
            approved_units=selected.units if selected and selected.action_approved else 0,
            holding_reason_en=hold_en,
            holding_reason_th=hold_th,
            stop_loss_move_reason_en=sl_en,
            stop_loss_move_reason_th=sl_th,
            take_profit_change_reason_en=tp_en,
            take_profit_change_reason_th=tp_th,
            trailing_stop_reason_en=trail_en,
            trailing_stop_reason_th=trail_th,
            partial_close_reason_en=partial_en,
            partial_close_reason_th=partial_th,
            exit_reason_en=exit_en,
            exit_reason_th=exit_th,
            expected_next_action_en=expected_en,
            expected_next_action_th=expected_th,
            next_review_time_utc=(now.astimezone(timezone.utc) + timedelta(minutes=5)).isoformat(),
            direct_execution=False,
        )
