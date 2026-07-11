"""Milestone N Pack 7: deterministic portfolio stress validation.

Research-only stress gate. It evaluates hypothetical portfolio resilience and
never creates, modifies, closes, or transmits orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping


@dataclass(frozen=True)
class PortfolioStressValidationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    stress_validation_id: str
    protection_id: str
    coordination_id: str
    allocation_id: str
    profile_id: str
    market_regime: str
    current_equity: float
    stressed_equity: float
    equity_floor: float
    allocated_risk_amount: float
    spread_cost_shock_amount: float
    volatility_shock_amount: float
    adverse_movement_amount: float
    liquidity_buffer_amount: float
    total_stress_loss_amount: float
    stressed_drawdown_percent: float
    maximum_stressed_drawdown_percent: float
    equity_floor_valid: bool
    stressed_drawdown_limit_valid: bool
    liquidity_buffer_valid: bool
    drawdown_protection_approved: bool
    exposure_coordination_approved: bool
    capital_allocation_approved: bool
    market_regime_before_signal: bool
    independent_position_lifecycles_valid: bool
    protected_runner_preserved: bool
    forbidden_methods_disabled: bool
    data_quality_certified: bool
    portfolio_stress_validation_approved: bool
    portfolio_stress_validation_ready: bool
    new_allocation_permitted_for_research: bool
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
    position_modification_attempted: bool = False
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class PortfolioStressValidationRuntime:
    """Evaluate deterministic hypothetical portfolio stress limits."""

    def evaluate(self, record: Mapping[str, Any]) -> PortfolioStressValidationReport:
        protection_id = str(record.get("protection_id", "")).strip()
        coordination_id = str(record.get("coordination_id", "")).strip()
        allocation_id = str(record.get("allocation_id", "")).strip()
        profile_id = str(record.get("profile_id", "")).strip()
        regime = str(record.get("market_regime", "")).strip().upper()

        current_equity = max(0.0, self._number(record.get("current_equity"), 0.0))
        equity_floor = max(0.0, self._number(record.get("equity_floor"), 0.0))
        allocated_risk = max(0.0, self._number(record.get("allocated_risk_amount"), 0.0))
        spread_shock = max(0.0, self._number(record.get("spread_cost_shock_amount"), 0.0))
        volatility_shock = max(0.0, self._number(record.get("volatility_shock_amount"), 0.0))
        adverse_movement = max(0.0, self._number(record.get("adverse_movement_amount"), 0.0))
        liquidity_buffer = max(0.0, self._number(record.get("liquidity_buffer_amount"), 0.0))
        max_stressed_dd = self._number(record.get("maximum_stressed_drawdown_percent"), 15.0)

        total_stress_loss = allocated_risk + spread_shock + volatility_shock + adverse_movement
        stressed_equity = max(0.0, current_equity - total_stress_loss)
        stressed_dd = (total_stress_loss / current_equity * 100.0) if current_equity > 0.0 else 0.0

        drawdown_ok = bool(record.get("portfolio_drawdown_protection_approved", False)) and bool(
            record.get("portfolio_drawdown_protection_ready", False)
        )
        coordination_ok = bool(record.get("portfolio_exposure_approved", False)) and bool(
            record.get("portfolio_exposure_coordination_ready", False)
        )
        allocation_ok = bool(record.get("capital_allocation_approved", False)) and bool(
            record.get("capital_allocation_ready", False)
        )
        lifecycle_ok = bool(record.get("independent_position_lifecycles_valid", False))
        runner_preserved = bool(record.get("protected_runner_preserved", True))
        regime_first = bool(record.get("market_regime_before_signal", True)) and bool(regime)
        forbidden_disabled = all(bool(record.get(key, True)) for key in (
            "traditional_dca_disabled",
            "averaging_down_disabled",
            "martingale_disabled",
            "grid_trading_disabled",
            "recovery_trading_disabled",
        ))
        data_quality = bool(record.get("data_quality_certified", False))
        future_safe = not bool(record.get("future_leakage_detected", False))

        equity_floor_valid = stressed_equity >= equity_floor > 0.0
        stressed_dd_valid = 0.0 < max_stressed_dd <= 100.0 and stressed_dd <= max_stressed_dd + 1e-12
        liquidity_buffer_valid = liquidity_buffer >= spread_shock + volatility_shock

        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        base_lot = self._number(record.get("base_lot_per_unit"), 0.01)

        checks = (
            (not protection_id, "drawdown_protection_lineage_missing"),
            (not coordination_id, "exposure_coordination_lineage_missing"),
            (not allocation_id, "capital_allocation_lineage_missing"),
            (not profile_id, "profile_id_missing"),
            (not drawdown_ok, "portfolio_drawdown_protection_not_approved"),
            (not coordination_ok, "portfolio_exposure_not_approved"),
            (not allocation_ok, "capital_allocation_not_approved"),
            (current_equity <= 0.0 or equity_floor <= 0.0, "equity_values_invalid"),
            (total_stress_loss <= 0.0, "stress_loss_inputs_missing"),
            (not equity_floor_valid, "stressed_equity_floor_breached"),
            (not stressed_dd_valid, "maximum_stressed_drawdown_exceeded"),
            (not liquidity_buffer_valid, "liquidity_buffer_insufficient"),
            (not lifecycle_ok, "independent_position_lifecycle_required"),
            (not runner_preserved, "protected_runner_preservation_required"),
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
            (bool(record.get("position_modification_attempted", False)), "position_modification_forbidden"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        approved = not blocked

        identity = {
            "protection_id": protection_id,
            "coordination_id": coordination_id,
            "allocation_id": allocation_id,
            "profile_id": profile_id,
            "regime": regime,
            "equity": [round(current_equity, 8), round(stressed_equity, 8), round(equity_floor, 8)],
            "stress": [round(allocated_risk, 8), round(spread_shock, 8), round(volatility_shock, 8), round(adverse_movement, 8), round(liquidity_buffer, 8)],
            "blocked": blocked,
        }
        stress_id = "PSV-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if approved:
            reason = "PORTFOLIO_STRESS_LIMITS_VALID"
            en = "The portfolio remains within certified equity, drawdown and liquidity limits under the recorded stress assumptions."
            th = "พอร์ตยังอยู่ภายในเพดาน Equity, Drawdown และสภาพคล่องภายใต้สมมติฐานความกดดันที่บันทึกไว้"
            next_en = "Continue research-only portfolio evaluation without enabling execution."
            next_th = "ดำเนินการประเมินพอร์ตในโหมดวิจัยต่อไปโดยไม่เปิดการส่งคำสั่งซื้อขาย"
        else:
            reason = "PORTFOLIO_STRESS_VALIDATION_BLOCKED"
            en = "New research allocation is blocked because one or more portfolio stress limits failed."
            th = "การจัดสรรเพื่อการวิจัยใหม่ถูกระงับ เนื่องจากเงื่อนไข Stress ของพอร์ตอย่างน้อยหนึ่งรายการไม่ผ่าน"
            next_en = "Keep execution locked, block new allocation, and review the recorded stress reasons."
            next_th = "คงการล็อก Execution ระงับการจัดสรรใหม่ และตรวจสอบเหตุผล Stress ที่บันทึกไว้"

        return PortfolioStressValidationReport(
            status="READY" if approved else "BLOCKED",
            reason=reason,
            milestone="N",
            pack="7",
            stress_validation_id=stress_id,
            protection_id=protection_id,
            coordination_id=coordination_id,
            allocation_id=allocation_id,
            profile_id=profile_id,
            market_regime=regime,
            current_equity=round(current_equity, 8),
            stressed_equity=round(stressed_equity, 8),
            equity_floor=round(equity_floor, 8),
            allocated_risk_amount=round(allocated_risk, 8),
            spread_cost_shock_amount=round(spread_shock, 8),
            volatility_shock_amount=round(volatility_shock, 8),
            adverse_movement_amount=round(adverse_movement, 8),
            liquidity_buffer_amount=round(liquidity_buffer, 8),
            total_stress_loss_amount=round(total_stress_loss, 8),
            stressed_drawdown_percent=round(stressed_dd, 8),
            maximum_stressed_drawdown_percent=round(max_stressed_dd, 8),
            equity_floor_valid=equity_floor_valid,
            stressed_drawdown_limit_valid=stressed_dd_valid,
            liquidity_buffer_valid=liquidity_buffer_valid,
            drawdown_protection_approved=drawdown_ok,
            exposure_coordination_approved=coordination_ok,
            capital_allocation_approved=allocation_ok,
            market_regime_before_signal=regime_first,
            independent_position_lifecycles_valid=lifecycle_ok,
            protected_runner_preserved=runner_preserved,
            forbidden_methods_disabled=forbidden_disabled,
            data_quality_certified=data_quality,
            portfolio_stress_validation_approved=approved,
            portfolio_stress_validation_ready=approved,
            new_allocation_permitted_for_research=approved,
            research_only=True,
            production_knowledge_approved=False,
            block_reasons=blocked,
            explanation_reason_en=en,
            explanation_reason_th=th,
            expected_next_action_en=next_en,
            expected_next_action_th=next_th,
            broker="XM",
            symbol="GOLD#",
            base_lot_per_unit=0.01,
            execution_status="LOCKED_SIMULATION_ONLY",
            direct_execution=False,
            live_execution_enabled=False,
            order_status="NO_ORDER_SENT",
            broker_request_created=False,
            order_transmission_attempted=False,
            position_modification_attempted=False,
            trading_logic_changed=False,
        )

    @staticmethod
    def _number(value: Any, default: float) -> float:
        try:
            result = float(value)
        except (TypeError, ValueError):
            return default
        return result if isfinite(result) else default
