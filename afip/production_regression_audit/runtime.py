"""Milestone R Pack 1: deterministic production regression audit.

The audit records regression evidence without granting Production Certification,
Release Candidate status, execution authority, or live trading permission.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ProductionRegressionAuditReport:
    audit_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    audit_timestamp: int
    baseline_test_count: int
    current_test_count: int
    regression_test_delta: int
    targeted_suite_count: int
    passed_targeted_suite_count: int
    failed_targeted_suite_count: int
    required_check_count: int
    passed_required_check_count: int
    failed_required_check_count: int
    milestone_q_complete: bool
    q_completion_lineage_valid: bool
    regression_count_valid: bool
    targeted_suites_valid: bool
    required_checks_valid: bool
    evidence_unique: bool
    chronology_valid: bool
    locked_policy_valid: bool
    regression_audit_passed: bool
    next_audit: str
    review_required: bool
    immutable_record: bool
    production_certification_granted: bool
    release_candidate_granted: bool
    block_reasons: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    explanation_reason_en: str
    explanation_reason_th: str
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

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProductionRegressionAuditRuntime:
    """Audit regression evidence while preserving all production locks."""

    REQUIRED_CHECKS = (
        "FULL_PYTEST",
        "AFIP_LOCAL_QUALITY_CHECK",
        "DASHBOARD_BUILD",
        "FINANCIAL_NAMING_VALIDATION",
        "MT5_DATA_CHECK",
    )

    def audit(
        self,
        completion_report: Mapping[str, Any],
        evidence: Iterable[Mapping[str, Any]],
        *,
        audit_timestamp: int,
        baseline_test_count: int,
        current_test_count: int,
        minimum_targeted_suite_count: int = 10,
    ) -> ProductionRegressionAuditReport:
        rows = tuple(dict(item) for item in evidence)
        evidence_ids = tuple(str(row.get("evidence_id", "")).strip().upper() for row in rows)
        audit_ts = self._integer(audit_timestamp)
        evidence_ts = tuple(self._integer(row.get("timestamp", 0)) for row in rows)

        q_lineage = (
            str(completion_report.get("milestone", "")).strip().upper() == "Q"
            and str(completion_report.get("pack", "")).strip() == "10"
            and str(completion_report.get("status", "")).strip().upper() == "COMPLETE"
            and bool(completion_report.get("milestone_q_complete", False))
            and str(completion_report.get("completion_id", "")).strip().upper().startswith("QCOMP-")
        )
        q_complete = q_lineage
        baseline = self._integer(baseline_test_count)
        current = self._integer(current_test_count)
        count_valid = baseline > 0 and current >= baseline

        unique = bool(rows) and all(item.startswith("REGR-") for item in evidence_ids) and len(evidence_ids) == len(set(evidence_ids))
        chronology = bool(rows) and all(ts > 0 for ts in evidence_ts) and max(evidence_ts) <= audit_ts

        targeted = tuple(row for row in rows if str(row.get("evidence_type", "")).strip().upper() == "TARGETED_TEST")
        passed_targeted = sum(1 for row in targeted if self._passed(row))
        failed_targeted = len(targeted) - passed_targeted
        targeted_valid = len(targeted) >= max(1, self._integer(minimum_targeted_suite_count)) and failed_targeted == 0

        check_rows = {
            str(row.get("check_name", "")).strip().upper(): row
            for row in rows
            if str(row.get("evidence_type", "")).strip().upper() == "REQUIRED_CHECK"
        }
        passed_checks = sum(1 for name in self.REQUIRED_CHECKS if name in check_rows and self._passed(check_rows[name]))
        failed_checks = len(self.REQUIRED_CHECKS) - passed_checks
        checks_valid = failed_checks == 0
        policy_valid = self._policy_valid(completion_report) and all(self._policy_valid(row) for row in rows)

        checks = (
            (not q_lineage, "milestone_q_completion_lineage_invalid"),
            (not count_valid, "regression_test_count_invalid"),
            (not rows, "regression_evidence_missing"),
            (not unique, "duplicate_or_invalid_regression_evidence_id"),
            (not chronology, "regression_audit_chronology_invalid"),
            (not targeted_valid, "targeted_regression_suite_failure_or_insufficiency"),
            (not checks_valid, "required_regression_check_failed_or_missing"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        passed = not blocked
        identity = {
            "q_completion_id": str(completion_report.get("completion_id", "")),
            "evidence_ids": evidence_ids,
            "audit_timestamp": audit_ts,
            "baseline": baseline,
            "current": current,
            "blocked": blocked,
        }
        audit_id = "RAUD-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()

        if passed:
            reason = "REGRESSION_AUDIT_PASSED"
            en = "Regression evidence passed deterministic audit. Production Certification and Release Candidate status remain disabled pending all Milestone R audits."
            th = "หลักฐาน regression ผ่านการตรวจสอบแบบ deterministic โดย Production Certification และสถานะ Release Candidate ยังคงปิดจนกว่าการตรวจทั้งหมดใน Milestone R จะเสร็จสิ้น"
        else:
            reason = "REGRESSION_AUDIT_BLOCKED"
            en = "Regression audit was blocked by lineage, evidence, chronology, validation, or frozen-policy controls."
            th = "Regression Audit ถูกระงับจาก lineage หลักฐาน ลำดับเวลา การตรวจสอบ หรือนโยบายล็อก"

        return ProductionRegressionAuditReport(
            audit_id=audit_id,
            status="PASS" if passed else "BLOCKED",
            reason=reason,
            milestone="R",
            pack="1",
            audit_timestamp=audit_ts,
            baseline_test_count=baseline,
            current_test_count=current,
            regression_test_delta=current - baseline if count_valid else 0,
            targeted_suite_count=len(targeted),
            passed_targeted_suite_count=passed_targeted,
            failed_targeted_suite_count=failed_targeted,
            required_check_count=len(self.REQUIRED_CHECKS),
            passed_required_check_count=passed_checks,
            failed_required_check_count=failed_checks,
            milestone_q_complete=q_complete,
            q_completion_lineage_valid=q_lineage,
            regression_count_valid=count_valid,
            targeted_suites_valid=targeted_valid,
            required_checks_valid=checks_valid,
            evidence_unique=unique,
            chronology_valid=chronology,
            locked_policy_valid=policy_valid,
            regression_audit_passed=passed,
            next_audit="R_DUPLICATE_CODE_AUDIT" if passed else "R_REGRESSION_REVIEW_REQUIRED",
            review_required=not passed,
            immutable_record=True,
            production_certification_granted=False,
            release_candidate_granted=False,
            block_reasons=blocked,
            evidence_ids=evidence_ids,
            explanation_reason_en=en,
            explanation_reason_th=th,
        )

    @staticmethod
    def _passed(row: Mapping[str, Any]) -> bool:
        return str(row.get("status", "")).strip().upper() in {"PASS", "PASSED"} and bool(row.get("passed", False))

    @staticmethod
    def _integer(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _policy_valid(row: Mapping[str, Any]) -> bool:
        try:
            base_lot = float(row.get("base_lot_per_unit", 0.0))
        except (TypeError, ValueError):
            return False
        return (
            str(row.get("broker", "")).strip().upper() == "XM"
            and str(row.get("symbol", "")).strip().upper() == "GOLD#"
            and abs(base_lot - 0.01) < 1e-12
            and str(row.get("execution_status", "")).strip().upper() == "LOCKED_SIMULATION_ONLY"
            and str(row.get("order_status", "")).strip().upper() == "NO_ORDER_SENT"
            and not bool(row.get("direct_execution", True))
            and not bool(row.get("live_execution_enabled", True))
            and not bool(row.get("production_certification_granted", True))
            and not bool(row.get("release_candidate_granted", True))
        )
