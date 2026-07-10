from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from .models import PortfolioDecision, PortfolioDecisionReport


class PortfolioDecisionRuntime:
    """Combine entry, position-management, exposure, and risk context without executing orders."""

    ACTION_PRIORITY = {"EXIT": 0, "PARTIAL_CLOSE": 1, "MOVE_STOP_LOSS": 2, "TRAIL_STOP": 3, "CHANGE_TAKE_PROFIT": 4, "ENTER": 5, "HOLD": 6, "WAIT": 7}

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

    @staticmethod
    def _mapping(value: Any) -> Mapping[str, Any]:
        return value if isinstance(value, Mapping) else {}

    def evaluate_one(self, record: Mapping[str, Any]) -> PortfolioDecisionReport:
        now = record.get("current_time_utc") or datetime.now(timezone.utc)
        if not isinstance(now, datetime):
            now = datetime.fromisoformat(str(now).replace("Z", "+00:00"))

        portfolio_id = str(record.get("portfolio_id", "AFIP_GOLD_PORTFOLIO"))
        symbol = str(record.get("symbol", "GOLD#")).upper()
        current_units = self._integer(record.get("current_units", record.get("portfolio_units", 0)))
        maximum_units = max(1, self._integer(record.get("maximum_units", record.get("profile_max_units", 1)), 1))
        available_units = max(0, maximum_units - current_units)
        risk_allowed = self._bool(record.get("risk_allowed", True), True)
        exposure_allowed = self._bool(record.get("exposure_allowed", current_units <= maximum_units), current_units <= maximum_units)

        entry = self._mapping(record.get("entry_validation"))
        exit_ctx = self._mapping(record.get("exit_validation"))
        entry_approved = self._bool(entry.get("entry_approved", record.get("entry_approved", False)), False)
        entry_units = self._integer(entry.get("approved_units", record.get("entry_units", 0)))
        entry_direction = str(entry.get("selected_direction", record.get("entry_direction", "WAIT"))).upper()
        exit_action = str(exit_ctx.get("approved_action", record.get("approved_exit_action", "HOLD"))).upper()
        exit_units = self._integer(exit_ctx.get("approved_units", record.get("exit_units", current_units)))
        exit_ready = self._bool(exit_ctx.get("action_approved", record.get("exit_action_approved", exit_action != "HOLD")), exit_action != "HOLD")

        blocks: list[str] = []
        if symbol != "GOLD#":
            blocks.append("version1_gold_only_required")
        if not risk_allowed:
            blocks.append("portfolio_risk_policy_blocks_decision")
        if not exposure_allowed:
            blocks.append("portfolio_exposure_limit_exceeded")

        decision = "WAIT"
        direction = "WAIT"
        approved_units = 0
        position_action_allowed = False
        entry_allowed = False

        if current_units > 0 and exit_ready and exit_action in {"EXIT", "PARTIAL_CLOSE", "MOVE_STOP_LOSS", "CHANGE_TAKE_PROFIT", "TRAIL_STOP"}:
            decision = exit_action
            direction = str(record.get("position_direction", "MANAGE")).upper()
            approved_units = min(current_units, exit_units or current_units)
            position_action_allowed = risk_allowed or exit_action == "EXIT"
            if exit_action in {"PARTIAL_CLOSE", "EXIT"} and approved_units <= 0:
                blocks.append("portfolio_exit_units_required")
            if not position_action_allowed:
                blocks.append("portfolio_position_action_not_allowed")
        elif current_units > 0:
            decision = "HOLD"
            direction = str(record.get("position_direction", "HOLD")).upper()
            approved_units = current_units
            position_action_allowed = risk_allowed and exposure_allowed
            if not position_action_allowed:
                blocks.append("portfolio_hold_not_allowed")
        elif entry_approved:
            decision = "ENTER"
            direction = entry_direction
            approved_units = min(entry_units, available_units)
            entry_allowed = risk_allowed and exposure_allowed and available_units > 0 and entry_direction in {"BUY", "SELL"} and approved_units > 0
            if available_units <= 0:
                blocks.append("portfolio_has_no_available_units")
            if entry_units > available_units:
                blocks.append("entry_units_reduced_to_portfolio_capacity")
            if entry_direction not in {"BUY", "SELL"}:
                blocks.append("portfolio_entry_direction_not_actionable")
            if approved_units <= 0:
                blocks.append("portfolio_entry_units_required")
            if not entry_allowed:
                blocks.append("portfolio_entry_not_allowed")
        else:
            blocks.append("no_approved_entry_or_position_action")

        blocking = [item for item in blocks if item != "entry_units_reduced_to_portfolio_capacity"]
        approved = not blocking and decision != "WAIT"
        if not approved and decision not in {"EXIT"}:
            decision = "WAIT"
            direction = "WAIT"
            approved_units = 0

        if approved:
            explanation_en = f"Portfolio decision {decision} is approved for {approved_units} fixed unit(s); the decision is context only and sends no order."
            explanation_th = f"อนุมัติการตัดสินใจระดับพอร์ต {decision} จำนวน {approved_units} Unit คงที่ โดยเป็นเพียงบริบทและไม่ส่งคำสั่งซื้อขาย"
            status, reason = "READY", "portfolio_decision_ready"
            wait_en, wait_th = "No portfolio decision block is active.", "ไม่มีเงื่อนไขบล็อกการตัดสินใจระดับพอร์ต"
            next_en = f"Pass {decision} context to paper/demo portfolio review; do not execute a live order."
            next_th = f"ส่งบริบท {decision} ไปยังการตรวจสอบพอร์ตแบบ paper/demo และห้ามส่งคำสั่งจริง"
        else:
            explanation_en = "Portfolio decision is waiting because: " + ", ".join(blocks) + "."
            explanation_th = "การตัดสินใจระดับพอร์ตยังรอเนื่องจาก: " + ", ".join(blocks)
            status, reason = "WAITING", "portfolio_decision_blocked_or_incomplete"
            wait_en = "Waiting for portfolio requirements: " + ", ".join(blocks) + "."
            wait_th = "รอเงื่อนไขระดับพอร์ต: " + ", ".join(blocks)
            next_en = "Review entry, exit, risk, exposure, and fixed-unit capacity before the next portfolio decision."
            next_th = "ตรวจสอบจุดเข้า การออก ความเสี่ยง Exposure และความจุ Unit คงที่ก่อนการตัดสินใจระดับพอร์ตครั้งถัดไป"

        decision_item = PortfolioDecision(
            portfolio_id=portfolio_id,
            symbol=symbol,
            current_units=current_units,
            maximum_units=maximum_units,
            available_units=available_units,
            entry_units=entry_units,
            exit_units=exit_units,
            decision=decision,
            direction=direction,
            risk_allowed=risk_allowed,
            exposure_allowed=exposure_allowed,
            entry_allowed=entry_allowed,
            position_action_allowed=position_action_allowed,
            approved=approved,
            block_reasons=tuple(blocks),
            explanation_en=explanation_en,
            explanation_th=explanation_th,
        )
        return PortfolioDecisionReport(
            status=status,
            reason=reason,
            decisions=(decision_item,),
            selected_portfolio_id=portfolio_id,
            portfolio_decision=decision,
            selected_direction=direction,
            approved_units=approved_units,
            current_units=current_units,
            maximum_units=maximum_units,
            available_units=available_units,
            portfolio_risk_status="READY" if risk_allowed and exposure_allowed else "BLOCKED",
            waiting_reason_en=wait_en,
            waiting_reason_th=wait_th,
            expected_next_action_en=next_en,
            expected_next_action_th=next_th,
            next_review_time_utc=(now.astimezone(timezone.utc) + timedelta(minutes=5)).isoformat(),
            direct_execution=False,
        )
