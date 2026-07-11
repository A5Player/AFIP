"""Milestone N Pack 8: deterministic portfolio resilience certification.

Research-only certification gate. It consolidates approved lineage from
Milestone N Packs 4-7 and never creates, modifies, closes, or transmits orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping


@dataclass(frozen=True)
class PortfolioResilienceCertificationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    certification_id: str
    stress_validation_id: str
    protection_id: str
    coordination_id: str
    allocation_id: str
    profile_id: str
    market_regime: str
    capital_allocation_approved: bool
    exposure_coordination_approved: bool
    drawdown_protection_approved: bool
    stress_validation_approved: bool
    evidence_complete: bool
    data_quality_certified: bool
    future_safe: bool
    market_regime_before_signal: bool
    independent_position_lifecycles_valid: bool
    protected_runner_preserved: bool
    forbidden_methods_disabled: bool
    portfolio_resilience_certified: bool
    portfolio_resilience_ready: bool
    production_knowledge_approved: bool
    research_only: bool
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


class PortfolioResilienceCertificationRuntime:
    """Consolidate deterministic portfolio resilience evidence."""

    def evaluate(self, record: Mapping[str, Any]) -> PortfolioResilienceCertificationReport:
        allocation_id = str(record.get("allocation_id", "")).strip()
        coordination_id = str(record.get("coordination_id", "")).strip()
        protection_id = str(record.get("protection_id", "")).strip()
        stress_validation_id = str(record.get("stress_validation_id", "")).strip()
        profile_id = str(record.get("profile_id", "")).strip()
        regime = str(record.get("market_regime", "")).strip().upper()

        allocation_ok = bool(record.get("capital_allocation_approved", False)) and bool(
            record.get("capital_allocation_ready", False)
        )
        coordination_ok = bool(record.get("portfolio_exposure_approved", False)) and bool(
            record.get("portfolio_exposure_coordination_ready", False)
        )
        protection_ok = bool(record.get("portfolio_drawdown_protection_approved", False)) and bool(
            record.get("portfolio_drawdown_protection_ready", False)
        )
        stress_ok = bool(record.get("portfolio_stress_validation_approved", False)) and bool(
            record.get("portfolio_stress_validation_ready", False)
        )
        data_quality = bool(record.get("data_quality_certified", False))
        future_safe = not bool(record.get("future_leakage_detected", False))
        regime_first = bool(record.get("market_regime_before_signal", True)) and bool(regime)
        lifecycle_ok = bool(record.get("independent_position_lifecycles_valid", False))
        runner_preserved = bool(record.get("protected_runner_preserved", True))
        forbidden_disabled = all(bool(record.get(key, True)) for key in (
            "traditional_dca_disabled",
            "averaging_down_disabled",
            "martingale_disabled",
            "grid_trading_disabled",
            "recovery_trading_disabled",
        ))
        evidence_complete = all((allocation_id, coordination_id, protection_id, stress_validation_id, profile_id))

        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        base_lot = self._number(record.get("base_lot_per_unit"), 0.01)

        checks = (
            (not allocation_id, "capital_allocation_lineage_missing"),
            (not coordination_id, "exposure_coordination_lineage_missing"),
            (not protection_id, "drawdown_protection_lineage_missing"),
            (not stress_validation_id, "stress_validation_lineage_missing"),
            (not profile_id, "profile_id_missing"),
            (not allocation_ok, "capital_allocation_not_approved"),
            (not coordination_ok, "portfolio_exposure_not_approved"),
            (not protection_ok, "portfolio_drawdown_protection_not_approved"),
            (not stress_ok, "portfolio_stress_validation_not_approved"),
            (not data_quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not regime_first, "market_regime_sequence_invalid"),
            (not lifecycle_ok, "independent_position_lifecycle_required"),
            (not runner_preserved, "protected_runner_preservation_required"),
            (not forbidden_disabled, "forbidden_trading_method_enabled"),
            (broker != "XM", "broker_policy_violation"),
            (symbol != "GOLD#", "symbol_policy_violation"),
            (not isfinite(base_lot) or abs(base_lot - 0.01) > 1e-12, "base_unit_policy_violation"),
            (str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).upper() != "LOCKED_SIMULATION_ONLY", "execution_lock_invalid"),
            (str(record.get("order_status", "NO_ORDER_SENT")).upper() != "NO_ORDER_SENT", "order_status_invalid"),
            (bool(record.get("direct_execution", False)) or bool(record.get("live_execution_enabled", False)), "execution_enablement_forbidden"),
            (bool(record.get("broker_request_created", False)) or bool(record.get("order_transmission_attempted", False)), "order_transmission_forbidden"),
            (bool(record.get("position_modification_attempted", False)), "position_modification_forbidden"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        certified = not blocked and evidence_complete

        identity = {
            "allocation_id": allocation_id,
            "coordination_id": coordination_id,
            "protection_id": protection_id,
            "stress_validation_id": stress_validation_id,
            "profile_id": profile_id,
            "market_regime": regime,
            "blocked": blocked,
        }
        certification_id = "PRC-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if certified:
            reason = "PORTFOLIO_RESILIENCE_CERTIFIED"
            en = "Portfolio allocation, exposure, drawdown and stress evidence are complete and internally consistent for research certification."
            th = "หลักฐานด้านการจัดสรรทุน Exposure, Drawdown และ Stress ของพอร์ตครบถ้วนและสอดคล้องกันสำหรับการรับรองเชิงวิจัย"
            next_en = "Continue to the next locked portfolio-intelligence validation stage without enabling execution."
            next_th = "ดำเนินการสู่ขั้นตรวจสอบ Portfolio Intelligence ถัดไปโดยไม่เปิดการส่งคำสั่งซื้อขาย"
        else:
            reason = "PORTFOLIO_RESILIENCE_CERTIFICATION_BLOCKED"
            en = "Portfolio resilience certification is blocked because required lineage, policy, integrity, or safety evidence failed."
            th = "การรับรองความทนทานของพอร์ตถูกระงับ เนื่องจากหลักฐานด้าน lineage, policy, integrity หรือ safety ไม่ผ่าน"
            next_en = "Keep execution locked and resolve the recorded certification reasons before further portfolio approval."
            next_th = "คงการล็อก Execution และแก้ไขเหตุผลการรับรองที่บันทึกไว้ก่อนอนุมัติพอร์ตขั้นต่อไป"

        return PortfolioResilienceCertificationReport(
            status="READY" if certified else "BLOCKED",
            reason=reason,
            milestone="N",
            pack="8",
            certification_id=certification_id,
            stress_validation_id=stress_validation_id,
            protection_id=protection_id,
            coordination_id=coordination_id,
            allocation_id=allocation_id,
            profile_id=profile_id,
            market_regime=regime,
            capital_allocation_approved=allocation_ok,
            exposure_coordination_approved=coordination_ok,
            drawdown_protection_approved=protection_ok,
            stress_validation_approved=stress_ok,
            evidence_complete=evidence_complete,
            data_quality_certified=data_quality,
            future_safe=future_safe,
            market_regime_before_signal=regime_first,
            independent_position_lifecycles_valid=lifecycle_ok,
            protected_runner_preserved=runner_preserved,
            forbidden_methods_disabled=forbidden_disabled,
            portfolio_resilience_certified=certified,
            portfolio_resilience_ready=certified,
            production_knowledge_approved=certified,
            research_only=True,
            block_reasons=blocked,
            explanation_reason_en=en,
            explanation_reason_th=th,
            expected_next_action_en=next_en,
            expected_next_action_th=next_th,
            broker=broker,
            symbol=symbol,
            base_lot_per_unit=round(base_lot, 8),
        )

    @staticmethod
    def _number(value: Any, default: float) -> float:
        try:
            result = float(value)
        except (TypeError, ValueError):
            return default
        return result if isfinite(result) else default
