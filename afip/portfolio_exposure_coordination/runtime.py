"""Milestone N Pack 5: deterministic, research-only exposure coordination.

This module validates proposed plan exposure after capital allocation. It has no
execution authority and never creates or transmits a broker request.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class PlanExposure:
    trade_plan_id: str
    direction: str
    allocated_units: int
    risk_amount: float
    protected_runner: bool
    independent_position_lifecycle: bool
    coordination_status: str
    coordination_reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExposureCoordinationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    coordination_id: str
    allocation_id: str
    risk_evaluation_id: str
    profile_id: str
    market_regime: str
    total_units: int
    maximum_portfolio_units: int
    total_risk_amount: float
    maximum_portfolio_risk_amount: float
    buy_units: int
    sell_units: int
    protected_runner_units: int
    maximum_protected_runner_units: int
    active_plan_count: int
    same_direction_plan_count: int
    direction_concentration_percent: float
    maximum_direction_concentration_percent: float
    exposures: tuple[PlanExposure, ...]
    allocation_approved: bool
    unit_limit_valid: bool
    risk_limit_valid: bool
    direction_concentration_valid: bool
    protected_runner_limit_valid: bool
    plan_lineage_valid: bool
    independent_position_lifecycles_valid: bool
    market_regime_before_signal: bool
    forbidden_methods_disabled: bool
    data_quality_certified: bool
    portfolio_exposure_approved: bool
    portfolio_exposure_coordination_ready: bool
    research_only: bool
    production_knowledge_approved: bool
    block_reasons: tuple[str, ...]
    explanation_reason_en: str
    explanation_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    broker: str = "XM"
    symbol: str = "GOLD#"
    base_lot_per_unit: float = 0.01
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    direct_execution: bool = False
    live_execution_enabled: bool = False
    order_status: str = "NO_ORDER_SENT"
    broker_request_created: bool = False
    order_transmission_attempted: bool = False
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["exposures"] = [item.as_dict() for item in self.exposures]
        return payload


class PortfolioExposureCoordinationRuntime:
    """Coordinates allocated exposure without changing orders or trade logic."""

    def evaluate(
        self,
        record: Mapping[str, Any],
        allocations: Iterable[Mapping[str, Any]] = (),
    ) -> ExposureCoordinationReport:
        allocation_id = str(record.get("allocation_id", "")).strip()
        risk_evaluation_id = str(record.get("risk_evaluation_id", "")).strip()
        profile_id = str(record.get("profile_id", "")).strip()
        regime = str(record.get("market_regime", "")).strip().upper()
        max_units = self._integer(record.get("maximum_portfolio_units"), 3)
        max_risk = max(0.0, self._number(record.get("maximum_portfolio_risk_amount"), 0.0))
        max_runner_units = self._integer(record.get("maximum_protected_runner_units"), 1)
        max_direction_pct = self._number(record.get("maximum_direction_concentration_percent"), 100.0)
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        base_lot = self._number(record.get("base_lot_per_unit"), 0.01)

        normalized: list[dict[str, Any]] = []
        ids: list[str] = []
        for raw in allocations:
            item = dict(raw)
            plan_id = str(item.get("trade_plan_id", "")).strip()
            direction = str(item.get("direction", "")).strip().upper()
            units = max(0, self._integer(item.get("allocated_units"), 0))
            risk = max(0.0, self._number(item.get("allocated_risk_amount"), 0.0))
            lifecycle = bool(item.get("independent_position_lifecycle", True))
            runner = bool(item.get("protected_runner", False))
            ids.append(plan_id)
            normalized.append({
                "trade_plan_id": plan_id,
                "direction": direction,
                "allocated_units": units,
                "allocated_risk_amount": risk,
                "protected_runner": runner,
                "independent_position_lifecycle": lifecycle,
            })

        total_units = sum(item["allocated_units"] for item in normalized)
        total_risk = sum(item["allocated_risk_amount"] for item in normalized)
        buy_units = sum(item["allocated_units"] for item in normalized if item["direction"] == "BUY")
        sell_units = sum(item["allocated_units"] for item in normalized if item["direction"] == "SELL")
        runner_units = sum(item["allocated_units"] for item in normalized if item["protected_runner"])
        active = [item for item in normalized if item["allocated_units"] > 0]
        dominant_units = max(buy_units, sell_units)
        concentration = dominant_units / total_units * 100.0 if total_units else 0.0
        same_direction_count = max(
            sum(1 for item in active if item["direction"] == "BUY"),
            sum(1 for item in active if item["direction"] == "SELL"),
        )

        allocation_approved = bool(record.get("capital_allocation_approved", False)) and bool(
            record.get("capital_allocation_ready", False)
        )
        lineage_valid = bool(normalized) and all(ids) and len(ids) == len(set(ids))
        directions_valid = all(item["direction"] in {"BUY", "SELL"} for item in normalized)
        lifecycle_valid = all(item["independent_position_lifecycle"] for item in normalized)
        unit_limit_valid = 0 <= total_units <= max_units <= 3
        risk_limit_valid = max_risk > 0.0 and total_risk <= max_risk + 1e-12
        direction_valid = 0.0 <= max_direction_pct <= 100.0 and concentration <= max_direction_pct + 1e-12
        runner_limit_valid = 0 <= runner_units <= max_runner_units <= 3
        regime_first = bool(record.get("market_regime_before_signal", True)) and bool(regime)
        forbidden_disabled = all(bool(record.get(key, True)) for key in (
            "traditional_dca_disabled", "averaging_down_disabled", "martingale_disabled",
            "grid_trading_disabled", "recovery_trading_disabled",
        ))
        data_quality = bool(record.get("data_quality_certified", False))
        future_safe = not bool(record.get("future_leakage_detected", False))

        checks = (
            (not allocation_id, "capital_allocation_lineage_missing"),
            (not risk_evaluation_id, "portfolio_risk_lineage_missing"),
            (not allocation_approved, "capital_allocation_not_approved"),
            (not profile_id, "profile_id_missing"),
            (not lineage_valid, "trade_plan_lineage_invalid"),
            (not directions_valid, "trade_plan_direction_invalid"),
            (not lifecycle_valid, "independent_position_lifecycle_required"),
            (not unit_limit_valid, "portfolio_unit_limit_exceeded"),
            (not risk_limit_valid, "portfolio_risk_limit_exceeded"),
            (not direction_valid, "direction_concentration_limit_exceeded"),
            (not runner_limit_valid, "protected_runner_limit_exceeded"),
            (not regime_first, "market_regime_sequence_invalid"),
            (not forbidden_disabled, "forbidden_trading_method_enabled"),
            (not data_quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (broker != "XM", "broker_policy_violation"),
            (symbol != "GOLD#", "symbol_policy_violation"),
            (abs(base_lot - 0.01) > 1e-12, "base_unit_policy_violation"),
            (str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).upper() != "LOCKED_SIMULATION_ONLY", "execution_lock_invalid"),
            (str(record.get("order_status", "NO_ORDER_SENT")).upper() != "NO_ORDER_SENT", "order_status_invalid"),
            (bool(record.get("direct_execution", False)) or bool(record.get("live_execution_enabled", False)), "execution_enablement_forbidden"),
            (bool(record.get("broker_request_created", False)) or bool(record.get("order_transmission_attempted", False)), "order_transmission_forbidden"),
        )
        block_reasons = tuple(sorted({reason for condition, reason in checks if condition}))
        approved = not block_reasons

        exposures = tuple(PlanExposure(
            trade_plan_id=item["trade_plan_id"],
            direction=item["direction"],
            allocated_units=item["allocated_units"],
            risk_amount=round(item["allocated_risk_amount"], 8),
            protected_runner=item["protected_runner"],
            independent_position_lifecycle=item["independent_position_lifecycle"],
            coordination_status="APPROVED" if approved else "BLOCKED",
            coordination_reason="PORTFOLIO_EXPOSURE_WITHIN_LIMITS" if approved else "PORTFOLIO_EXPOSURE_GATE_FAILED",
        ) for item in sorted(normalized, key=lambda value: value["trade_plan_id"]))

        identity = {
            "allocation_id": allocation_id,
            "risk_evaluation_id": risk_evaluation_id,
            "profile_id": profile_id,
            "regime": regime,
            "limits": [max_units, round(max_risk, 8), max_runner_units, round(max_direction_pct, 8)],
            "allocations": sorted(normalized, key=lambda value: value["trade_plan_id"]),
            "blocked": block_reasons,
        }
        coordination_id = "PEC-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        return ExposureCoordinationReport(
            status="READY" if approved else "BLOCKED",
            reason="Allocated portfolio exposure is coordinated within locked research limits." if approved else "Portfolio exposure coordination is blocked by lineage, concentration, risk, policy or safety controls.",
            milestone="N", pack="5", coordination_id=coordination_id,
            allocation_id=allocation_id, risk_evaluation_id=risk_evaluation_id,
            profile_id=profile_id, market_regime=regime, total_units=total_units,
            maximum_portfolio_units=max_units, total_risk_amount=round(total_risk, 8),
            maximum_portfolio_risk_amount=round(max_risk, 8), buy_units=buy_units,
            sell_units=sell_units, protected_runner_units=runner_units,
            maximum_protected_runner_units=max_runner_units, active_plan_count=len(active),
            same_direction_plan_count=same_direction_count,
            direction_concentration_percent=round(concentration, 8),
            maximum_direction_concentration_percent=round(max_direction_pct, 8),
            exposures=exposures, allocation_approved=allocation_approved,
            unit_limit_valid=unit_limit_valid, risk_limit_valid=risk_limit_valid,
            direction_concentration_valid=direction_valid,
            protected_runner_limit_valid=runner_limit_valid,
            plan_lineage_valid=lineage_valid,
            independent_position_lifecycles_valid=lifecycle_valid,
            market_regime_before_signal=regime_first,
            forbidden_methods_disabled=forbidden_disabled,
            data_quality_certified=data_quality,
            portfolio_exposure_approved=approved,
            portfolio_exposure_coordination_ready=approved,
            research_only=True, production_knowledge_approved=False,
            block_reasons=block_reasons,
            explanation_reason_en="Coordinates allocated BUY, SELL, protected-runner, unit and risk exposure before any execution decision." if approved else "No exposure approval is issued until all portfolio and execution-safety gates pass.",
            explanation_reason_th="ประสาน Exposure ฝั่ง BUY, SELL, Protected Runner, จำนวน Unit และความเสี่ยงที่จัดสรรแล้ว ก่อนการตัดสินใจด้าน Execution" if approved else "ไม่อนุมัติ Exposure จนกว่าเกณฑ์ Portfolio และ Execution Safety จะผ่านครบ",
            expected_next_action_en="Continue to Milestone N Pack 6 under the locked Version 1.0 roadmap." if approved else "Correct blocked exposure evidence and evaluate again.",
            expected_next_action_th="ดำเนินการต่อ Milestone N Pack 6 ตาม Roadmap Version 1.0 ที่ล็อกไว้" if approved else "แก้หลักฐาน Exposure ที่ถูกบล็อกแล้วประเมินใหม่",
            broker=broker, symbol=symbol, base_lot_per_unit=base_lot,
        )

    @staticmethod
    def _number(value: Any, default: float) -> float:
        try:
            number = float(value)
            return number if isfinite(number) else default
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _integer(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
