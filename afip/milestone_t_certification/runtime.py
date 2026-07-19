"""Milestone T Pack 15: production certification and milestone closure.

This module certifies evidence produced by Milestone T Packs 11 through 14.
It is execution-neutral and permanently denies order execution authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from afip.historical_replay_research import AppendOnlyResearchDataset


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _checksum(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MilestoneTEvidenceSnapshot:
    evidence_id: str
    repository_commit: str
    financial_naming_passed: bool
    focused_tests_passed: bool
    full_regression_passed: bool
    local_quality_passed: bool
    complete_trade_plan_available: bool
    trade_plan_runtime_available: bool
    position_care_available: bool
    unattended_continuity_available: bool
    dataset_registry_complete: bool
    decision_trace_complete: bool
    bilingual_documentation_complete: bool
    project_database_updated: bool
    handoff_updated: bool
    simulation_lock_confirmed: bool
    execution_permission_locked_false: bool
    mt5_order_send_not_added: bool
    mt5_order_modify_not_added: bool
    mt5_order_close_not_added: bool
    observed_at: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence_checksum"] = _checksum(payload)
        return payload


@dataclass(frozen=True)
class MilestoneTClosureCertification:
    certification_id: str
    evidence_id: str
    repository_commit: str
    certification_status: str
    milestone_status: str
    reason_codes: tuple[str, ...]
    production_foundation_certified: bool
    unattended_safety_foundation_certified: bool
    capital_stewardship_certified: bool
    decision_trace_certified: bool
    regression_closure_certified: bool
    execution_permission: bool
    certified_at: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["certification_checksum"] = _checksum(payload)
        return payload


class MilestoneTProductionCertifier:
    """Close Milestone T only when every required item has evidence."""

    EXECUTION_PERMISSION = False

    REQUIRED_EVIDENCE = (
        ("financial_naming_passed", "financial_naming_not_passed"),
        ("focused_tests_passed", "focused_tests_not_passed"),
        ("full_regression_passed", "full_regression_not_passed"),
        ("local_quality_passed", "local_quality_not_passed"),
        ("complete_trade_plan_available", "complete_trade_plan_unavailable"),
        ("trade_plan_runtime_available", "trade_plan_runtime_unavailable"),
        ("position_care_available", "position_care_unavailable"),
        ("unattended_continuity_available", "unattended_continuity_unavailable"),
        ("dataset_registry_complete", "dataset_registry_incomplete"),
        ("decision_trace_complete", "decision_trace_incomplete"),
        ("bilingual_documentation_complete", "bilingual_documentation_incomplete"),
        ("project_database_updated", "project_database_not_updated"),
        ("handoff_updated", "handoff_not_updated"),
        ("simulation_lock_confirmed", "simulation_lock_not_confirmed"),
        ("execution_permission_locked_false", "execution_permission_not_locked"),
        ("mt5_order_send_not_added", "mt5_order_send_authority_detected"),
        ("mt5_order_modify_not_added", "mt5_order_modify_authority_detected"),
        ("mt5_order_close_not_added", "mt5_order_close_authority_detected"),
    )

    def __init__(self, dataset_root: str | Path | None = None) -> None:
        self.dataset = AppendOnlyResearchDataset(dataset_root) if dataset_root is not None else None

    def certify(self, evidence: MilestoneTEvidenceSnapshot) -> MilestoneTClosureCertification:
        reasons = tuple(reason for field, reason in self.REQUIRED_EVIDENCE if not getattr(evidence, field))
        passed = not reasons
        identity = {
            "evidence_id": evidence.evidence_id,
            "repository_commit": evidence.repository_commit,
            "reasons": reasons,
        }
        result = MilestoneTClosureCertification(
            certification_id=f"MTC-{_checksum(identity)[:16].upper()}",
            evidence_id=evidence.evidence_id,
            repository_commit=evidence.repository_commit,
            certification_status="PASS" if passed else "BLOCK",
            milestone_status="MILESTONE_T_CERTIFIED" if passed else "MILESTONE_T_NOT_CERTIFIED",
            reason_codes=("milestone_t_evidence_complete",) if passed else reasons,
            production_foundation_certified=passed,
            unattended_safety_foundation_certified=passed,
            capital_stewardship_certified=passed,
            decision_trace_certified=passed,
            regression_closure_certified=passed,
            execution_permission=self.EXECUTION_PERMISSION,
            certified_at=_utc_now(),
        )
        if self.dataset is not None:
            self.dataset.append("milestone_t_certification_evidence", evidence.as_dict())
            self.dataset.append("milestone_t_closure_certifications", result.as_dict())
        return result


class MilestoneTFinalHandoffBuilder:
    """Build a deterministic handoff record for the next milestone."""

    def build(self, certification: MilestoneTClosureCertification) -> dict[str, Any]:
        record = {
            "milestone": "T",
            "milestone_status": certification.milestone_status,
            "certification_id": certification.certification_id,
            "repository_commit": certification.repository_commit,
            "production_foundation_certified": certification.production_foundation_certified,
            "unattended_safety_foundation_certified": certification.unattended_safety_foundation_certified,
            "capital_stewardship_certified": certification.capital_stewardship_certified,
            "decision_trace_certified": certification.decision_trace_certified,
            "regression_closure_certified": certification.regression_closure_certified,
            "execution_permission": False,
            "next_milestone_entry_allowed": certification.certification_status == "PASS",
            "next_milestone_rule": "PATCH_ONLY_AND_BACKWARD_COMPATIBLE",
            "generated_at": certification.certified_at,
        }
        record["handoff_checksum"] = _checksum(record)
        return record


class MilestoneTClosureContract:
    @staticmethod
    def as_dict() -> dict[str, Any]:
        return {
            "required_packs": (11, 12, 13, 14, 15),
            "full_regression_required": True,
            "financial_naming_required": True,
            "local_quality_required": True,
            "bilingual_documentation_required": True,
            "append_only_evidence_required": True,
            "execution_permission_locked_false": True,
            "mt5_order_authority_added": False,
            "closure_status": "MILESTONE_T_CERTIFIED",
            "source_datasets": (
                "milestone_t_certification_evidence",
                "milestone_t_closure_certifications",
                "milestone_t_final_handoffs",
            ),
        }
