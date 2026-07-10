"""Deterministic paper outcome evaluation for Milestone L Pack 4."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Any, Mapping

_ALLOWED_DIRECTIONS = {"BUY", "SELL", "NONE"}
_ALLOWED_OUTCOME_STATES = {"TRACKING", "CLOSED", "CANCELLED", "EXPIRED"}


@dataclass(frozen=True)
class PaperOutcomeEvaluationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    outcome_readiness: str
    outcome_id: str
    decision_id: str
    decision_link_valid: bool
    outcome_state: str
    direction: str
    entry_price: float
    current_price: float
    exit_price: float
    maximum_favorable_excursion: float
    maximum_adverse_excursion: float
    gross_profit: float
    trading_cost: float
    swap_cost: float
    net_profit: float
    planned_risk_amount: float
    realized_r_multiple: float
    outcome_classification: str
    exit_quality: str
    failure_reason: str
    data_complete: bool
    future_leakage_blocked: bool
    chronological_order_valid: bool
    independent_position_lifecycle_valid: bool
    protected_runner_exposure_included: bool
    traditional_dca_disabled: bool
    averaging_down_disabled: bool
    simulation_lock_valid: bool
    direct_execution_blocked: bool
    live_execution_blocked: bool
    no_order_sent_valid: bool
    block_reasons: tuple[str, ...]
    evaluation_reason_en: str
    evaluation_reason_th: str
    learning_value_en: str
    learning_value_th: str
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


class PaperOutcomeEvaluationRuntime:
    """Attach an auditable market outcome to a paper decision without execution."""

    def evaluate_one(self, record: Mapping[str, Any]) -> PaperOutcomeEvaluationReport:
        now = self._utc_time(record.get("current_time_utc"))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        decision_id = str(record.get("decision_id", "")).strip().upper()
        decision_status = str(record.get("paper_decision_status", record.get("decision_status", "READY"))).strip().upper()
        outcome_state = str(record.get("outcome_state", "TRACKING")).strip().upper() or "TRACKING"
        direction = str(record.get("direction", "NONE")).strip().upper() or "NONE"
        entry_price = self._number(record.get("entry_price", 0.0))
        current_price = self._number(record.get("current_price", entry_price))
        exit_price = self._number(record.get("exit_price", 0.0))
        mfe = max(0.0, self._number(record.get("maximum_favorable_excursion", 0.0)))
        mae = max(0.0, self._number(record.get("maximum_adverse_excursion", 0.0)))
        gross = self._number(record.get("gross_profit", 0.0))
        trading_cost = max(0.0, self._number(record.get("trading_cost", 0.0)))
        swap_cost = max(0.0, self._number(record.get("swap_cost", 0.0)))
        planned_risk = max(0.0, self._number(record.get("planned_risk_amount", 0.0)))
        net_profit = gross - trading_cost - swap_cost
        realized_r = net_profit / planned_risk if planned_risk > 0.0 else 0.0
        decision_time = self._optional_utc_time(record.get("decision_time_utc"))
        outcome_time = self._optional_utc_time(record.get("outcome_time_utc"))
        chronological = decision_time is None or outcome_time is None or outcome_time >= decision_time
        completed = outcome_state in {"CLOSED", "CANCELLED", "EXPIRED"}
        price_data_valid = entry_price > 0.0 and current_price > 0.0 and (not completed or outcome_state != "CLOSED" or exit_price > 0.0)
        data_complete = bool(record.get("data_complete", True)) and price_data_valid
        no_future_leakage = not bool(record.get("future_data_used", False))
        independent_lifecycle = bool(record.get("independent_position_lifecycle_valid", True))
        exposure_included = bool(record.get("protected_runner_exposure_included", True))
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        checks = {
            "paper_decision_not_ready": decision_status in {"READY", "CERTIFIED", "COMPLETE"},
            "decision_id_missing": decision_id.startswith("L03-") and len(decision_id) > 4,
            "outcome_state_invalid": outcome_state in _ALLOWED_OUTCOME_STATES,
            "direction_invalid": direction in _ALLOWED_DIRECTIONS,
            "outcome_data_incomplete": data_complete,
            "future_leakage_detected": no_future_leakage,
            "chronological_order_invalid": chronological,
            "planned_risk_missing": planned_risk > 0.0 if outcome_state == "CLOSED" else planned_risk >= 0.0,
            "independent_position_lifecycle_invalid": independent_lifecycle,
            "protected_runner_exposure_excluded": exposure_included,
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
        if outcome_state == "TRACKING":
            classification = "OPEN_OBSERVATION"
            exit_quality = "NOT_APPLICABLE"
            failure_reason = "NONE"
        elif outcome_state in {"CANCELLED", "EXPIRED"}:
            classification = "NO_TRADE_OUTCOME"
            exit_quality = "NOT_APPLICABLE"
            failure_reason = str(record.get("failure_reason", outcome_state)).strip().upper() or outcome_state
        else:
            classification = "PROFIT" if net_profit > 0.0 else "LOSS" if net_profit < 0.0 else "BREAK_EVEN"
            capture_ratio = (max(0.0, net_profit) / mfe) if mfe > 0.0 else 0.0
            exit_quality = "EXCELLENT" if capture_ratio >= 0.75 else "GOOD" if capture_ratio >= 0.45 else "EARLY" if net_profit > 0.0 else "RISK_EXIT"
            failure_reason = str(record.get("failure_reason", "NONE" if net_profit >= 0.0 else "MARKET_THESIS_FAILED")).strip().upper()
        payload = {
            "decision_id": decision_id,
            "outcome_state": outcome_state,
            "direction": direction,
            "entry_price": entry_price,
            "current_price": current_price,
            "exit_price": exit_price,
            "mfe": mfe,
            "mae": mae,
            "gross": gross,
            "trading_cost": trading_cost,
            "swap_cost": swap_cost,
            "planned_risk": planned_risk,
            "checks": checks,
        }
        outcome_id = "L04-" + sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        if not blocks:
            status, reason, readiness = "READY", "paper_outcome_evaluation_ready", "PAPER_OUTCOME_EVALUATION_READY"
            en = "The paper outcome is linked to its deterministic decision record with chronological, cost, risk, and future-leakage controls."
            th = "เชื่อมผลลัพธ์แบบ Paper เข้ากับบันทึกการตัดสินใจแบบกำหนดแน่นอน พร้อมตรวจลำดับเวลา ต้นทุน ความเสี่ยง และป้องกันการใช้ข้อมูลอนาคต"
            learning_en = "MFE, MAE, net profit, realized R, exit quality, and failure reason are available for later validated learning."
            learning_th = "MFE, MAE, กำไรสุทธิ, Realized R, คุณภาพการออก และสาเหตุความล้มเหลวพร้อมสำหรับการเรียนรู้ที่ต้องผ่านการรับรองภายหลัง"
            next_en = "Continue tracking while open, or close the outcome record and include it in paper performance evaluation."
            next_th = "ติดตามต่อเมื่อสถานะยังเปิด หรือปิดบันทึกผลลัพธ์และนำเข้าสู่การประเมินผลงาน Paper"
        else:
            status, reason, readiness = "BLOCKED", blocks[0], "PAPER_OUTCOME_EVALUATION_BLOCKED"
            en = "The outcome was rejected because its decision link, data, chronology, risk, policy, or execution-safety evidence is incomplete."
            th = "ไม่รับผลลัพธ์เนื่องจากหลักฐานด้านการเชื่อม Decision, ข้อมูล, ลำดับเวลา, ความเสี่ยง, นโยบาย หรือความปลอดภัยของ Execution ไม่ครบ"
            learning_en = "Blocked outcomes must not enter performance statistics or production knowledge."
            learning_th = "ผลลัพธ์ที่ถูกบล็อกห้ามเข้าสถิติผลงานหรือองค์ความรู้ Production"
            next_en = "Correct every block reason and re-evaluate the same paper decision without future information."
            next_th = "แก้ไข Block Reason ทั้งหมดและประเมิน Paper Decision เดิมใหม่โดยไม่ใช้ข้อมูลอนาคต"
        review = max(30, self._integer(record.get("next_review_seconds", 60)) or 60)
        return PaperOutcomeEvaluationReport(
            status=status, reason=reason, milestone="MILESTONE_L", pack="PACK_4", outcome_readiness=readiness,
            outcome_id=outcome_id, decision_id=decision_id, decision_link_valid=checks["decision_id_missing"],
            outcome_state=outcome_state, direction=direction, entry_price=entry_price, current_price=current_price,
            exit_price=exit_price, maximum_favorable_excursion=round(mfe, 8), maximum_adverse_excursion=round(mae, 8),
            gross_profit=round(gross, 8), trading_cost=round(trading_cost, 8), swap_cost=round(swap_cost, 8),
            net_profit=round(net_profit, 8), planned_risk_amount=round(planned_risk, 8),
            realized_r_multiple=round(realized_r, 4), outcome_classification=classification, exit_quality=exit_quality,
            failure_reason=failure_reason, data_complete=data_complete, future_leakage_blocked=no_future_leakage,
            chronological_order_valid=chronological, independent_position_lifecycle_valid=independent_lifecycle,
            protected_runner_exposure_included=exposure_included, traditional_dca_disabled=checks["traditional_dca_enabled"],
            averaging_down_disabled=checks["averaging_down_enabled"], simulation_lock_valid=checks["simulation_lock_missing"],
            direct_execution_blocked=checks["direct_execution_requested"], live_execution_blocked=checks["live_execution_requested"],
            no_order_sent_valid=checks["order_status_not_safe"], block_reasons=blocks, evaluation_reason_en=en,
            evaluation_reason_th=th, learning_value_en=learning_en, learning_value_th=learning_th,
            expected_next_action_en=next_en, expected_next_action_th=next_th,
            confidence=round(sum(checks.values()) / len(checks) * 100.0, 2),
            next_review_time_utc=(now + timedelta(seconds=review)).isoformat(), broker=broker, symbol=symbol,
            lot_per_unit=lot, execution_status=execution_status,
        )

    def explain_one(self, record: Mapping[str, Any]) -> PaperOutcomeEvaluationReport:
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
        return PaperOutcomeEvaluationRuntime._optional_utc_time(value) or datetime.now(timezone.utc)

    @staticmethod
    def _optional_utc_time(value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc)
        if isinstance(value, str) and value.strip():
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
            except ValueError:
                return None
        return None
