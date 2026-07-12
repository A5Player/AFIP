"""Milestone R Pack 2: deterministic production duplicate-code audit.

The audit evaluates supplied duplicate-code evidence only. It never edits source,
performs cleanup, grants Production Certification, or enables execution.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ProductionDuplicateCodeAuditReport:
    audit_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    audit_timestamp: int
    regression_audit_id: str
    finding_count: int
    reviewed_finding_count: int
    exact_duplicate_count: int
    structural_duplicate_count: int
    expected_duplicate_count: int
    actionable_duplicate_count: int
    critical_duplicate_count: int
    high_duplicate_count: int
    medium_duplicate_count: int
    low_duplicate_count: int
    duplicated_line_count: int
    duplicate_ratio: float
    maximum_allowed_duplicate_ratio: float
    regression_lineage_valid: bool
    evidence_unique: bool
    chronology_valid: bool
    finding_schema_valid: bool
    all_findings_reviewed: bool
    duplicate_ratio_valid: bool
    no_critical_duplicates: bool
    locked_policy_valid: bool
    duplicate_code_audit_passed: bool
    next_audit: str
    review_required: bool
    cleanup_required: bool
    immutable_record: bool
    production_certification_granted: bool
    release_candidate_granted: bool
    block_reasons: tuple[str, ...]
    finding_ids: tuple[str, ...]
    actionable_finding_ids: tuple[str, ...]
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


class ProductionDuplicateCodeAuditRuntime:
    """Audit duplicate-code findings while preserving the frozen repository policy."""

    ALLOWED_KINDS = frozenset({"EXACT", "STRUCTURAL", "EXPECTED"})
    ALLOWED_SEVERITIES = frozenset({"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"})
    ACCEPTED_REVIEW_STATUSES = frozenset({"REVIEWED", "ACCEPTED", "REMEDIATION_REQUIRED"})

    def audit(
        self,
        regression_report: Mapping[str, Any],
        findings: Iterable[Mapping[str, Any]],
        *,
        audit_timestamp: int,
        scanned_line_count: int,
        maximum_allowed_duplicate_ratio: float = 0.05,
    ) -> ProductionDuplicateCodeAuditReport:
        rows = tuple(dict(item) for item in findings)
        audit_ts = self._integer(audit_timestamp)
        scanned_lines = self._integer(scanned_line_count)
        ratio_limit = self._ratio(maximum_allowed_duplicate_ratio)
        finding_ids = tuple(str(row.get("finding_id", "")).strip().upper() for row in rows)
        finding_timestamps = tuple(self._integer(row.get("timestamp", 0)) for row in rows)

        regression_lineage = (
            str(regression_report.get("milestone", "")).strip().upper() == "R"
            and str(regression_report.get("pack", "")).strip() == "1"
            and str(regression_report.get("status", "")).strip().upper() == "PASS"
            and bool(regression_report.get("regression_audit_passed", False))
            and str(regression_report.get("audit_id", "")).strip().upper().startswith("RAUD-")
        )
        unique = (
            all(item.startswith("DUP-") for item in finding_ids)
            and len(finding_ids) == len(set(finding_ids))
        )
        chronology = all(ts > 0 and ts <= audit_ts for ts in finding_timestamps)
        schema_valid = all(self._finding_schema_valid(row) for row in rows)
        reviewed_count = sum(1 for row in rows if self._reviewed(row))
        all_reviewed = reviewed_count == len(rows)

        exact_count = self._kind_count(rows, "EXACT")
        structural_count = self._kind_count(rows, "STRUCTURAL")
        expected_count = self._kind_count(rows, "EXPECTED")
        actionable = tuple(row for row in rows if self._actionable(row))
        actionable_ids = tuple(str(row.get("finding_id", "")).strip().upper() for row in actionable)
        critical_count = self._severity_count(actionable, "CRITICAL")
        high_count = self._severity_count(actionable, "HIGH")
        medium_count = self._severity_count(actionable, "MEDIUM")
        low_count = self._severity_count(actionable, "LOW")
        duplicated_lines = sum(max(0, self._integer(row.get("duplicated_line_count", 0))) for row in actionable)
        duplicate_ratio = round(duplicated_lines / scanned_lines, 12) if scanned_lines > 0 else 0.0
        ratio_valid = scanned_lines > 0 and 0.0 <= ratio_limit <= 1.0 and duplicate_ratio <= ratio_limit
        no_critical = critical_count == 0
        policy_valid = self._policy_valid(regression_report) and all(self._policy_valid(row) for row in rows)

        checks = (
            (not regression_lineage, "regression_audit_lineage_invalid"),
            (not unique, "duplicate_or_invalid_duplicate_finding_id"),
            (not chronology, "duplicate_audit_chronology_invalid"),
            (not schema_valid, "duplicate_finding_schema_invalid"),
            (not all_reviewed, "duplicate_finding_review_incomplete"),
            (not ratio_valid, "duplicate_ratio_exceeds_limit_or_scan_invalid"),
            (not no_critical, "critical_duplicate_code_detected"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        passed = not blocked
        cleanup_required = bool(actionable)
        identity = {
            "regression_audit_id": str(regression_report.get("audit_id", "")),
            "finding_ids": finding_ids,
            "audit_timestamp": audit_ts,
            "scanned_line_count": scanned_lines,
            "duplicate_ratio": duplicate_ratio,
            "ratio_limit": ratio_limit,
            "blocked": blocked,
        }
        audit_id = "DAUD-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if passed:
            reason = "DUPLICATE_CODE_AUDIT_PASSED"
            en = (
                "Duplicate-code evidence passed deterministic audit. Actionable findings remain recorded "
                "for controlled Milestone R cleanup; no source was changed by this audit."
            )
            th = (
                "หลักฐานโค้ดซ้ำผ่านการตรวจสอบแบบ deterministic โดยรายการที่ต้องดำเนินการยังถูกบันทึกไว้ "
                "สำหรับการ cleanup แบบควบคุมใน Milestone R และ audit นี้ไม่ได้แก้ไข source code"
            )
        else:
            reason = "DUPLICATE_CODE_AUDIT_BLOCKED"
            en = "Duplicate-code audit was blocked by lineage, evidence, chronology, review, ratio, severity, or frozen-policy controls."
            th = "Duplicate Code Audit ถูกระงับจาก lineage หลักฐาน ลำดับเวลา การทบทวน อัตรา ความรุนแรง หรือนโยบายล็อก"

        return ProductionDuplicateCodeAuditReport(
            audit_id=audit_id,
            status="PASS" if passed else "BLOCKED",
            reason=reason,
            milestone="R",
            pack="2",
            audit_timestamp=audit_ts,
            regression_audit_id=str(regression_report.get("audit_id", "")).strip().upper(),
            finding_count=len(rows),
            reviewed_finding_count=reviewed_count,
            exact_duplicate_count=exact_count,
            structural_duplicate_count=structural_count,
            expected_duplicate_count=expected_count,
            actionable_duplicate_count=len(actionable),
            critical_duplicate_count=critical_count,
            high_duplicate_count=high_count,
            medium_duplicate_count=medium_count,
            low_duplicate_count=low_count,
            duplicated_line_count=duplicated_lines,
            duplicate_ratio=duplicate_ratio,
            maximum_allowed_duplicate_ratio=ratio_limit,
            regression_lineage_valid=regression_lineage,
            evidence_unique=unique,
            chronology_valid=chronology,
            finding_schema_valid=schema_valid,
            all_findings_reviewed=all_reviewed,
            duplicate_ratio_valid=ratio_valid,
            no_critical_duplicates=no_critical,
            locked_policy_valid=policy_valid,
            duplicate_code_audit_passed=passed,
            next_audit="R_DEAD_CODE_AUDIT" if passed else "R_DUPLICATE_CODE_REVIEW_REQUIRED",
            review_required=not passed,
            cleanup_required=cleanup_required,
            immutable_record=True,
            production_certification_granted=False,
            release_candidate_granted=False,
            block_reasons=blocked,
            finding_ids=finding_ids,
            actionable_finding_ids=actionable_ids,
            explanation_reason_en=en,
            explanation_reason_th=th,
        )

    def _finding_schema_valid(self, row: Mapping[str, Any]) -> bool:
        kind = str(row.get("duplicate_kind", "")).strip().upper()
        severity = str(row.get("severity", "")).strip().upper()
        fingerprint = str(row.get("fingerprint", "")).strip().lower()
        occurrences = self._integer(row.get("occurrence_count", 0))
        duplicated_lines = self._integer(row.get("duplicated_line_count", 0))
        expected = bool(row.get("expected_duplicate", False))
        return (
            kind in self.ALLOWED_KINDS
            and severity in self.ALLOWED_SEVERITIES
            and len(fingerprint) == 64
            and all(char in "0123456789abcdef" for char in fingerprint)
            and occurrences >= 2
            and duplicated_lines >= 0
            and (kind == "EXPECTED") == expected
        )

    def _reviewed(self, row: Mapping[str, Any]) -> bool:
        return str(row.get("review_status", "")).strip().upper() in self.ACCEPTED_REVIEW_STATUSES

    def _actionable(self, row: Mapping[str, Any]) -> bool:
        return (
            str(row.get("duplicate_kind", "")).strip().upper() != "EXPECTED"
            and not bool(row.get("expected_duplicate", False))
            and str(row.get("review_status", "")).strip().upper() == "REMEDIATION_REQUIRED"
        )

    @staticmethod
    def _kind_count(rows: Iterable[Mapping[str, Any]], kind: str) -> int:
        return sum(1 for row in rows if str(row.get("duplicate_kind", "")).strip().upper() == kind)

    @staticmethod
    def _severity_count(rows: Iterable[Mapping[str, Any]], severity: str) -> int:
        return sum(1 for row in rows if str(row.get("severity", "")).strip().upper() == severity)

    @staticmethod
    def _integer(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _ratio(value: Any) -> float:
        try:
            return round(float(value), 12)
        except (TypeError, ValueError):
            return -1.0

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
