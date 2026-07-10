"""Deterministic paper performance analytics for Milestone L Pack 5."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class PaperPerformanceAnalyticsReport:
    status: str
    reason: str
    milestone: str
    pack: str
    analytics_readiness: str
    analytics_id: str
    eligible_outcomes: int
    rejected_outcomes: int
    closed_outcomes: int
    winning_outcomes: int
    losing_outcomes: int
    break_even_outcomes: int
    win_rate_percent: float
    gross_profit: float
    gross_loss: float
    net_profit: float
    profit_factor: float
    average_r_multiple: float
    expectancy_r: float
    maximum_drawdown: float
    trading_cost: float
    swap_cost: float
    cost_to_gross_profit_percent: float
    minimum_sample_required: int
    sample_sufficient: bool
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
    block_reasons: tuple[str, ...]
    performance_reason_en: str
    performance_reason_th: str
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


class PaperPerformanceAnalyticsRuntime:
    """Aggregate accepted paper outcomes without changing trading logic."""

    def evaluate_one(self, record: Mapping[str, Any]) -> PaperPerformanceAnalyticsReport:
        now = self._utc_time(record.get("current_time_utc"))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        outcomes = list(self._outcomes(record.get("outcomes", ())))
        minimum_sample = max(1, self._integer(record.get("minimum_sample_required", 30)) or 30)

        eligible: list[Mapping[str, Any]] = []
        rejected = 0
        future_leakage_blocked = True
        incomplete_data_blocked = True
        for outcome in outcomes:
            future_safe = not bool(outcome.get("future_data_used", False)) and bool(outcome.get("future_leakage_blocked", True))
            complete = bool(outcome.get("data_complete", True))
            accepted = str(outcome.get("status", "READY")).strip().upper() == "READY"
            closed = str(outcome.get("outcome_state", "CLOSED")).strip().upper() == "CLOSED"
            decision_link = bool(outcome.get("decision_link_valid", True))
            if future_safe and complete and accepted and closed and decision_link:
                eligible.append(outcome)
            else:
                rejected += 1
                future_leakage_blocked = future_leakage_blocked and future_safe
                incomplete_data_blocked = incomplete_data_blocked and complete

        net_values = [self._number(item.get("net_profit", 0.0)) for item in eligible]
        r_values = [self._number(item.get("realized_r_multiple", 0.0)) for item in eligible]
        wins = [value for value in net_values if value > 0.0]
        losses = [value for value in net_values if value < 0.0]
        break_even = len(net_values) - len(wins) - len(losses)
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        net_profit = sum(net_values)
        profit_factor = gross_profit / gross_loss if gross_loss > 0.0 else (999.0 if gross_profit > 0.0 else 0.0)
        average_r = sum(r_values) / len(r_values) if r_values else 0.0
        win_rate = (len(wins) / len(eligible) * 100.0) if eligible else 0.0
        average_win_r = sum(value for value in r_values if value > 0.0) / max(1, sum(1 for value in r_values if value > 0.0))
        average_loss_r = abs(sum(value for value in r_values if value < 0.0) / max(1, sum(1 for value in r_values if value < 0.0)))
        win_probability = len(wins) / len(eligible) if eligible else 0.0
        loss_probability = len(losses) / len(eligible) if eligible else 0.0
        expectancy_r = win_probability * average_win_r - loss_probability * average_loss_r
        maximum_drawdown = self._maximum_drawdown(net_values)
        trading_cost = sum(max(0.0, self._number(item.get("trading_cost", 0.0))) for item in eligible)
        swap_cost = sum(max(0.0, self._number(item.get("swap_cost", 0.0))) for item in eligible)
        cost_ratio = ((trading_cost + swap_cost) / gross_profit * 100.0) if gross_profit > 0.0 else 0.0
        sample_sufficient = len(eligible) >= minimum_sample

        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        checks = {
            "paper_outcomes_missing": len(outcomes) > 0,
            "eligible_outcomes_missing": len(eligible) > 0,
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
            "outcomes": [str(item.get("outcome_id", "")) for item in eligible],
            "net": net_values,
            "r": r_values,
            "minimum_sample": minimum_sample,
            "checks": checks,
        }
        analytics_id = "L05-" + sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        if not blocks:
            status, reason, readiness = "READY", "paper_performance_analytics_ready", "PAPER_PERFORMANCE_ANALYTICS_READY"
            en = "Accepted chronological paper outcomes were aggregated into auditable performance, risk, and cost statistics."
            th = "รวมผลลัพธ์ Paper ที่ผ่านการรับรองตามลำดับเวลาเป็นสถิติผลงาน ความเสี่ยง และต้นทุนที่ตรวจสอบย้อนหลังได้แล้ว"
            next_en = "Continue collecting outcomes until the minimum sample is reached, then certify the paper performance baseline."
            next_th = "เก็บผลลัพธ์ต่อจนถึงจำนวนตัวอย่างขั้นต่ำ แล้วรับรองค่าฐานผลงาน Paper"
        else:
            status, reason, readiness = "BLOCKED", blocks[0], "PAPER_PERFORMANCE_ANALYTICS_BLOCKED"
            en = "Performance analytics were blocked because eligible outcomes, policy evidence, or execution-safety evidence is incomplete."
            th = "บล็อกการวิเคราะห์ผลงานเนื่องจากผลลัพธ์ที่มีสิทธิ์ หลักฐานนโยบาย หรือหลักฐานความปลอดภัยของ Execution ไม่ครบ"
            next_en = "Correct every block reason and re-run analytics using only accepted Pack 4 outcomes."
            next_th = "แก้ไข Block Reason ทั้งหมดและวิเคราะห์ใหม่โดยใช้เฉพาะผลลัพธ์จาก Pack 4 ที่ผ่านการรับรอง"
        confidence = round(min(100.0, 55.0 + min(len(eligible), minimum_sample) / minimum_sample * 35.0 + (10.0 if sample_sufficient else 0.0)), 2) if not blocks else 0.0
        review = max(30, self._integer(record.get("next_review_seconds", 300)) or 300)
        return PaperPerformanceAnalyticsReport(
            status=status, reason=reason, milestone="MILESTONE_L", pack="PACK_5", analytics_readiness=readiness,
            analytics_id=analytics_id, eligible_outcomes=len(eligible), rejected_outcomes=rejected, closed_outcomes=len(eligible),
            winning_outcomes=len(wins), losing_outcomes=len(losses), break_even_outcomes=break_even,
            win_rate_percent=round(win_rate, 4), gross_profit=round(gross_profit, 6), gross_loss=round(gross_loss, 6),
            net_profit=round(net_profit, 6), profit_factor=round(profit_factor, 6), average_r_multiple=round(average_r, 6),
            expectancy_r=round(expectancy_r, 6), maximum_drawdown=round(maximum_drawdown, 6), trading_cost=round(trading_cost, 6),
            swap_cost=round(swap_cost, 6), cost_to_gross_profit_percent=round(cost_ratio, 6), minimum_sample_required=minimum_sample,
            sample_sufficient=sample_sufficient, future_leakage_blocked=future_leakage_blocked,
            incomplete_data_blocked=incomplete_data_blocked,
            independent_position_lifecycle_valid=checks["independent_position_lifecycle_invalid"],
            protected_runner_exposure_included=checks["protected_runner_exposure_excluded"],
            traditional_dca_disabled=checks["traditional_dca_enabled"], averaging_down_disabled=checks["averaging_down_enabled"],
            simulation_lock_valid=checks["simulation_lock_missing"], direct_execution_blocked=checks["direct_execution_requested"],
            live_execution_blocked=checks["live_execution_requested"], no_order_sent_valid=checks["order_status_not_safe"],
            block_reasons=blocks, performance_reason_en=en, performance_reason_th=th,
            expected_next_action_en=next_en, expected_next_action_th=next_th, confidence=confidence,
            next_review_time_utc=(now + timedelta(seconds=review)).isoformat(), broker=broker, symbol=symbol,
            lot_per_unit=lot, execution_status=execution_status, order_status=order_status,
        )

    @staticmethod
    def _outcomes(value: Any) -> Iterable[Mapping[str, Any]]:
        if isinstance(value, Mapping):
            return (value,)
        if isinstance(value, (list, tuple)):
            return tuple(item for item in value if isinstance(item, Mapping))
        return ()

    @staticmethod
    def _maximum_drawdown(values: list[float]) -> float:
        equity = 0.0
        peak = 0.0
        maximum = 0.0
        for value in values:
            equity += value
            peak = max(peak, equity)
            maximum = max(maximum, peak - equity)
        return maximum

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
