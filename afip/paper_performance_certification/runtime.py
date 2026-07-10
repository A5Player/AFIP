"""Deterministic paper performance certification for Milestone L Pack 6."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Any, Mapping


@dataclass(frozen=True)
class PaperPerformanceCertificationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    certification_readiness: str
    certification_id: str
    analytics_status: str
    analytics_id: str
    eligible_outcomes: int
    minimum_sample_required: int
    sample_sufficient: bool
    expectancy_r: float
    minimum_expectancy_r: float
    expectancy_valid: bool
    profit_factor: float
    minimum_profit_factor: float
    profit_factor_valid: bool
    maximum_drawdown: float
    maximum_allowed_drawdown: float
    drawdown_valid: bool
    cost_to_gross_profit_percent: float
    maximum_cost_ratio_percent: float
    cost_ratio_valid: bool
    net_profit: float
    net_profit_valid: bool
    data_integrity_valid: bool
    future_leakage_blocked: bool
    incomplete_data_blocked: bool
    independent_position_lifecycle_valid: bool
    protected_runner_exposure_included: bool
    traditional_dca_disabled: bool
    averaging_down_disabled: bool
    simulation_lock_valid: bool
    direct_execution_blocked: bool
    live_execution_blocked: bool
    no_order_sent_valid: bool
    certified_for_shadow_observation: bool
    certified_for_demo_execution: bool
    block_reasons: tuple[str, ...]
    certification_reason_en: str
    certification_reason_th: str
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


class PaperPerformanceCertificationRuntime:
    """Certify an auditable Pack 5 paper-performance baseline."""

    def evaluate_one(self, record: Mapping[str, Any]) -> PaperPerformanceCertificationReport:
        now = self._utc_time(record.get("current_time_utc"))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        analytics_status = str(record.get("analytics_status", "BLOCKED")).strip().upper()
        analytics_id = str(record.get("analytics_id", "")).strip()
        eligible = max(0, self._integer(record.get("eligible_outcomes", 0)))
        minimum_sample = max(1, self._integer(record.get("minimum_sample_required", 30)) or 30)
        sample_sufficient = bool(record.get("sample_sufficient", eligible >= minimum_sample)) and eligible >= minimum_sample
        expectancy_r = self._number(record.get("expectancy_r", 0.0))
        minimum_expectancy = self._number(record.get("minimum_expectancy_r", 0.05))
        profit_factor = self._number(record.get("profit_factor", 0.0))
        minimum_profit_factor = max(1.0, self._number(record.get("minimum_profit_factor", 1.10)) or 1.10)
        maximum_drawdown = max(0.0, self._number(record.get("maximum_drawdown", 0.0)))
        maximum_allowed_drawdown = max(0.0, self._number(record.get("maximum_allowed_drawdown", 100.0)) or 100.0)
        cost_ratio = max(0.0, self._number(record.get("cost_to_gross_profit_percent", 0.0)))
        maximum_cost_ratio = max(0.0, self._number(record.get("maximum_cost_ratio_percent", 35.0)) or 35.0)
        net_profit = self._number(record.get("net_profit", 0.0))

        expectancy_valid = expectancy_r >= minimum_expectancy
        profit_factor_valid = profit_factor >= minimum_profit_factor
        drawdown_valid = maximum_drawdown <= maximum_allowed_drawdown
        cost_ratio_valid = cost_ratio <= maximum_cost_ratio
        net_profit_valid = net_profit > 0.0
        future_safe = bool(record.get("future_leakage_blocked", True))
        complete_safe = bool(record.get("incomplete_data_blocked", True))
        data_integrity_valid = bool(record.get("data_integrity_valid", True)) and future_safe and complete_safe
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()

        checks = {
            "analytics_not_ready": analytics_status == "READY",
            "analytics_id_missing": bool(analytics_id),
            "sample_insufficient": sample_sufficient,
            "expectancy_below_minimum": expectancy_valid,
            "profit_factor_below_minimum": profit_factor_valid,
            "drawdown_above_limit": drawdown_valid,
            "cost_ratio_above_limit": cost_ratio_valid,
            "net_profit_not_positive": net_profit_valid,
            "data_integrity_invalid": data_integrity_valid,
            "independent_position_lifecycle_invalid": bool(record.get("independent_position_lifecycle_valid", True)),
            "protected_runner_exposure_excluded": bool(record.get("protected_runner_exposure_included", True)),
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
            "analytics_id": analytics_id,
            "eligible": eligible,
            "thresholds": [minimum_sample, minimum_expectancy, minimum_profit_factor, maximum_allowed_drawdown, maximum_cost_ratio],
            "metrics": [expectancy_r, profit_factor, maximum_drawdown, cost_ratio, net_profit],
            "checks": checks,
        }
        certification_id = "L06-" + sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        certified_shadow = not blocks
        certified_demo = False
        if certified_shadow:
            status, reason, readiness = "READY", "paper_performance_certified", "PAPER_PERFORMANCE_CERTIFIED"
            en = "The Pack 5 paper-performance baseline passed sample, expectancy, profit factor, drawdown, cost, data-integrity, and execution-safety gates."
            th = "ค่าฐานผลงาน Paper จาก Pack 5 ผ่านเกณฑ์จำนวนตัวอย่าง Expectancy, Profit Factor, Drawdown, ต้นทุน คุณภาพข้อมูล และความปลอดภัยของ Execution แล้ว"
            next_en = "Proceed to controlled shadow observation; demo execution remains separately gated and disabled."
            next_th = "ดำเนินการต่อไปยัง Shadow Observation แบบควบคุม โดย Demo Execution ยังต้องผ่านการรับรองแยกและยังปิดอยู่"
        else:
            status, reason, readiness = "BLOCKED", blocks[0], "PAPER_PERFORMANCE_CERTIFICATION_BLOCKED"
            en = "Paper performance certification was blocked because one or more statistical, data-quality, policy, or execution-safety gates failed."
            th = "บล็อกการรับรองผลงาน Paper เพราะเกณฑ์ด้านสถิติ คุณภาพข้อมูล นโยบาย หรือความปลอดภัยของ Execution อย่างน้อยหนึ่งรายการไม่ผ่าน"
            next_en = "Correct every block reason, collect more accepted outcomes when required, and re-run Pack 5 analytics before certification."
            next_th = "แก้ไข Block Reason ทั้งหมด เก็บผลลัพธ์ที่ผ่านการรับรองเพิ่มเมื่อจำเป็น และรันการวิเคราะห์ Pack 5 ใหม่ก่อนรับรอง"
        passed = sum(1 for value in checks.values() if value)
        confidence = round(passed / len(checks) * 100.0, 2)
        review = max(30, self._integer(record.get("next_review_seconds", 300)) or 300)
        return PaperPerformanceCertificationReport(
            status=status, reason=reason, milestone="MILESTONE_L", pack="PACK_6",
            certification_readiness=readiness, certification_id=certification_id,
            analytics_status=analytics_status, analytics_id=analytics_id,
            eligible_outcomes=eligible, minimum_sample_required=minimum_sample,
            sample_sufficient=sample_sufficient, expectancy_r=round(expectancy_r, 6),
            minimum_expectancy_r=round(minimum_expectancy, 6), expectancy_valid=expectancy_valid,
            profit_factor=round(profit_factor, 6), minimum_profit_factor=round(minimum_profit_factor, 6),
            profit_factor_valid=profit_factor_valid, maximum_drawdown=round(maximum_drawdown, 6),
            maximum_allowed_drawdown=round(maximum_allowed_drawdown, 6), drawdown_valid=drawdown_valid,
            cost_to_gross_profit_percent=round(cost_ratio, 6), maximum_cost_ratio_percent=round(maximum_cost_ratio, 6),
            cost_ratio_valid=cost_ratio_valid, net_profit=round(net_profit, 6), net_profit_valid=net_profit_valid,
            data_integrity_valid=data_integrity_valid, future_leakage_blocked=future_safe,
            incomplete_data_blocked=complete_safe,
            independent_position_lifecycle_valid=checks["independent_position_lifecycle_invalid"],
            protected_runner_exposure_included=checks["protected_runner_exposure_excluded"],
            traditional_dca_disabled=checks["traditional_dca_enabled"],
            averaging_down_disabled=checks["averaging_down_enabled"],
            simulation_lock_valid=checks["simulation_lock_missing"],
            direct_execution_blocked=checks["direct_execution_requested"],
            live_execution_blocked=checks["live_execution_requested"],
            no_order_sent_valid=checks["order_status_not_safe"],
            certified_for_shadow_observation=certified_shadow,
            certified_for_demo_execution=certified_demo,
            block_reasons=blocks, certification_reason_en=en, certification_reason_th=th,
            expected_next_action_en=next_en, expected_next_action_th=next_th,
            confidence=confidence, next_review_time_utc=(now + timedelta(seconds=review)).isoformat(),
            broker=broker, symbol=symbol, lot_per_unit=lot, execution_status=execution_status,
            order_status=order_status,
        )

    @staticmethod
    def _number(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _integer(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _utc_time(value: Any) -> datetime:
        if isinstance(value, datetime):
            parsed = value
        elif value:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        else:
            parsed = datetime.now(timezone.utc)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
