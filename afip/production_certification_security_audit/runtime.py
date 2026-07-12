"""Milestone R Pack 7: deterministic production security audit.

This audit validates reviewed security-control evidence after a successful
production safety audit. It does not modify credentials, network settings,
dependencies, files, broker connectivity, trading logic, or execution rights.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ProductionSecurityAuditReport:
    audit_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    audit_timestamp: int
    safety_audit_id: str
    control_count: int
    reviewed_control_count: int
    passed_control_count: int
    failed_control_count: int
    accepted_exception_count: int
    critical_failure_count: int
    credential_security_control_count: int
    secret_exposure_control_count: int
    input_validation_control_count: int
    dependency_integrity_control_count: int
    file_configuration_control_count: int
    network_boundary_control_count: int
    audit_logging_control_count: int
    safety_lineage_valid: bool
    control_ids_unique: bool
    chronology_valid: bool
    control_schema_valid: bool
    all_controls_reviewed: bool
    no_unaccepted_failure: bool
    no_critical_failure: bool
    mandatory_domains_covered: bool
    locked_policy_valid: bool
    security_score: float
    security_audit_passed: bool
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
    credential_value_collected: bool = False
    secret_value_exposed: bool = False
    dependency_changed: bool = False
    network_configuration_changed: bool = False
    broker_request_created: bool = False
    order_transmission_attempted: bool = False
    position_modification_attempted: bool = False
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProductionSecurityAuditRuntime:
    """Validate immutable security evidence under Feature Freeze."""

    ALLOWED_DOMAINS = frozenset({
        "CREDENTIAL_SECURITY",
        "SECRET_EXPOSURE",
        "INPUT_VALIDATION",
        "DEPENDENCY_INTEGRITY",
        "FILE_CONFIGURATION",
        "NETWORK_BOUNDARY",
        "AUDIT_LOGGING",
    })
    MANDATORY_DOMAINS = ALLOWED_DOMAINS
    ALLOWED_RESULTS = frozenset({"PASS", "FAIL", "ACCEPTED_EXCEPTION"})
    ALLOWED_SEVERITIES = frozenset({"LOW", "MEDIUM", "HIGH", "CRITICAL"})
    ALLOWED_REVIEW_STATUSES = frozenset({"REVIEWED", "ACCEPTED", "REJECTED"})

    def validate(
        self,
        safety_report: Mapping[str, Any],
        controls: Iterable[Mapping[str, Any]],
        *,
        audit_timestamp: int,
        minimum_security_score: float = 0.95,
    ) -> ProductionSecurityAuditReport:
        rows = tuple(dict(item) for item in controls)
        audit_ts = self._integer(audit_timestamp)
        control_ids = tuple(str(row.get("control_id", "")).strip().upper() for row in rows)
        timestamps = tuple(self._integer(row.get("timestamp", 0)) for row in rows)

        lineage = (
            str(safety_report.get("milestone", "")).strip().upper() == "R"
            and str(safety_report.get("pack", "")).strip() == "6"
            and str(safety_report.get("status", "")).strip().upper() == "PASS"
            and bool(safety_report.get("safety_audit_passed", False))
            and str(safety_report.get("audit_id", "")).strip().upper().startswith("RSAFE-")
        )
        unique = all(item.startswith("SEC-") for item in control_ids) and len(control_ids) == len(set(control_ids))
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
        policy_valid = self._policy_valid(safety_report) and all(self._policy_valid(row) for row in rows)

        denominator = max(len(rows), 1)
        security_score = round((len(passed_rows) + (0.5 * len(exception_rows))) / denominator, 6)
        threshold = self._bounded_score(minimum_security_score)

        checks = (
            (not lineage, "safety_audit_lineage_invalid"),
            (not unique, "duplicate_or_invalid_security_control_id"),
            (not chronology, "security_audit_chronology_invalid"),
            (not schema_valid, "security_control_schema_invalid"),
            (not all_reviewed, "security_control_review_incomplete"),
            (bool(unaccepted_failure), "unaccepted_security_control_failure"),
            (bool(critical_failures), "critical_security_control_failure"),
            (not mandatory_covered, "mandatory_security_domain_missing"),
            (security_score < threshold, "security_score_below_threshold"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        passed = not blocked
        identity = {
            "safety_audit_id": str(safety_report.get("audit_id", "")),
            "control_ids": control_ids,
            "audit_timestamp": audit_ts,
            "security_score": security_score,
            "blocked": blocked,
        }
        audit_id = "RSEC-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if passed:
            reason = "SECURITY_AUDIT_PASSED"
            en = (
                "Reviewed production-security controls passed deterministic validation across credentials, secrets, "
                "input validation, dependency integrity, files, network boundaries, and audit logging. Execution remains locked."
            )
            th = (
                "มาตรการความปลอดภัยระบบที่ผ่านการทบทวน ผ่านการตรวจสอบ deterministic ครบด้านข้อมูลรับรอง ความลับ "
                "การตรวจสอบอินพุต ความสมบูรณ์ของ dependency ไฟล์ ขอบเขตเครือข่าย และบันทึก audit โดย execution ยังคงถูกล็อก"
            )
        else:
            reason = "SECURITY_AUDIT_BLOCKED"
            en = "Security Audit was blocked by lineage, evidence, chronology, review, domain coverage, score, failure, or frozen-policy controls."
            th = "Security Audit ถูกระงับจาก lineage หลักฐาน ลำดับเวลา การทบทวน ความครอบคลุม คะแนน ความล้มเหลว หรือนโยบายล็อก"

        return ProductionSecurityAuditReport(
            audit_id=audit_id,
            status="PASS" if passed else "BLOCKED",
            reason=reason,
            milestone="R",
            pack="7",
            audit_timestamp=audit_ts,
            safety_audit_id=str(safety_report.get("audit_id", "")).strip().upper(),
            control_count=len(rows),
            reviewed_control_count=reviewed_count,
            passed_control_count=len(passed_rows),
            failed_control_count=len(failed_rows),
            accepted_exception_count=len(exception_rows),
            critical_failure_count=len(critical_failures),
            credential_security_control_count=self._domain_count(rows, "CREDENTIAL_SECURITY"),
            secret_exposure_control_count=self._domain_count(rows, "SECRET_EXPOSURE"),
            input_validation_control_count=self._domain_count(rows, "INPUT_VALIDATION"),
            dependency_integrity_control_count=self._domain_count(rows, "DEPENDENCY_INTEGRITY"),
            file_configuration_control_count=self._domain_count(rows, "FILE_CONFIGURATION"),
            network_boundary_control_count=self._domain_count(rows, "NETWORK_BOUNDARY"),
            audit_logging_control_count=self._domain_count(rows, "AUDIT_LOGGING"),
            safety_lineage_valid=lineage,
            control_ids_unique=unique,
            chronology_valid=chronology,
            control_schema_valid=schema_valid,
            all_controls_reviewed=all_reviewed,
            no_unaccepted_failure=not bool(unaccepted_failure),
            no_critical_failure=not bool(critical_failures),
            mandatory_domains_covered=mandatory_covered,
            locked_policy_valid=policy_valid,
            security_score=security_score,
            security_audit_passed=passed,
            next_audit="R_DATA_INTEGRITY_AUDIT" if passed else "R_SECURITY_REVIEW_REQUIRED",
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
        description = str(row.get("description", "")).strip()
        return (
            domain in self.ALLOWED_DOMAINS
            and result in self.ALLOWED_RESULTS
            and severity in self.ALLOWED_SEVERITIES
            and review in self.ALLOWED_REVIEW_STATUSES
            and len(fingerprint) == 64
            and all(char in "0123456789abcdef" for char in fingerprint)
            and bool(description)
        )

    def _reviewed(self, row: Mapping[str, Any]) -> bool:
        return str(row.get("review_status", "")).strip().upper() in {"REVIEWED", "ACCEPTED"}

    def _result(self, row: Mapping[str, Any]) -> str:
        return str(row.get("result", "")).strip().upper()

    def _domain_count(self, rows: tuple[dict[str, Any], ...], domain: str) -> int:
        return sum(1 for row in rows if str(row.get("control_domain", "")).strip().upper() == domain)

    def _policy_valid(self, row: Mapping[str, Any]) -> bool:
        return (
            str(row.get("broker", "XM")).strip().upper() == "XM"
            and str(row.get("symbol", "GOLD#")).strip().upper() == "GOLD#"
            and abs(float(row.get("base_lot_per_unit", 0.01)) - 0.01) < 1e-12
            and str(row.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper() == "LOCKED_SIMULATION_ONLY"
            and not bool(row.get("direct_execution", False))
            and not bool(row.get("live_execution_enabled", False))
            and str(row.get("order_status", "NO_ORDER_SENT")).strip().upper() == "NO_ORDER_SENT"
            and not bool(row.get("credential_value_collected", False))
            and not bool(row.get("secret_value_exposed", False))
            and not bool(row.get("dependency_changed", False))
            and not bool(row.get("network_configuration_changed", False))
            and not bool(row.get("broker_request_created", False))
            and not bool(row.get("order_transmission_attempted", False))
            and not bool(row.get("position_modification_attempted", False))
            and not bool(row.get("trading_logic_changed", False))
        )

    def _bounded_score(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 1.0

    def _integer(self, value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
