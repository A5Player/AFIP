"""Deterministic paper-execution foundation for Milestone L Pack 1."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Any, Mapping

@dataclass(frozen=True)
class PaperExecutionFoundationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    paper_execution_readiness: str
    foundation_id: str
    milestone_k_complete: bool
    runtime_certified: bool
    paper_account_connected: bool
    market_data_ready: bool
    historical_data_ready: bool
    risk_limits_configured: bool
    audit_record_ready: bool
    dashboard_explainability_ready: bool
    broker_policy_valid: bool
    symbol_policy_valid: bool
    unit_policy_valid: bool
    simulation_lock_valid: bool
    direct_execution_blocked: bool
    live_execution_blocked: bool
    no_order_sent_valid: bool
    block_reasons: tuple[str, ...]
    readiness_reason_en: str
    readiness_reason_th: str
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

class PaperExecutionFoundationRuntime:
    """Open Milestone L only for controlled paper/demo observation, never live execution."""

    def evaluate_one(self, record: Mapping[str, Any]) -> PaperExecutionFoundationReport:
        now = self._utc_time(record.get("current_time_utc"))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        milestone_k_complete = bool(record.get("milestone_k_complete", str(record.get("milestone_k_status", "COMPLETE")).upper() == "COMPLETE"))
        runtime_certified = str(record.get("runtime_certification_status", "CERTIFIED")).strip().upper() in {"READY", "CERTIFIED", "COMPLETE"}
        checks = {
            "milestone_k_not_complete": milestone_k_complete,
            "runtime_not_certified": runtime_certified,
            "paper_account_not_connected": bool(record.get("paper_account_connected", True)),
            "market_data_not_ready": bool(record.get("market_data_ready", True)),
            "historical_data_not_ready": bool(record.get("historical_data_ready", True)),
            "risk_limits_not_configured": bool(record.get("risk_limits_configured", True)),
            "audit_record_not_ready": bool(record.get("audit_record_ready", True)),
            "dashboard_explainability_not_ready": bool(record.get("dashboard_explainability_ready", True)),
            "xm_only_policy": broker == "XM",
            "gold_only_policy": symbol == "GOLD#",
            "fixed_unit_policy": abs(lot - 0.01) <= 1e-12,
            "simulation_lock_missing": execution_status == "LOCKED_SIMULATION_ONLY",
            "direct_execution_requested": not bool(record.get("direct_execution", False)),
            "live_execution_requested": not bool(record.get("live_execution_enabled", False)),
            "order_status_not_safe": order_status == "NO_ORDER_SENT",
        }
        blocks = tuple(name for name, passed in checks.items() if not passed)
        ready = not blocks
        payload = {"checks": checks, "broker": broker, "symbol": symbol, "lot": lot, "execution": execution_status, "order": order_status}
        foundation_id = "L01-" + sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        if ready:
            status, reason, readiness = "READY", "paper_execution_foundation_ready", "PAPER_OBSERVATION_READY"
            en = "Milestone K certification, paper account, data, risk, audit, explainability, and all simulation safety gates are ready."
            th = "การรับรอง Milestone K, บัญชี Paper, ข้อมูล, ความเสี่ยง, Audit, Explainability และ Simulation Safety Gate พร้อมครบ"
            hold_en = "Keep live and direct execution disabled while paper observations are collected."
            hold_th = "คงการปิด Live Execution และ Direct Execution ระหว่างเก็บผลการสังเกตแบบ Paper"
            next_en = "Begin deterministic paper-session observation without transmitting an order."
            next_th = "เริ่มการสังเกต Paper Session แบบกำหนดแน่นอนโดยไม่ส่งคำสั่งซื้อขาย"
        else:
            status, reason, readiness = "BLOCKED", blocks[0], "NOT_READY"
            en = "Paper execution foundation is blocked because at least one dependency, data, risk, policy, or safety gate failed."
            th = "Paper Execution Foundation ถูกบล็อก เพราะ Dependency, ข้อมูล, ความเสี่ยง, นโยบาย หรือ Safety Gate อย่างน้อยหนึ่งรายการไม่ผ่าน"
            hold_en = "Hold the project state and keep every execution path disabled."
            hold_th = "คงสถานะโครงการและปิดทุกเส้นทางการส่งคำสั่ง"
            next_en = "Correct all block reasons and rerun Milestone L Pack 1 validation."
            next_th = "แก้ไข Block Reason ทั้งหมดแล้วรันการตรวจ Milestone L Pack 1 อีกครั้ง"
        review = max(60, self._integer(record.get("next_review_seconds", 300)) or 300)
        return PaperExecutionFoundationReport(
            status=status, reason=reason, milestone="MILESTONE_L", pack="PACK_1",
            paper_execution_readiness=readiness, foundation_id=foundation_id,
            milestone_k_complete=milestone_k_complete, runtime_certified=runtime_certified,
            paper_account_connected=checks["paper_account_not_connected"], market_data_ready=checks["market_data_not_ready"],
            historical_data_ready=checks["historical_data_not_ready"], risk_limits_configured=checks["risk_limits_not_configured"],
            audit_record_ready=checks["audit_record_not_ready"], dashboard_explainability_ready=checks["dashboard_explainability_not_ready"],
            broker_policy_valid=checks["xm_only_policy"], symbol_policy_valid=checks["gold_only_policy"], unit_policy_valid=checks["fixed_unit_policy"],
            simulation_lock_valid=checks["simulation_lock_missing"], direct_execution_blocked=checks["direct_execution_requested"],
            live_execution_blocked=checks["live_execution_requested"], no_order_sent_valid=checks["order_status_not_safe"], block_reasons=blocks,
            readiness_reason_en=en, readiness_reason_th=th, holding_reason_en=hold_en, holding_reason_th=hold_th,
            expected_next_action_en=next_en, expected_next_action_th=next_th,
            confidence=round(sum(checks.values()) / len(checks) * 100.0, 2), next_review_time_utc=(now + timedelta(seconds=review)).isoformat(),
            broker=broker, symbol=symbol, lot_per_unit=lot, execution_status=execution_status,
        )

    def explain_one(self, record: Mapping[str, Any]) -> PaperExecutionFoundationReport:
        return self.evaluate_one(record)

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
