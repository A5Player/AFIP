"""Milestone N Pack 10: deterministic Portfolio Intelligence completion gate.

This gate certifies that Milestone N Packs 1-9 are complete under research-only
and simulation-only authority. It never creates broker requests, transmits
orders, modifies positions, or changes trading logic.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping, Sequence

_REQUIRED_CAPABILITIES = (
    "portfolio_intelligence_foundation",
    "adaptive_position_sizing",
    "portfolio_risk_engine",
    "capital_allocation",
    "portfolio_exposure_coordination",
    "portfolio_drawdown_protection",
    "portfolio_stress_validation",
    "portfolio_resilience_certification",
    "portfolio_governance_validation",
)


@dataclass(frozen=True)
class PortfolioIntelligenceCompleteReport:
    status: str
    reason: str
    milestone: str
    pack: str
    completion_id: str
    portfolio_version: str
    governance_id: str
    required_capability_count: int
    completed_capability_count: int
    missing_capabilities: tuple[str, ...]
    capability_lineage_valid: bool
    portfolio_governance_approved: bool
    data_quality_certified: bool
    future_safe: bool
    deterministic_runtime_valid: bool
    market_regime_before_signal: bool
    independent_trade_plans_valid: bool
    independent_position_lifecycles_valid: bool
    protected_runner_preserved: bool
    forbidden_methods_disabled: bool
    milestone_n_complete: bool
    ready_for_milestone_o: bool
    production_certified: bool
    research_only: bool
    feature_flags: tuple[tuple[str, bool], ...]
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
        payload = asdict(self)
        payload["feature_flags"] = dict(self.feature_flags)
        return payload


class PortfolioIntelligenceCompleteRuntime:
    """Close Milestone N without granting production or execution authority."""

    def evaluate_one(self, record: Mapping[str, Any]) -> PortfolioIntelligenceCompleteReport:
        portfolio_version = str(record.get("portfolio_version", "N1.10.0-RESEARCH")).strip() or "N1.10.0-RESEARCH"
        governance_id = str(record.get("governance_id", "")).strip()
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        base_lot = self._number(record.get("base_lot_per_unit", 0.01), 0.01)
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()

        raw_capabilities = record.get("capabilities", {})
        capabilities = dict(raw_capabilities) if isinstance(raw_capabilities, Mapping) else {}
        completed = tuple(sorted(name for name in _REQUIRED_CAPABILITIES if bool(capabilities.get(name, False))))
        missing = tuple(sorted(set(_REQUIRED_CAPABILITIES) - set(completed)))

        lineages = self._strings(record.get("capability_lineages", ()))
        lineage_valid = len(lineages) >= len(_REQUIRED_CAPABILITIES) and len(set(lineages)) == len(lineages)
        governance_approved = bool(governance_id) and bool(record.get("portfolio_governance_approved", False)) and bool(
            record.get("portfolio_governance_ready", False)
        )
        data_quality = bool(record.get("data_quality_certified", False))
        future_safe = not bool(record.get("future_leakage_detected", False))
        deterministic = bool(record.get("deterministic_runtime_valid", True))
        regime_first = bool(record.get("market_regime_before_signal", True))
        trade_plans_valid = bool(record.get("independent_trade_plans_valid", False))
        lifecycle_valid = bool(record.get("independent_position_lifecycles_valid", False))
        runner_preserved = bool(record.get("protected_runner_preserved", True))
        forbidden_disabled = all(bool(record.get(key, True)) for key in (
            "traditional_dca_disabled",
            "averaging_down_disabled",
            "martingale_disabled",
            "grid_trading_disabled",
            "recovery_trading_disabled",
        ))

        checks = (
            (bool(missing), "required_capabilities_incomplete"),
            (not lineage_valid, "capability_lineage_invalid"),
            (not governance_approved, "portfolio_governance_not_approved"),
            (not data_quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not deterministic, "deterministic_runtime_invalid"),
            (not regime_first, "market_regime_sequence_invalid"),
            (not trade_plans_valid, "independent_trade_plan_required"),
            (not lifecycle_valid, "independent_position_lifecycle_required"),
            (not runner_preserved, "protected_runner_preservation_required"),
            (not forbidden_disabled, "forbidden_trading_method_enabled"),
            (broker != "XM", "broker_policy_violation"),
            (symbol != "GOLD#", "symbol_policy_violation"),
            (not isfinite(base_lot) or abs(base_lot - 0.01) > 1e-12, "base_unit_policy_violation"),
            (execution_status != "LOCKED_SIMULATION_ONLY", "execution_lock_invalid"),
            (order_status != "NO_ORDER_SENT", "order_status_invalid"),
            (bool(record.get("direct_execution", False)) or bool(record.get("live_execution_enabled", False)), "execution_enablement_forbidden"),
            (bool(record.get("broker_request_created", False)) or bool(record.get("order_transmission_attempted", False)), "order_transmission_forbidden"),
            (bool(record.get("position_modification_attempted", False)), "position_modification_forbidden"),
            (bool(record.get("trading_logic_changed", False)), "trading_logic_change_forbidden"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        complete = not blocked

        flags = tuple(sorted({
            "portfolio_intelligence_complete": complete,
            "learning_intelligence_enabled": False,
            "production_certification_enabled": False,
            "direct_execution_enabled": False,
            "live_execution_enabled": False,
        }.items()))
        identity = {
            "portfolio_version": portfolio_version,
            "governance_id": governance_id,
            "completed": completed,
            "lineages": sorted(lineages),
            "flags": flags,
            "blocked": blocked,
        }
        completion_id = "NCOMP-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if complete:
            reason = "MILESTONE_N_PORTFOLIO_INTELLIGENCE_COMPLETE"
            en = "All Milestone N portfolio capabilities, governance lineage, data integrity, policy controls, and permanent execution locks passed."
            th = "ความสามารถด้านพอร์ตของ Milestone N, Governance Lineage, ความสมบูรณ์ของข้อมูล, นโยบายควบคุม และ Execution Lock ผ่านครบทั้งหมด"
            next_en = "Continue to Milestone O Pack 1 — Learning Intelligence Foundation without enabling execution."
            next_th = "ดำเนินการต่อ Milestone O Pack 1 — Learning Intelligence Foundation โดยไม่เปิด Execution"
        else:
            reason = "MILESTONE_N_PORTFOLIO_INTELLIGENCE_BLOCKED"
            en = "Milestone N completion remains blocked until every portfolio capability, lineage, integrity, policy, and safety gate passes."
            th = "การปิด Milestone N ยังถูกระงับจนกว่าด่านความสามารถ Lineage ความสมบูรณ์ นโยบาย และความปลอดภัยของพอร์ตจะผ่านครบ"
            next_en = "Keep execution locked, correct all recorded block reasons, and evaluate the completion gate again."
            next_th = "คงการล็อก Execution แก้ไข Block Reason ทั้งหมด แล้วประเมินเกณฑ์ปิด Milestone อีกครั้ง"

        return PortfolioIntelligenceCompleteReport(
            status="READY" if complete else "BLOCKED",
            reason=reason,
            milestone="N",
            pack="10",
            completion_id=completion_id,
            portfolio_version=portfolio_version,
            governance_id=governance_id,
            required_capability_count=len(_REQUIRED_CAPABILITIES),
            completed_capability_count=len(completed),
            missing_capabilities=missing,
            capability_lineage_valid=lineage_valid,
            portfolio_governance_approved=governance_approved,
            data_quality_certified=data_quality,
            future_safe=future_safe,
            deterministic_runtime_valid=deterministic,
            market_regime_before_signal=regime_first,
            independent_trade_plans_valid=trade_plans_valid,
            independent_position_lifecycles_valid=lifecycle_valid,
            protected_runner_preserved=runner_preserved,
            forbidden_methods_disabled=forbidden_disabled,
            milestone_n_complete=complete,
            ready_for_milestone_o=complete,
            production_certified=False,
            research_only=True,
            feature_flags=flags,
            block_reasons=blocked,
            explanation_reason_en=en,
            explanation_reason_th=th,
            expected_next_action_en=next_en,
            expected_next_action_th=next_th,
            broker=broker,
            symbol=symbol,
            base_lot_per_unit=round(base_lot, 8),
            execution_status=execution_status,
            order_status=order_status,
        )

    @staticmethod
    def _strings(value: Any) -> tuple[str, ...]:
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return tuple(str(item).strip() for item in value if str(item).strip())
        return ()

    @staticmethod
    def _number(value: Any, default: float) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return default
        return number if isfinite(number) else default
