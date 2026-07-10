"""Read-only Production Bring-up certification for Pack 10."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ProductionCertificationReport:
    status: str
    reason: str
    broker: str
    symbol: str
    certification_level: str
    passed_checks: int
    total_checks: int
    failed_checks: tuple[str, ...]
    certification_summary_en: str
    certification_summary_th: str
    next_action_en: str
    next_action_th: str
    market_intelligence_ready: bool
    live_execution_enabled: bool = False
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProductionCertificationRuntime:
    """Certify the read-only Production Bring-up surface without enabling trading."""

    _CHECKS = (
        ("vps", "vps_status"),
        ("mt5", "mt5_status"),
        ("internet", "internet_status"),
        ("market_calendar", "market_calendar_status"),
        ("explainable_order_center", "explainable_order_center_status"),
        ("afip_bank", "afip_bank_status"),
        ("historical_data", "historical_data_status"),
        ("dashboard_live", "dashboard_live_runtime_status"),
        ("runtime_supervisor", "runtime_supervisor_status"),
    )
    _PASS = {"READY", "OK", "PASS", "COMPLETED", "HEALTHY", "RUNNING"}

    def evaluate_one(self, record: Mapping[str, Any]) -> ProductionCertificationReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        live_requested = bool(record.get("live_execution_enabled", False))
        states = {
            name: str(record.get(key, "READY")).strip().upper() or "READY"
            for name, key in self._CHECKS
        }
        failed = tuple(name for name, state in states.items() if state not in self._PASS)
        policy_failed = broker != "XM" or symbol != "GOLD#" or live_requested
        if policy_failed:
            failed = ("version1_policy",) + failed

        total = len(states) + 1
        passed = total - len(failed)
        if failed:
            status = "BLOCKED"
            reason = "production_certification_requirements_not_met"
            level = "NOT_CERTIFIED"
            summary_en = "Production Bring-up certification is blocked until every required control passes."
            summary_th = "การรับรอง Production Bring-up ถูกบล็อกจนกว่าการควบคุมที่จำเป็นทุกข้อจะผ่าน"
            next_en = "Keep live execution disabled, correct failed checks, and rerun certification."
            next_th = "คงการปิดคำสั่งจริง แก้ไขรายการที่ไม่ผ่าน และรันการรับรองอีกครั้ง"
            intelligence_ready = False
        else:
            status = "CERTIFIED"
            reason = "production_bringup_certified_for_market_intelligence"
            level = "PRODUCTION_BRINGUP_COMPLETE"
            summary_en = "Production Bring-up is certified for the Market Intelligence Platform milestone."
            summary_th = "Production Bring-up ผ่านการรับรองสำหรับ Milestone แพลตฟอร์ม Market Intelligence"
            next_en = "Proceed to Milestone I while live execution remains disabled."
            next_th = "ดำเนินการต่อสู่ Milestone I โดยยังคงปิดคำสั่งจริง"
            intelligence_ready = True

        return ProductionCertificationReport(
            status=status,
            reason=reason,
            broker=broker,
            symbol=symbol,
            certification_level=level,
            passed_checks=passed,
            total_checks=total,
            failed_checks=failed,
            certification_summary_en=summary_en,
            certification_summary_th=summary_th,
            next_action_en=next_en,
            next_action_th=next_th,
            market_intelligence_ready=intelligence_ready,
        )

    def explain_one(self, record: Mapping[str, Any]) -> ProductionCertificationReport:
        return self.evaluate_one(record)
