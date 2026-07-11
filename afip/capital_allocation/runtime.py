"""Milestone N Pack 4: deterministic, research-only capital allocation.

The runtime allocates bounded portfolio capacity among independent trade plans.
It has no execution authority and never creates or transmits a broker request.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class PlanAllocation:
    trade_plan_id: str
    priority_score: float
    requested_units: int
    allocated_units: int
    rejected_units: int
    risk_amount_per_unit: float
    allocated_risk_amount: float
    margin_required_per_unit: float
    allocated_margin_amount: float
    protected_runner: bool
    independent_position_lifecycle: bool
    allocation_reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CapitalAllocationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    allocation_id: str
    risk_evaluation_id: str
    profile_id: str
    market_regime: str
    equity: float
    free_margin: float
    minimum_free_margin_reserve: float
    allocatable_margin_amount: float
    current_open_risk_amount: float
    maximum_portfolio_risk_amount: float
    available_risk_amount: float
    current_units: int
    maximum_portfolio_units: int
    available_units: int
    requested_plan_count: int
    allocated_plan_count: int
    requested_units: int
    allocated_units: int
    rejected_units: int
    allocated_risk_amount: float
    allocated_margin_amount: float
    remaining_risk_amount: float
    remaining_margin_amount: float
    remaining_units: int
    allocations: tuple[PlanAllocation, ...]
    portfolio_risk_engine_approved: bool
    market_regime_before_signal: bool
    independent_trade_plans_valid: bool
    independent_position_lifecycles_valid: bool
    protected_runner_exposure_included: bool
    forbidden_methods_disabled: bool
    data_quality_certified: bool
    capital_allocation_approved: bool
    capital_allocation_ready: bool
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
        payload["allocations"] = [allocation.as_dict() for allocation in self.allocations]
        return payload


class CapitalAllocationRuntime:
    """Allocates risk, unit and margin capacity without execution authority."""

    def evaluate(
        self,
        record: Mapping[str, Any],
        trade_plans: Iterable[Mapping[str, Any]] = (),
    ) -> CapitalAllocationReport:
        risk_evaluation_id = str(record.get("risk_evaluation_id", "")).strip()
        profile_id = str(record.get("profile_id", "")).strip()
        market_regime = str(record.get("market_regime", "")).strip().upper()
        equity = max(0.0, self._number(record.get("equity"), 0.0))
        free_margin = max(0.0, self._number(record.get("free_margin"), 0.0))
        reserve = max(0.0, self._number(record.get("minimum_free_margin_reserve"), 0.0))
        current_risk = max(0.0, self._number(record.get("current_open_risk_amount"), 0.0))
        max_risk_percent = self._number(record.get("maximum_portfolio_risk_percent"), 3.0)
        current_units = max(0, self._integer(record.get("current_units"), 0))
        maximum_units = self._integer(record.get("maximum_portfolio_units"), 3)
        base_lot = self._number(record.get("base_lot_per_unit"), 0.01)
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"

        maximum_risk_amount = equity * max_risk_percent / 100.0 if equity > 0.0 else 0.0
        available_risk = max(0.0, maximum_risk_amount - current_risk)
        allocatable_margin = max(0.0, free_margin - reserve)
        available_units = max(0, maximum_units - current_units)

        normalized: list[dict[str, Any]] = []
        plan_ids: list[str] = []
        lifecycle_valid = True
        for raw in trade_plans:
            plan = dict(raw)
            plan_id = str(plan.get("trade_plan_id", "")).strip()
            requested_units = max(0, self._integer(plan.get("requested_units"), 0))
            priority = self._number(plan.get("priority_score"), 0.0)
            risk_per_unit = max(0.0, self._number(plan.get("risk_amount_per_unit"), 0.0))
            margin_per_unit = max(0.0, self._number(plan.get("margin_required_per_unit"), 0.0))
            independent = bool(plan.get("independent_position_lifecycle", True))
            plan_ids.append(plan_id)
            lifecycle_valid = lifecycle_valid and independent
            normalized.append({
                "trade_plan_id": plan_id,
                "priority_score": priority,
                "requested_units": requested_units,
                "risk_amount_per_unit": risk_per_unit,
                "margin_required_per_unit": margin_per_unit,
                "protected_runner": bool(plan.get("protected_runner", False)),
                "independent_position_lifecycle": independent,
            })

        lineage_valid = bool(normalized) and all(plan_ids) and len(plan_ids) == len(set(plan_ids))
        plan_values_valid = all(
            0.0 <= plan["priority_score"] <= 100.0
            and plan["requested_units"] >= 0
            and plan["risk_amount_per_unit"] > 0.0
            and plan["margin_required_per_unit"] > 0.0
            for plan in normalized
        )
        risk_engine_approved = bool(record.get("portfolio_risk_approved", False)) and bool(
            record.get("portfolio_risk_engine_ready", False)
        )
        regime_first = bool(record.get("market_regime_before_signal", True)) and bool(market_regime)
        runner_included = bool(record.get("protected_runner_exposure_included", True))
        forbidden_disabled = all(bool(record.get(key, True)) for key in (
            "traditional_dca_disabled", "averaging_down_disabled", "martingale_disabled",
            "grid_trading_disabled", "recovery_trading_disabled",
        ))
        data_quality = bool(record.get("data_quality_certified", False))
        future_safe = not bool(record.get("future_leakage_detected", False))

        blocked_checks = (
            (not risk_evaluation_id, "portfolio_risk_lineage_missing"),
            (not risk_engine_approved, "portfolio_risk_engine_not_approved"),
            (not profile_id, "profile_id_missing"),
            (equity <= 0.0, "equity_invalid"),
            (not 0.0 < max_risk_percent <= 10.0, "portfolio_risk_limit_invalid"),
            (reserve > free_margin, "free_margin_reserve_exceeds_free_margin"),
            (not 0 <= current_units <= maximum_units <= 3, "portfolio_unit_limit_invalid"),
            (abs(base_lot - 0.01) > 1e-12, "base_unit_policy_violation"),
            (not lineage_valid, "trade_plan_lineage_invalid"),
            (not plan_values_valid, "trade_plan_allocation_values_invalid"),
            (not lifecycle_valid, "independent_position_lifecycle_required"),
            (not regime_first, "market_regime_sequence_invalid"),
            (not runner_included, "protected_runner_exposure_missing"),
            (not forbidden_disabled, "forbidden_trading_method_enabled"),
            (not data_quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (broker != "XM", "broker_policy_violation"),
            (symbol != "GOLD#", "symbol_policy_violation"),
            (str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).upper() != "LOCKED_SIMULATION_ONLY", "execution_lock_invalid"),
            (str(record.get("order_status", "NO_ORDER_SENT")).upper() != "NO_ORDER_SENT", "order_status_invalid"),
            (bool(record.get("direct_execution", False)) or bool(record.get("live_execution_enabled", False)), "execution_enablement_forbidden"),
            (bool(record.get("broker_request_created", False)) or bool(record.get("order_transmission_attempted", False)), "order_transmission_forbidden"),
        )
        block_reasons = [reason for condition, reason in blocked_checks if condition]

        allocations: list[PlanAllocation] = []
        remaining_risk = available_risk
        remaining_margin = allocatable_margin
        remaining_units = available_units
        allocation_allowed = not block_reasons
        for plan in sorted(normalized, key=lambda item: (-item["priority_score"], item["trade_plan_id"])):
            allocated = 0
            if allocation_allowed:
                for _ in range(plan["requested_units"]):
                    if remaining_units <= 0:
                        break
                    if remaining_risk + 1e-12 < plan["risk_amount_per_unit"]:
                        break
                    if remaining_margin + 1e-12 < plan["margin_required_per_unit"]:
                        break
                    allocated += 1
                    remaining_units -= 1
                    remaining_risk -= plan["risk_amount_per_unit"]
                    remaining_margin -= plan["margin_required_per_unit"]
            rejected = plan["requested_units"] - allocated
            if allocated == plan["requested_units"]:
                allocation_reason = "FULLY_ALLOCATED"
            elif allocated > 0:
                allocation_reason = "PARTIALLY_ALLOCATED_BY_PORTFOLIO_CAPACITY"
            elif not allocation_allowed:
                allocation_reason = "BLOCKED_BY_ALLOCATION_POLICY"
            else:
                allocation_reason = "NO_AVAILABLE_PORTFOLIO_CAPACITY"
            allocations.append(PlanAllocation(
                trade_plan_id=plan["trade_plan_id"], priority_score=round(plan["priority_score"], 8),
                requested_units=plan["requested_units"], allocated_units=allocated, rejected_units=rejected,
                risk_amount_per_unit=round(plan["risk_amount_per_unit"], 8),
                allocated_risk_amount=round(allocated * plan["risk_amount_per_unit"], 8),
                margin_required_per_unit=round(plan["margin_required_per_unit"], 8),
                allocated_margin_amount=round(allocated * plan["margin_required_per_unit"], 8),
                protected_runner=plan["protected_runner"], independent_position_lifecycle=plan["independent_position_lifecycle"],
                allocation_reason=allocation_reason,
            ))

        requested_units = sum(item.requested_units for item in allocations)
        allocated_units = sum(item.allocated_units for item in allocations)
        rejected_units = requested_units - allocated_units
        allocated_risk = sum(item.allocated_risk_amount for item in allocations)
        allocated_margin = sum(item.allocated_margin_amount for item in allocations)
        allocated_plan_count = sum(1 for item in allocations if item.allocated_units > 0)
        if allocation_allowed and requested_units > 0 and allocated_units == 0:
            block_reasons.append("no_allocatable_portfolio_capacity")
        approved = not block_reasons

        identity = {
            "risk_evaluation_id": risk_evaluation_id,
            "profile_id": profile_id,
            "market_regime": market_regime,
            "equity": round(equity, 8),
            "free_margin": round(free_margin, 8),
            "reserve": round(reserve, 8),
            "current_risk": round(current_risk, 8),
            "max_risk_percent": round(max_risk_percent, 8),
            "current_units": current_units,
            "maximum_units": maximum_units,
            "plans": sorted(normalized, key=lambda item: item["trade_plan_id"]),
            "allocations": [item.as_dict() for item in sorted(allocations, key=lambda item: item.trade_plan_id)],
            "blocked": sorted(set(block_reasons)),
        }
        allocation_id = "CAL-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        return CapitalAllocationReport(
            status="READY" if approved else "BLOCKED",
            reason="Capital allocation is approved under research-only authority." if approved else "Capital allocation is blocked by lineage, portfolio capacity, policy or safety controls.",
            milestone="N", pack="4", allocation_id=allocation_id,
            risk_evaluation_id=risk_evaluation_id, profile_id=profile_id, market_regime=market_regime,
            equity=round(equity, 8), free_margin=round(free_margin, 8),
            minimum_free_margin_reserve=round(reserve, 8), allocatable_margin_amount=round(allocatable_margin, 8),
            current_open_risk_amount=round(current_risk, 8), maximum_portfolio_risk_amount=round(maximum_risk_amount, 8),
            available_risk_amount=round(available_risk, 8), current_units=current_units,
            maximum_portfolio_units=maximum_units, available_units=available_units,
            requested_plan_count=len(allocations), allocated_plan_count=allocated_plan_count,
            requested_units=requested_units, allocated_units=allocated_units, rejected_units=rejected_units,
            allocated_risk_amount=round(allocated_risk, 8), allocated_margin_amount=round(allocated_margin, 8),
            remaining_risk_amount=round(max(0.0, remaining_risk), 8), remaining_margin_amount=round(max(0.0, remaining_margin), 8),
            remaining_units=max(0, remaining_units), allocations=tuple(allocations),
            portfolio_risk_engine_approved=risk_engine_approved, market_regime_before_signal=regime_first,
            independent_trade_plans_valid=lineage_valid, independent_position_lifecycles_valid=lifecycle_valid,
            protected_runner_exposure_included=runner_included, forbidden_methods_disabled=forbidden_disabled,
            data_quality_certified=data_quality, capital_allocation_approved=approved,
            capital_allocation_ready=approved, research_only=True, production_knowledge_approved=False,
            block_reasons=tuple(sorted(set(block_reasons))),
            explanation_reason_en="Distributes only the remaining risk, unit and margin capacity among independent trade plans in deterministic priority order." if approved else "No capital-allocation approval is issued until every portfolio, lineage and safety gate passes.",
            explanation_reason_th="จัดสรรเฉพาะความสามารถด้าน Risk, Unit และ Margin ที่เหลือให้แผนการเทรดอิสระตามลำดับความสำคัญแบบ Deterministic" if approved else "ไม่อนุมัติการจัดสรรทุนจนกว่าเกณฑ์ Portfolio, Lineage และ Safety จะผ่านครบ",
            expected_next_action_en="Continue to Milestone N Pack 5 under the locked Version 1.0 roadmap." if approved else "Correct blocked capital-allocation evidence and evaluate again.",
            expected_next_action_th="ดำเนินการต่อ Milestone N Pack 5 ตาม Roadmap Version 1.0 ที่ล็อกไว้" if approved else "แก้หลักฐาน Capital Allocation ที่ถูกบล็อกแล้วประเมินใหม่",
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
