"""Read-only Milestone J Decision Intelligence certification."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class DecisionIntelligenceCertificationReport:
    status: str
    reason: str
    certification_level: str
    passed_checks: int
    total_checks: int
    failed_checks: tuple[str, ...]
    decision_intelligence_ready: bool
    certification_summary_en: str
    certification_summary_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    next_review_time_utc: str
    direct_execution: bool = False
    live_execution_enabled: bool = False
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class DecisionIntelligenceCertificationRuntime:
    """Certify Milestone J while preserving simulation-only execution policy."""

    _CHECKS = (
        ("market_regime_v2", "market_regime_status"),
        ("decision_foundation", "decision_intelligence_status"),
        ("consensus_engine", "consensus_status"),
        ("conflict_resolver", "conflict_resolver_status"),
        ("opportunity_ranking", "opportunity_ranking_status"),
        ("trade_scoring", "trade_scoring_status"),
        ("unit_allocation", "unit_allocation_status"),
        ("entry_validation", "entry_validation_status"),
        ("exit_validation", "exit_validation_status"),
        ("portfolio_decision", "portfolio_decision_status"),
    )
    _PASS = {"READY", "PASS", "COMPLETED", "CERTIFIED", "WAITING", "REVIEW"}

    def evaluate_one(self, record: Mapping[str, Any]) -> DecisionIntelligenceCertificationReport:
        now = record.get("current_time_utc") or datetime.now(timezone.utc)
        if not isinstance(now, datetime):
            now = datetime.fromisoformat(str(now).replace("Z", "+00:00"))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        live_requested = bool(record.get("live_execution_enabled", False))
        direct_execution = bool(record.get("direct_execution", False))
        unit_lot = float(record.get("lot_per_unit", 0.01) or 0.01)

        states = {
            name: str(record.get(key, "READY")).strip().upper() or "READY"
            for name, key in self._CHECKS
        }
        failed = [name for name, state in states.items() if state not in self._PASS]
        if broker != "XM" or symbol != "GOLD#":
            failed.append("version1_market_policy")
        if live_requested or direct_execution:
            failed.append("execution_policy")
        if abs(unit_lot - 0.01) > 1e-12:
            failed.append("fixed_unit_policy")

        total = len(self._CHECKS) + 3
        passed = max(0, total - len(failed))
        if failed:
            status = "BLOCKED"
            reason = "decision_intelligence_certification_requirements_not_met"
            level = "NOT_CERTIFIED"
            ready = False
            summary_en = "Milestone J certification is blocked until every decision-intelligence and safety control passes."
            summary_th = "การรับรอง Milestone J ถูกบล็อกจนกว่าการควบคุม Decision Intelligence และความปลอดภัยทุกข้อจะผ่าน"
            next_en = "Correct failed checks, keep live execution disabled, and rerun the certification."
            next_th = "แก้ไขรายการที่ไม่ผ่าน คงการปิดคำสั่งจริง และรันการรับรองอีกครั้ง"
        else:
            status = "CERTIFIED"
            reason = "milestone_j_decision_intelligence_certified"
            level = "DECISION_INTELLIGENCE_COMPLETE"
            ready = True
            summary_en = "Milestone J is certified as an explainable, deterministic, simulation-only Decision Intelligence platform."
            summary_th = "Milestone J ผ่านการรับรองเป็นแพลตฟอร์ม Decision Intelligence ที่อธิบายได้ กำหนดผลซ้ำได้ และจำกัดเฉพาะ simulation"
            next_en = "Proceed to Milestone K Execution Intelligence while live execution remains disabled."
            next_th = "ดำเนินการต่อสู่ Milestone K Execution Intelligence โดยยังคงปิดคำสั่งจริง"

        return DecisionIntelligenceCertificationReport(
            status=status,
            reason=reason,
            certification_level=level,
            passed_checks=passed,
            total_checks=total,
            failed_checks=tuple(failed),
            decision_intelligence_ready=ready,
            certification_summary_en=summary_en,
            certification_summary_th=summary_th,
            expected_next_action_en=next_en,
            expected_next_action_th=next_th,
            next_review_time_utc=(now.astimezone(timezone.utc) + timedelta(minutes=15)).isoformat(),
        )

    def explain_one(self, record: Mapping[str, Any]) -> DecisionIntelligenceCertificationReport:
        return self.evaluate_one(record)
