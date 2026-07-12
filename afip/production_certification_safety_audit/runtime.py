"""Milestone R Pack 6: deterministic production safety audit.

This audit validates reviewed safety-control evidence after repository cleanup.
It does not alter trading logic, position lifecycle, broker connectivity,
execution permissions, Production Certification, or Release Candidate status.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ProductionSafetyAuditReport:
    audit_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    audit_timestamp: int
    repository_cleanup_id: str
    control_count: int
    reviewed_control_count: int
    passed_control_count: int
    failed_control_count: int
    accepted_exception_count: int
    critical_failure_count: int
    risk_boundary_control_count: int
    order_safety_control_count: int
    position_safety_control_count: int
    data_safety_control_count: int
    operational_safety_control_count: int
    fail_safe_control_count: int
    cleanup_lineage_valid: bool
    control_ids_unique: bool
    chronology_valid: bool
    control_schema_valid: bool
    all_controls_reviewed: bool
    no_unaccepted_failure: bool
    no_critical_failure: bool
    mandatory_domains_covered: bool
    locked_policy_valid: bool
    safety_score: float
    safety_audit_passed: bool
    next_audit: str
    review_required: bool
    immutable_record: bool
    production_certification_granted: bool
    release_candidate_granted: bool
    block_reasons: tuple[str, ...]
    control_ids: tuple[str, ...]
    failed_control_ids: tuple[str, ...]
    accepted_exception_ids: tuple[str, ...]
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
    trading_logic_changed: bool = False
    safety_control_bypassed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProductionSafetyAuditRuntime:
    """Validate immutable production-safety evidence under Feature Freeze."""

    ALLOWED_DOMAINS = frozenset({
        "RISK_BOUNDARY", "ORDER_SAFETY", "POSITION_SAFETY",
        "DATA_SAFETY", "OPERATIONAL_SAFETY", "FAIL_SAFE",
    })
    MANDATORY_DOMAINS = ALLOWED_DOMAINS
    ALLOWED_RESULTS = frozenset({"PASS", "FAIL", "ACCEPTED_EXCEPTION"})
    ALLOWED_SEVERITIES = frozenset({"LOW", "MEDIUM", "HIGH", "CRITICAL"})
    ALLOWED_REVIEW_STATUSES = frozenset({"REVIEWED", "ACCEPTED", "REJECTED"})

    def validate(
        self,
        cleanup_report: Mapping[str, Any],
        controls: Iterable[Mapping[str, Any]],
        *,
        audit_timestamp: int,
        minimum_safety_score: float = 0.95,
    ) -> ProductionSafetyAuditReport:
        rows = tuple(dict(item) for item in controls)
        audit_ts = self._integer(audit_timestamp)
        control_ids = tuple(str(row.get("control_id", "")).strip().upper() for row in rows)
        timestamps = tuple(self._integer(row.get("timestamp", 0)) for row in rows)

        lineage = (
            str(cleanup_report.get("milestone", "")).strip().upper() == "R"
            and str(cleanup_report.get("pack", "")).strip() == "5"
            and str(cleanup_report.get("status", "")).strip().upper() == "PASS"
            and bool(cleanup_report.get("repository_cleanup_passed", False))
            and str(cleanup_report.get("cleanup_id", "")).strip().upper().startswith("RCLEAN-")
        )
        unique = all(item.startswith("SAFE-") for item in control_ids) and len(control_ids) == len(set(control_ids))
        chronology = all(ts > 0 and ts <= audit_ts for ts in timestamps)
        schema_valid = all(self._control_schema_valid(row) for row in rows)
        reviewed_count = sum(1 for row in rows if self._reviewed(row))
        all_reviewed = reviewed_count == len(rows)

        passed_rows = tuple(row for row in rows if self._result(row) == "PASS")
        failed_rows = tuple(row for row in rows if self._result(row) == "FAIL")
        exception_rows = tuple(row for row in rows if self._result(row) == "ACCEPTED_EXCEPTION")
        unaccepted_failure = tuple(row for row in failed_rows if not bool(row.get("exception_accepted", False)))
        critical_failures = tuple(
            row for row in failed_rows
            if str(row.get("severity", "")).strip().upper() == "CRITICAL"
        )
        domains = {str(row.get("control_domain", "")).strip().upper() for row in rows}
        mandatory_covered = self.MANDATORY_DOMAINS.issubset(domains)
        policy_valid = self._policy_valid(cleanup_report) and all(self._policy_valid(row) for row in rows)

        denominator = max(len(rows), 1)
        safety_score = round((len(passed_rows) + (0.5 * len(exception_rows))) / denominator, 6)
        threshold = self._bounded_score(minimum_safety_score)

        checks = (
            (not lineage, "repository_cleanup_lineage_invalid"),
            (not unique, "duplicate_or_invalid_safety_control_id"),
            (not chronology, "safety_audit_chronology_invalid"),
            (not schema_valid, "safety_control_schema_invalid"),
            (not all_reviewed, "safety_control_review_incomplete"),
            (bool(unaccepted_failure), "unaccepted_safety_control_failure"),
            (bool(critical_failures), "critical_safety_control_failure"),
            (not mandatory_covered, "mandatory_safety_domain_missing"),
            (safety_score < threshold, "safety_score_below_threshold"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        passed = not blocked
        identity = {
            "cleanup_id": str(cleanup_report.get("cleanup_id", "")),
            "control_ids": control_ids,
            "audit_timestamp": audit_ts,
            "safety_score": safety_score,
            "blocked": blocked,
        }
        audit_id = "RSAFE-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if passed:
            reason = "SAFETY_AUDIT_PASSED"
            en = (
                "Reviewed production-safety controls passed deterministic validation across risk, order, position, "
                "data, operational, and fail-safe domains. Execution permissions remain locked."
            )
            th = (
                "มาตรการความปลอดภัยที่ผ่านการทบทวนผ่านการตรวจสอบ deterministic ครบด้านความเสี่ยง คำสั่งซื้อขาย "
                "สถานะ Position ข้อมูล การปฏิบัติการ และ Fail-safe โดยสิทธิ์ execution ยังคงถูกล็อก"
            )
        else:
            reason = "SAFETY_AUDIT_BLOCKED"
            en = "Safety Audit was blocked by lineage, evidence, chronology, review, domain coverage, score, failure, or frozen-policy controls."
            th = "Safety Audit ถูกระงับจาก lineage หลักฐาน ลำดับเวลา การทบทวน ความครอบคลุม คะแนน ความล้มเหลว หรือนโยบายล็อก"

        return ProductionSafetyAuditReport(
            audit_id=audit_id,
            status="PASS" if passed else "BLOCKED",
            reason=reason,
            milestone="R",
            pack="6",
            audit_timestamp=audit_ts,
            repository_cleanup_id=str(cleanup_report.get("cleanup_id", "")).strip().upper(),
            control_count=len(rows),
            reviewed_control_count=reviewed_count,
            passed_control_count=len(passed_rows),
            failed_control_count=len(failed_rows),
            accepted_exception_count=len(exception_rows),
            critical_failure_count=len(critical_failures),
            risk_boundary_control_count=self._domain_count(rows, "RISK_BOUNDARY"),
            order_safety_control_count=self._domain_count(rows, "ORDER_SAFETY"),
            position_safety_control_count=self._domain_count(rows, "POSITION_SAFETY"),
            data_safety_control_count=self._domain_count(rows, "DATA_SAFETY"),
            operational_safety_control_count=self._domain_count(rows, "OPERATIONAL_SAFETY"),
            fail_safe_control_count=self._domain_count(rows, "FAIL_SAFE"),
            cleanup_lineage_valid=lineage,
            control_ids_unique=unique,
            chronology_valid=chronology,
            control_schema_valid=schema_valid,
            all_controls_reviewed=all_reviewed,
            no_unaccepted_failure=not bool(unaccepted_failure),
            no_critical_failure=not bool(critical_failures),
            mandatory_domains_covered=mandatory_covered,
            locked_policy_valid=policy_valid,
            safety_score=safety_score,
            safety_audit_passed=passed,
            next_audit="R_SECURITY_AUDIT" if passed else "R_SAFETY_REVIEW_REQUIRED",
            review_required=not passed,
            immutable_record=True,
            production_certification_granted=False,
            release_candidate_granted=False,
            block_reasons=blocked,
            control_ids=control_ids,
            failed_control_ids=tuple(str(row.get("control_id", "")).strip().upper() for row in failed_rows),
            accepted_exception_ids=tuple(str(row.get("control_id", "")).strip().upper() for row in exception_rows),
            explanation_reason_en=en,
            explanation_reason_th=th,
        )

    def _control_schema_valid(self, row: Mapping[str, Any]) -> bool:
        domain = str(row.get("control_domain", "")).strip().upper()
        result = self._result(row)
        severity = str(row.get("severity", "")).strip().upper()
        review = str(row.get("review_status", "")).strip().upper()
        fingerprint = str(row.get("fingerprint", "")).strip().lower()
        exception_consistent = result != "ACCEPTED_EXCEPTION" or bool(row.get("exception_accepted", False))
        return (
            domain in self.ALLOWED_DOMAINS
            and result in self.ALLOWED_RESULTS
            and severity in self.ALLOWED_SEVERITIES
            and review in self.ALLOWED_REVIEW_STATUSES
            and len(fingerprint) == 64
            and all(ch in "0123456789abcdef" for ch in fingerprint)
            and bool(str(row.get("control_name", "")).strip())
            and exception_consistent
        )

    @staticmethod
    def _result(row: Mapping[str, Any]) -> str:
        return str(row.get("result", "")).strip().upper()

    def _reviewed(self, row: Mapping[str, Any]) -> bool:
        return str(row.get("review_status", "")).strip().upper() in self.ALLOWED_REVIEW_STATUSES

    @staticmethod
    def _policy_valid(row: Mapping[str, Any]) -> bool:
        return (
            str(row.get("broker", "XM")).strip().upper() == "XM"
            and str(row.get("symbol", "GOLD#")).strip().upper() == "GOLD#"
            and float(row.get("base_lot_per_unit", 0.01)) == 0.01
            and str(row.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper() == "LOCKED_SIMULATION_ONLY"
            and str(row.get("order_status", "NO_ORDER_SENT")).strip().upper() == "NO_ORDER_SENT"
            and not bool(row.get("direct_execution", False))
            and not bool(row.get("live_execution_enabled", False))
            and not bool(row.get("production_certification_granted", False))
            and not bool(row.get("release_candidate_granted", False))
        )

    @staticmethod
    def _domain_count(rows: Iterable[Mapping[str, Any]], domain: str) -> int:
        return sum(1 for row in rows if str(row.get("control_domain", "")).strip().upper() == domain)

    @staticmethod
    def _integer(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _bounded_score(value: Any) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 1.0
        return min(max(number, 0.0), 1.0)
