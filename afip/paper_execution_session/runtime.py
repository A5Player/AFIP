"""Deterministic paper execution session monitoring for Milestone L Pack 2."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Any, Mapping


@dataclass(frozen=True)
class PaperExecutionSessionReport:
    status: str
    reason: str
    milestone: str
    pack: str
    session_readiness: str
    observation_id: str
    foundation_ready: bool
    paper_account_connected: bool
    market_session_available: bool
    market_data_fresh: bool
    spread_valid: bool
    latency_valid: bool
    clock_sync_valid: bool
    risk_limits_valid: bool
    audit_record_ready: bool
    independent_trade_plan_required: bool
    traditional_dca_disabled: bool
    averaging_down_disabled: bool
    simulation_lock_valid: bool
    direct_execution_blocked: bool
    live_execution_blocked: bool
    no_order_sent_valid: bool
    spread_points: float
    maximum_spread_points: float
    latency_ms: float
    maximum_latency_ms: float
    data_age_seconds: float
    maximum_data_age_seconds: float
    block_reasons: tuple[str, ...]
    session_reason_en: str
    session_reason_th: str
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


class PaperExecutionSessionRuntime:
    """Certify a paper observation session without creating a broker instruction."""

    def evaluate_one(self, record: Mapping[str, Any]) -> PaperExecutionSessionReport:
        now = self._utc_time(record.get("current_time_utc"))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        foundation_status = str(record.get("paper_execution_foundation_status", record.get("foundation_status", "READY"))).strip().upper()

        spread = max(0.0, self._number(record.get("spread_points", 0.0)))
        maximum_spread = max(0.0, self._number(record.get("maximum_spread_points", 80.0)) or 80.0)
        latency = max(0.0, self._number(record.get("latency_ms", 0.0)))
        maximum_latency = max(1.0, self._number(record.get("maximum_latency_ms", 1000.0)) or 1000.0)
        data_age = max(0.0, self._number(record.get("data_age_seconds", 0.0)))
        maximum_data_age = max(1.0, self._number(record.get("maximum_data_age_seconds", 120.0)) or 120.0)

        checks = {
            "paper_execution_foundation_not_ready": foundation_status in {"READY", "CERTIFIED", "COMPLETE"},
            "paper_account_not_connected": bool(record.get("paper_account_connected", True)),
            "market_session_not_available": bool(record.get("market_session_available", True)),
            "market_data_stale": bool(record.get("market_data_fresh", data_age <= maximum_data_age)) and data_age <= maximum_data_age,
            "spread_above_limit": spread <= maximum_spread,
            "latency_above_limit": latency <= maximum_latency,
            "clock_not_synchronized": bool(record.get("clock_sync_valid", True)),
            "risk_limits_invalid": bool(record.get("risk_limits_valid", True)),
            "audit_record_not_ready": bool(record.get("audit_record_ready", True)),
            "independent_trade_plan_missing": bool(record.get("independent_trade_plan_required", True)),
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
            "checks": checks, "broker": broker, "symbol": symbol, "lot": lot,
            "spread": spread, "max_spread": maximum_spread, "latency": latency,
            "max_latency": maximum_latency, "data_age": data_age, "max_data_age": maximum_data_age,
        }
        observation_id = "L02-" + sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()

        if not blocks:
            status, reason, readiness = "READY", "paper_execution_session_ready", "PAPER_SESSION_READY"
            en = "Paper account, fresh market data, spread, latency, time synchronization, risk, audit, and safety policies are ready for observation."
            th = "บัญชี Paper, ข้อมูลตลาดสดใหม่, Spread, Latency, การซิงก์เวลา, ความเสี่ยง, Audit และนโยบายความปลอดภัยพร้อมสำหรับการสังเกต"
            hold_en = "Observe each independent trade plan and protected runner without combining positions as DCA."
            hold_th = "สังเกตแต่ละ Independent Trade Plan และ Protected Runner แยกกัน โดยไม่รวมสถานะเป็น DCA"
            next_en = "Record the next deterministic paper decision and its market outcome without transmitting an order."
            next_th = "บันทึกการตัดสินใจแบบ Paper ครั้งถัดไปและผลตลาด โดยไม่ส่งคำสั่งซื้อขาย"
        else:
            status, reason, readiness = "BLOCKED", blocks[0], "PAPER_SESSION_BLOCKED"
            en = "Paper observation is blocked because at least one session, data, cost, connectivity, risk, policy, or safety check failed."
            th = "การสังเกตแบบ Paper ถูกบล็อก เพราะการตรวจ Session, ข้อมูล, ต้นทุน, การเชื่อมต่อ, ความเสี่ยง, นโยบาย หรือความปลอดภัยอย่างน้อยหนึ่งรายการไม่ผ่าน"
            hold_en = "Keep the session inactive and preserve all execution locks."
            hold_th = "คง Session เป็น Inactive และรักษาการล็อก Execution ทั้งหมด"
            next_en = "Correct every block reason and rerun Milestone L Pack 2 validation."
            next_th = "แก้ไข Block Reason ทั้งหมดแล้วรันการตรวจ Milestone L Pack 2 อีกครั้ง"

        review = max(30, self._integer(record.get("next_review_seconds", 60)) or 60)
        return PaperExecutionSessionReport(
            status=status, reason=reason, milestone="MILESTONE_L", pack="PACK_2",
            session_readiness=readiness, observation_id=observation_id,
            foundation_ready=checks["paper_execution_foundation_not_ready"],
            paper_account_connected=checks["paper_account_not_connected"],
            market_session_available=checks["market_session_not_available"],
            market_data_fresh=checks["market_data_stale"], spread_valid=checks["spread_above_limit"],
            latency_valid=checks["latency_above_limit"], clock_sync_valid=checks["clock_not_synchronized"],
            risk_limits_valid=checks["risk_limits_invalid"], audit_record_ready=checks["audit_record_not_ready"],
            independent_trade_plan_required=checks["independent_trade_plan_missing"],
            traditional_dca_disabled=checks["traditional_dca_enabled"], averaging_down_disabled=checks["averaging_down_enabled"],
            simulation_lock_valid=checks["simulation_lock_missing"], direct_execution_blocked=checks["direct_execution_requested"],
            live_execution_blocked=checks["live_execution_requested"], no_order_sent_valid=checks["order_status_not_safe"],
            spread_points=spread, maximum_spread_points=maximum_spread, latency_ms=latency,
            maximum_latency_ms=maximum_latency, data_age_seconds=data_age, maximum_data_age_seconds=maximum_data_age,
            block_reasons=blocks, session_reason_en=en, session_reason_th=th,
            holding_reason_en=hold_en, holding_reason_th=hold_th,
            expected_next_action_en=next_en, expected_next_action_th=next_th,
            confidence=round(sum(checks.values()) / len(checks) * 100.0, 2),
            next_review_time_utc=(now + timedelta(seconds=review)).isoformat(), broker=broker, symbol=symbol,
            lot_per_unit=lot, execution_status=execution_status,
        )

    def explain_one(self, record: Mapping[str, Any]) -> PaperExecutionSessionReport:
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
