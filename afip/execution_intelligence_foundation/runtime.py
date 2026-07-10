"""Explainable, deterministic, simulation-only execution intelligence foundation."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class ExecutionIntelligenceReport:
    status: str
    reason: str
    execution_stage: str
    execution_readiness: str
    approval_stage: str
    pipeline_progress_percent: int
    execution_confidence: float
    simulation_ready: bool
    no_order_sent: bool
    block_reasons: tuple[str, ...]
    waiting_reason_en: str
    waiting_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    next_review_time_utc: str
    broker: str = "XM"
    symbol: str = "GOLD#"
    unit_count: int = 0
    lot_per_unit: float = 0.01
    direct_execution: bool = False
    live_execution_enabled: bool = False
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExecutionIntelligenceFoundationRuntime:
    """Convert certified portfolio decisions into a safe simulation context only."""

    def evaluate_one(self, record: Mapping[str, Any]) -> ExecutionIntelligenceReport:
        now = record.get("current_time_utc") or datetime.now(timezone.utc)
        if not isinstance(now, datetime):
            now = datetime.fromisoformat(str(now).replace("Z", "+00:00"))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        certified = str(record.get("decision_certification_status", "CERTIFIED")).strip().upper()
        portfolio_status = str(record.get("portfolio_decision_status", "WAITING")).strip().upper()
        portfolio_decision = str(record.get("portfolio_decision", "WAIT")).strip().upper()
        entry_status = str(record.get("entry_validation_status", "WAITING")).strip().upper()
        conflict_level = str(record.get("conflict_level", "LOW")).strip().upper()
        risk_allowed = bool(record.get("risk_allowed", True))
        timing_allowed = bool(record.get("timing_allowed", True))
        trading_cost_allowed = bool(record.get("trading_cost_allowed", True))
        market_open = bool(record.get("market_open", True))
        calendar_allowed = bool(record.get("calendar_allowed", True))
        units = max(0, int(record.get("approved_units", 0) or 0))
        lot_per_unit = float(record.get("lot_per_unit", 0.01) or 0.01)
        live_requested = bool(record.get("live_execution_enabled", False))
        direct_requested = bool(record.get("direct_execution", False))

        blocks: list[str] = []
        checks = 12
        passed = 0
        for ok, reason in (
            (broker == "XM", "xm_only_policy"),
            (symbol == "GOLD#", "gold_only_policy"),
            (certified == "CERTIFIED", "decision_intelligence_not_certified"),
            (portfolio_status in {"READY", "WAITING", "REVIEW", "PASS"}, "portfolio_decision_not_ready"),
            (conflict_level != "HIGH", "high_unresolved_conflict"),
            (risk_allowed, "risk_not_approved"),
            (timing_allowed, "timing_not_approved"),
            (trading_cost_allowed, "trading_cost_not_approved"),
            (market_open, "market_closed"),
            (calendar_allowed, "calendar_block"),
            (abs(lot_per_unit - 0.01) <= 1e-12, "fixed_unit_policy"),
            (not live_requested and not direct_requested, "live_or_direct_execution_requested"),
        ):
            if ok:
                passed += 1
            else:
                blocks.append(reason)

        actionable = portfolio_decision in {"ENTER", "BUY", "SELL"} and entry_status in {"READY", "PASS", "APPROVED"} and units > 0
        progress = round((passed / checks) * 100)
        confidence = round(min(1.0, max(0.0, float(record.get("decision_confidence", progress / 100.0) or 0.0))), 4)

        if blocks:
            status = "BLOCKED"
            readiness = "BLOCKED_BY_POLICY" if any(x in blocks for x in ("xm_only_policy", "gold_only_policy", "live_or_direct_execution_requested", "fixed_unit_policy")) else "BLOCKED_BY_VALIDATION"
            stage = "EXECUTION_GATE_BLOCKED"
            approval = "NOT_APPROVED"
            simulation_ready = False
            reason = blocks[0]
            wait_en = "Execution simulation is blocked because one or more safety or validation gates failed."
            wait_th = "การจำลองการส่งคำสั่งถูกบล็อก เนื่องจากการตรวจสอบด้านความปลอดภัยหรือเงื่อนไขบางข้อไม่ผ่าน"
            next_en = "Correct the listed block reasons and run the execution gate again."
            next_th = "แก้ไขเหตุผลที่ถูกบล็อก แล้วประเมิน Execution Gate อีกครั้ง"
        elif actionable:
            status = "READY"
            readiness = "READY_FOR_SIMULATION"
            stage = "SIMULATION_CONTEXT_READY"
            approval = "SIMULATION_APPROVED"
            simulation_ready = True
            reason = "execution_context_ready_for_simulation"
            wait_en = "No waiting condition remains for simulation context generation."
            wait_th = "ไม่มีเงื่อนไขที่ต้องรอก่อนสร้างบริบทสำหรับ Simulation"
            next_en = "Create a paper/demo execution instruction; do not send an MT5 live order."
            next_th = "สร้างคำสั่งสำหรับ Paper/Demo เท่านั้น และห้ามส่งคำสั่งจริงไปยัง MT5"
        else:
            status = "WAITING"
            readiness = "WAITING_FOR_VALIDATION"
            stage = "AWAITING_ACTIONABLE_PORTFOLIO_DECISION"
            approval = "PENDING"
            simulation_ready = False
            reason = "portfolio_decision_not_actionable_for_entry"
            wait_en = "The portfolio decision is not yet an approved entry with at least one fixed unit."
            wait_th = "การตัดสินใจระดับพอร์ตยังไม่ใช่จุดเข้าที่อนุมัติพร้อมอย่างน้อย 1 Unit คงที่"
            next_en = "Wait for an approved entry decision, then rerun the simulation readiness gate."
            next_th = "รอการอนุมัติจุดเข้า แล้วประเมิน Simulation Readiness อีกครั้ง"

        return ExecutionIntelligenceReport(
            status=status,
            reason=reason,
            execution_stage=stage,
            execution_readiness=readiness,
            approval_stage=approval,
            pipeline_progress_percent=progress,
            execution_confidence=confidence,
            simulation_ready=simulation_ready,
            no_order_sent=True,
            block_reasons=tuple(blocks),
            waiting_reason_en=wait_en,
            waiting_reason_th=wait_th,
            expected_next_action_en=next_en,
            expected_next_action_th=next_th,
            next_review_time_utc=(now.astimezone(timezone.utc) + timedelta(minutes=5)).isoformat(),
            broker=broker,
            symbol=symbol,
            unit_count=units,
            lot_per_unit=0.01,
        )

    def explain_one(self, record: Mapping[str, Any]) -> ExecutionIntelligenceReport:
        return self.evaluate_one(record)
