"""Deterministic paper decision ledger for Milestone L Pack 3."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Any, Mapping

_ALLOWED_ACTIONS = {"HOLD", "ENTRY", "FULL_EXIT", "PARTIAL_CLOSE", "MOVE_STOP_LOSS", "CHANGE_TAKE_PROFIT", "TRAILING_STOP", "NO_ACTION"}


@dataclass(frozen=True)
class PaperDecisionLedgerReport:
    status: str
    reason: str
    milestone: str
    pack: str
    ledger_readiness: str
    decision_id: str
    session_ready: bool
    decision_recorded: bool
    approved_action: str
    position_state: str
    direction: str
    requested_units: int
    recorded_units: int
    trade_plan_id: str
    independent_trade_plan_valid: bool
    protected_runner: bool
    protected_runner_excluded_from_new_entry_count: bool
    total_exposure_included: bool
    market_context_recorded: bool
    news_context_recorded: bool
    confidence_breakdown_recorded: bool
    rejected_alternatives_recorded: bool
    version_context_recorded: bool
    outcome_tracking_ready: bool
    traditional_dca_disabled: bool
    averaging_down_disabled: bool
    simulation_lock_valid: bool
    direct_execution_blocked: bool
    live_execution_blocked: bool
    no_order_sent_valid: bool
    block_reasons: tuple[str, ...]
    decision_reason_en: str
    decision_reason_th: str
    holding_reason_en: str
    holding_reason_th: str
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


class PaperDecisionLedgerRuntime:
    """Record an explainable paper decision without transmitting an order."""

    def evaluate_one(self, record: Mapping[str, Any]) -> PaperDecisionLedgerReport:
        now = self._utc_time(record.get("current_time_utc"))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        action = str(record.get("approved_action", "HOLD")).strip().upper() or "HOLD"
        position_state = str(record.get("position_state", "FLAT")).strip().upper() or "FLAT"
        direction = str(record.get("direction", "NONE")).strip().upper() or "NONE"
        requested_units = max(0, self._integer(record.get("requested_units", 0)))
        trade_plan_id = str(record.get("trade_plan_id", "PAPER-PLAN-UNASSIGNED")).strip() or "PAPER-PLAN-UNASSIGNED"
        protected_runner = bool(record.get("protected_runner", False))
        session_status = str(record.get("paper_execution_session_status", record.get("session_status", "READY"))).strip().upper()
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        action_position_valid = not ((action == "ENTRY" and position_state != "FLAT") or (action in _ALLOWED_ACTIONS - {"ENTRY", "HOLD", "NO_ACTION"} and position_state != "OPEN"))
        units_valid = requested_units > 0 if action in {"ENTRY", "PARTIAL_CLOSE"} else requested_units >= 0
        plan_valid = bool(record.get("independent_trade_plan_valid", True)) and (trade_plan_id != "PAPER-PLAN-UNASSIGNED" or action in {"HOLD", "NO_ACTION"})
        checks = {
            "paper_execution_session_not_ready": session_status in {"READY", "CERTIFIED", "COMPLETE"},
            "approved_action_invalid": action in _ALLOWED_ACTIONS,
            "action_position_mismatch": action_position_valid,
            "requested_units_invalid": units_valid,
            "independent_trade_plan_invalid": plan_valid,
            "market_context_missing": bool(record.get("market_context_recorded", True)),
            "news_context_missing": bool(record.get("news_context_recorded", True)),
            "confidence_breakdown_missing": bool(record.get("confidence_breakdown_recorded", True)),
            "rejected_alternatives_missing": bool(record.get("rejected_alternatives_recorded", True)),
            "version_context_missing": bool(record.get("version_context_recorded", True)),
            "outcome_tracking_not_ready": bool(record.get("outcome_tracking_ready", True)),
            "total_exposure_excluded": bool(record.get("total_exposure_included", True)),
            "traditional_dca_enabled": not bool(record.get("traditional_dca_enabled", False)),
            "averaging_down_enabled": not bool(record.get("averaging_down_enabled", False)),
            "xm_only_policy": broker == "XM",
            "gold_only_policy": symbol == "GOLD#",
            "fixed_unit_policy": abs(lot - 0.01) <= 1e-12,
            "simulation_lock_missing": execution_status == "LOCKED_SIMULATION_ONLY",
            "direct_execution_requested": not bool(record.get("direct_execution", False)),
            "live_execution_requested": not bool(record.get("live_execution_enabled", False)),
            "order_status_not_safe": order_status == "NO_ORDER_SENT",
        }
        blocks = tuple(name for name, passed in checks.items() if not passed)
        payload = {
            "action": action, "position_state": position_state, "direction": direction,
            "units": requested_units, "trade_plan_id": trade_plan_id, "protected_runner": protected_runner,
            "checks": checks, "broker": broker, "symbol": symbol, "lot": lot,
        }
        decision_id = "L03-" + sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        if not blocks:
            status, reason, readiness = "READY", "paper_decision_recorded", "PAPER_DECISION_LEDGER_READY"
            en = "The paper decision, its evidence, rejected alternatives, versions, and outcome-tracking context are recorded without transmitting an order."
            th = "บันทึกการตัดสินใจแบบ Paper พร้อมหลักฐาน ทางเลือกที่ปฏิเสธ เวอร์ชัน และบริบทติดตามผล โดยไม่ส่งคำสั่งซื้อขาย"
            hold_en = "Manage every position independently; protected runners may be excluded from the new-entry ticket count but remain included in total exposure and risk."
            hold_th = "บริหารแต่ละ Position แยกกัน โดย Protected Runner อาจไม่นับในโควตาไม้ใหม่ แต่ยังนับใน Exposure และความเสี่ยงรวม"
            next_en = "Track the market outcome and attach it to this deterministic decision ID."
            next_th = "ติดตามผลลัพธ์ตลาดและเชื่อมผลเข้ากับ Decision ID แบบกำหนดแน่นอนนี้"
        else:
            status, reason, readiness = "BLOCKED", blocks[0], "PAPER_DECISION_LEDGER_BLOCKED"
            en = "The paper decision was not accepted because at least one session, decision, context, policy, or execution-safety requirement failed."
            th = "ไม่รับบันทึกการตัดสินใจแบบ Paper เพราะข้อกำหนดด้าน Session, Decision, Context, นโยบาย หรือความปลอดภัยอย่างน้อยหนึ่งรายการไม่ผ่าน"
            hold_en = "Preserve the existing position state and all execution locks."
            hold_th = "คงสถานะ Position เดิมและการล็อก Execution ทั้งหมด"
            next_en = "Correct every block reason and create a complete independent paper decision record."
            next_th = "แก้ไข Block Reason ทั้งหมดและสร้างบันทึก Paper Decision แบบอิสระให้ครบถ้วน"
        review = max(30, self._integer(record.get("next_review_seconds", 60)) or 60)
        return PaperDecisionLedgerReport(
            status=status, reason=reason, milestone="MILESTONE_L", pack="PACK_3", ledger_readiness=readiness,
            decision_id=decision_id, session_ready=checks["paper_execution_session_not_ready"], decision_recorded=not blocks,
            approved_action=action, position_state=position_state, direction=direction, requested_units=requested_units,
            recorded_units=requested_units if not blocks else 0, trade_plan_id=trade_plan_id,
            independent_trade_plan_valid=checks["independent_trade_plan_invalid"], protected_runner=protected_runner,
            protected_runner_excluded_from_new_entry_count=protected_runner and bool(record.get("profit_locked", True)),
            total_exposure_included=checks["total_exposure_excluded"], market_context_recorded=checks["market_context_missing"],
            news_context_recorded=checks["news_context_missing"], confidence_breakdown_recorded=checks["confidence_breakdown_missing"],
            rejected_alternatives_recorded=checks["rejected_alternatives_missing"], version_context_recorded=checks["version_context_missing"],
            outcome_tracking_ready=checks["outcome_tracking_not_ready"], traditional_dca_disabled=checks["traditional_dca_enabled"],
            averaging_down_disabled=checks["averaging_down_enabled"], simulation_lock_valid=checks["simulation_lock_missing"],
            direct_execution_blocked=checks["direct_execution_requested"], live_execution_blocked=checks["live_execution_requested"],
            no_order_sent_valid=checks["order_status_not_safe"], block_reasons=blocks, decision_reason_en=en, decision_reason_th=th,
            holding_reason_en=hold_en, holding_reason_th=hold_th, expected_next_action_en=next_en,
            expected_next_action_th=next_th, confidence=round(sum(checks.values()) / len(checks) * 100.0, 2),
            next_review_time_utc=(now + timedelta(seconds=review)).isoformat(), broker=broker, symbol=symbol,
            lot_per_unit=lot, execution_status=execution_status,
        )

    def explain_one(self, record: Mapping[str, Any]) -> PaperDecisionLedgerReport:
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
            return value.astimezone(timezone.utc)
        if isinstance(value, str) and value.strip():
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
            except ValueError:
                pass
        return datetime.now(timezone.utc)
