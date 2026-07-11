"""Milestone N Pack 9: deterministic portfolio governance validation.

This validation is research-only. It verifies that certified portfolio evidence
remains under the frozen Version 1.0 policy and has no execution authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping


@dataclass(frozen=True)
class PortfolioGovernanceValidationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    governance_id: str
    certification_id: str
    profile_id: str
    policy_version: str
    configuration_hash: str
    audit_reference: str
    resilience_certified: bool
    policy_frozen: bool
    configuration_integrity_valid: bool
    audit_lineage_complete: bool
    authority_separation_valid: bool
    manual_override_absent: bool
    independent_position_lifecycles_valid: bool
    protected_runner_preserved: bool
    forbidden_methods_disabled: bool
    portfolio_governance_approved: bool
    portfolio_governance_ready: bool
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


class PortfolioGovernanceValidationRuntime:
    """Validate frozen policy, audit lineage and separation of authority."""

    FROZEN_POLICY_VERSION = "AFIP_V1.0_FEATURE_FREEZE"

    def evaluate(self, record: Mapping[str, Any]) -> PortfolioGovernanceValidationReport:
        certification_id = str(record.get("certification_id", "")).strip()
        profile_id = str(record.get("profile_id", "")).strip()
        policy_version = str(record.get("policy_version", "")).strip().upper()
        configuration_hash = str(record.get("configuration_hash", "")).strip()
        audit_reference = str(record.get("audit_reference", "")).strip()

        resilience_certified = bool(record.get("portfolio_resilience_certified", False)) and bool(
            record.get("portfolio_resilience_ready", False)
        )
        policy_frozen = policy_version == self.FROZEN_POLICY_VERSION
        config_integrity = bool(configuration_hash) and bool(record.get("configuration_integrity_valid", False))
        audit_complete = bool(audit_reference) and bool(record.get("audit_lineage_complete", False))
        authority_separation = bool(record.get("authority_separation_valid", False))
        manual_override_absent = not bool(record.get("manual_execution_override", False))
        lifecycle_ok = bool(record.get("independent_position_lifecycles_valid", False))
        runner_preserved = bool(record.get("protected_runner_preserved", True))
        forbidden_disabled = all(bool(record.get(key, True)) for key in (
            "traditional_dca_disabled",
            "averaging_down_disabled",
            "martingale_disabled",
            "grid_trading_disabled",
            "recovery_trading_disabled",
        ))

        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        base_lot = self._number(record.get("base_lot_per_unit"), 0.01)

        checks = (
            (not certification_id, "resilience_certification_lineage_missing"),
            (not profile_id, "profile_id_missing"),
            (not resilience_certified, "portfolio_resilience_not_certified"),
            (not policy_frozen, "feature_freeze_policy_invalid"),
            (not config_integrity, "configuration_integrity_invalid"),
            (not audit_complete, "audit_lineage_incomplete"),
            (not authority_separation, "authority_separation_invalid"),
            (not manual_override_absent, "manual_execution_override_forbidden"),
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
        approved = not blocked

        identity = {
            "certification_id": certification_id,
            "profile_id": profile_id,
            "policy_version": policy_version,
            "configuration_hash": configuration_hash,
            "audit_reference": audit_reference,
            "blocked": blocked,
        }
        governance_id = "PGV-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if approved:
            reason = "PORTFOLIO_GOVERNANCE_VALIDATED"
            en = "Portfolio resilience evidence remains governed by the frozen Version 1.0 policy with complete audit lineage and separated execution authority."
            th = "หลักฐานความทนทานของพอร์ตยังอยู่ภายใต้นโยบาย Version 1.0 ที่ล็อกไว้ พร้อม audit lineage ครบถ้วนและแยกอำนาจ Execution ชัดเจน"
            next_en = "Continue to Milestone N completion certification without enabling execution."
            next_th = "ดำเนินการสู่การรับรองปิด Milestone N โดยไม่เปิด Execution"
        else:
            reason = "PORTFOLIO_GOVERNANCE_BLOCKED"
            en = "Portfolio governance validation is blocked because frozen policy, audit, integrity, or authority-separation evidence failed."
            th = "การตรวจสอบธรรมาภิบาลพอร์ตถูกระงับ เนื่องจากหลักฐานด้านนโยบายที่ล็อกไว้ audit, integrity หรือการแยกอำนาจไม่ผ่าน"
            next_en = "Keep execution locked and resolve the recorded governance reasons before completion certification."
            next_th = "คงการล็อก Execution และแก้ไขเหตุผลด้านธรรมาภิบาลที่บันทึกไว้ก่อนการรับรองขั้นปิด"

        return PortfolioGovernanceValidationReport(
            status="READY" if approved else "BLOCKED",
            reason=reason,
            milestone="N",
            pack="9",
            governance_id=governance_id,
            certification_id=certification_id,
            profile_id=profile_id,
            policy_version=policy_version,
            configuration_hash=configuration_hash,
            audit_reference=audit_reference,
            resilience_certified=resilience_certified,
            policy_frozen=policy_frozen,
            configuration_integrity_valid=config_integrity,
            audit_lineage_complete=audit_complete,
            authority_separation_valid=authority_separation,
            manual_override_absent=manual_override_absent,
            independent_position_lifecycles_valid=lifecycle_ok,
            protected_runner_preserved=runner_preserved,
            forbidden_methods_disabled=forbidden_disabled,
            portfolio_governance_approved=approved,
            portfolio_governance_ready=approved,
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
