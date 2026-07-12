"""Milestone R Pack 3: deterministic production dead-code audit.

The audit evaluates supplied dead-code evidence only. It never removes source,
changes runtime wiring, grants Production Certification, or enables execution.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ProductionDeadCodeAuditReport:
    audit_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    audit_timestamp: int
    duplicate_code_audit_id: str
    finding_count: int
    reviewed_finding_count: int
    unreachable_code_count: int
    unused_symbol_count: int
    unused_module_count: int
    obsolete_path_count: int
    expected_retention_count: int
    actionable_dead_code_count: int
    critical_dead_code_count: int
    high_dead_code_count: int
    medium_dead_code_count: int
    low_dead_code_count: int
    dead_line_count: int
    dead_code_ratio: float
    maximum_allowed_dead_code_ratio: float
    duplicate_audit_lineage_valid: bool
    evidence_unique: bool
    chronology_valid: bool
    finding_schema_valid: bool
    all_findings_reviewed: bool
    dead_code_ratio_valid: bool
    no_critical_dead_code: bool
    locked_policy_valid: bool
    dead_code_audit_passed: bool
    next_audit: str
    review_required: bool
    cleanup_required: bool
    immutable_record: bool
    production_certification_granted: bool
    release_candidate_granted: bool
    block_reasons: tuple[str, ...]
    finding_ids: tuple[str, ...]
    actionable_finding_ids: tuple[str, ...]
    retained_finding_ids: tuple[str, ...]
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
    source_removal_performed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProductionDeadCodeAuditRuntime:
    """Audit dead-code findings while preserving Feature Freeze and execution lock."""

    ALLOWED_KINDS = frozenset({"UNREACHABLE", "UNUSED_SYMBOL", "UNUSED_MODULE", "OBSOLETE_PATH", "RETAINED"})
    ALLOWED_SEVERITIES = frozenset({"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"})
    ACCEPTED_REVIEW_STATUSES = frozenset({"REVIEWED", "ACCEPTED", "REMEDIATION_REQUIRED"})

    def audit(
        self,
        duplicate_report: Mapping[str, Any],
        findings: Iterable[Mapping[str, Any]],
        *,
        audit_timestamp: int,
        scanned_line_count: int,
        maximum_allowed_dead_code_ratio: float = 0.03,
    ) -> ProductionDeadCodeAuditReport:
        rows = tuple(dict(item) for item in findings)
        audit_ts = self._integer(audit_timestamp)
        scanned_lines = self._integer(scanned_line_count)
        ratio_limit = self._ratio(maximum_allowed_dead_code_ratio)
        finding_ids = tuple(str(row.get("finding_id", "")).strip().upper() for row in rows)
        finding_timestamps = tuple(self._integer(row.get("timestamp", 0)) for row in rows)

        lineage = (
            str(duplicate_report.get("milestone", "")).strip().upper() == "R"
            and str(duplicate_report.get("pack", "")).strip() == "2"
            and str(duplicate_report.get("status", "")).strip().upper() == "PASS"
            and bool(duplicate_report.get("duplicate_code_audit_passed", False))
            and str(duplicate_report.get("audit_id", "")).strip().upper().startswith("DAUD-")
        )
        unique = all(item.startswith("DEAD-") for item in finding_ids) and len(finding_ids) == len(set(finding_ids))
        chronology = all(ts > 0 and ts <= audit_ts for ts in finding_timestamps)
        schema_valid = all(self._finding_schema_valid(row) for row in rows)
        reviewed_count = sum(1 for row in rows if self._reviewed(row))
        all_reviewed = reviewed_count == len(rows)

        actionable = tuple(row for row in rows if self._actionable(row))
        retained = tuple(row for row in rows if self._retained(row))
        actionable_ids = tuple(str(row.get("finding_id", "")).strip().upper() for row in actionable)
        retained_ids = tuple(str(row.get("finding_id", "")).strip().upper() for row in retained)
        dead_lines = sum(max(0, self._integer(row.get("dead_line_count", 0))) for row in actionable)
        dead_ratio = round(dead_lines / scanned_lines, 12) if scanned_lines > 0 else 0.0
        ratio_valid = scanned_lines > 0 and 0.0 <= ratio_limit <= 1.0 and dead_ratio <= ratio_limit
        critical_count = self._severity_count(actionable, "CRITICAL")
        no_critical = critical_count == 0
        policy_valid = self._policy_valid(duplicate_report) and all(self._policy_valid(row) for row in rows)

        checks = (
            (not lineage, "duplicate_code_audit_lineage_invalid"),
            (not unique, "duplicate_or_invalid_dead_code_finding_id"),
            (not chronology, "dead_code_audit_chronology_invalid"),
            (not schema_valid, "dead_code_finding_schema_invalid"),
            (not all_reviewed, "dead_code_finding_review_incomplete"),
            (not ratio_valid, "dead_code_ratio_exceeds_limit_or_scan_invalid"),
            (not no_critical, "critical_dead_code_detected"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        passed = not blocked
        identity = {
            "duplicate_code_audit_id": str(duplicate_report.get("audit_id", "")),
            "finding_ids": finding_ids,
            "audit_timestamp": audit_ts,
            "scanned_line_count": scanned_lines,
            "dead_code_ratio": dead_ratio,
            "ratio_limit": ratio_limit,
            "blocked": blocked,
        }
        audit_id = "DCAUD-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if passed:
            reason = "DEAD_CODE_AUDIT_PASSED"
            en = (
                "Dead-code evidence passed deterministic audit. Actionable findings remain recorded for controlled "
                "Milestone R cleanup; no source removal or runtime rewiring was performed."
            )
            th = (
                "หลักฐาน dead code ผ่านการตรวจสอบแบบ deterministic โดยรายการที่ต้องดำเนินการยังถูกบันทึกไว้ "
                "สำหรับ cleanup แบบควบคุมใน Milestone R และยังไม่มีการลบ source หรือเปลี่ยน runtime wiring"
            )
        else:
            reason = "DEAD_CODE_AUDIT_BLOCKED"
            en = "Dead-code audit was blocked by lineage, evidence, chronology, review, ratio, severity, or frozen-policy controls."
            th = "Dead Code Audit ถูกระงับจาก lineage หลักฐาน ลำดับเวลา การทบทวน อัตรา ความรุนแรง หรือนโยบายล็อก"

        return ProductionDeadCodeAuditReport(
            audit_id=audit_id,
            status="PASS" if passed else "BLOCKED",
            reason=reason,
            milestone="R",
            pack="3",
            audit_timestamp=audit_ts,
            duplicate_code_audit_id=str(duplicate_report.get("audit_id", "")).strip().upper(),
            finding_count=len(rows),
            reviewed_finding_count=reviewed_count,
            unreachable_code_count=self._kind_count(rows, "UNREACHABLE"),
            unused_symbol_count=self._kind_count(rows, "UNUSED_SYMBOL"),
            unused_module_count=self._kind_count(rows, "UNUSED_MODULE"),
            obsolete_path_count=self._kind_count(rows, "OBSOLETE_PATH"),
            expected_retention_count=len(retained),
            actionable_dead_code_count=len(actionable),
            critical_dead_code_count=critical_count,
            high_dead_code_count=self._severity_count(actionable, "HIGH"),
            medium_dead_code_count=self._severity_count(actionable, "MEDIUM"),
            low_dead_code_count=self._severity_count(actionable, "LOW"),
            dead_line_count=dead_lines,
            dead_code_ratio=dead_ratio,
            maximum_allowed_dead_code_ratio=ratio_limit,
            duplicate_audit_lineage_valid=lineage,
            evidence_unique=unique,
            chronology_valid=chronology,
            finding_schema_valid=schema_valid,
            all_findings_reviewed=all_reviewed,
            dead_code_ratio_valid=ratio_valid,
            no_critical_dead_code=no_critical,
            locked_policy_valid=policy_valid,
            dead_code_audit_passed=passed,
            next_audit="R_ARCHITECTURE_AUDIT" if passed else "R_DEAD_CODE_REVIEW_REQUIRED",
            review_required=not passed,
            cleanup_required=bool(actionable),
            immutable_record=True,
            production_certification_granted=False,
            release_candidate_granted=False,
            block_reasons=blocked,
            finding_ids=finding_ids,
            actionable_finding_ids=actionable_ids,
            retained_finding_ids=retained_ids,
            explanation_reason_en=en,
            explanation_reason_th=th,
        )

    def _finding_schema_valid(self, row: Mapping[str, Any]) -> bool:
        kind = str(row.get("dead_code_kind", "")).strip().upper()
        severity = str(row.get("severity", "")).strip().upper()
        fingerprint = str(row.get("fingerprint", "")).strip().lower()
        references = self._integer(row.get("reference_count", 0))
        dead_lines = self._integer(row.get("dead_line_count", 0))
        retained = bool(row.get("retained_by_policy", False))
        return (
            kind in self.ALLOWED_KINDS
            and severity in self.ALLOWED_SEVERITIES
            and len(fingerprint) == 64
            and all(char in "0123456789abcdef" for char in fingerprint)
            and references >= 0
            and dead_lines >= 0
            and (kind == "RETAINED") == retained
        )

    def _reviewed(self, row: Mapping[str, Any]) -> bool:
        return str(row.get("review_status", "")).strip().upper() in self.ACCEPTED_REVIEW_STATUSES

    def _retained(self, row: Mapping[str, Any]) -> bool:
        return str(row.get("dead_code_kind", "")).strip().upper() == "RETAINED" and bool(row.get("retained_by_policy", False))

    def _actionable(self, row: Mapping[str, Any]) -> bool:
        return (
            not self._retained(row)
            and str(row.get("review_status", "")).strip().upper() == "REMEDIATION_REQUIRED"
        )

    @staticmethod
    def _kind_count(rows: Iterable[Mapping[str, Any]], kind: str) -> int:
        return sum(1 for row in rows if str(row.get("dead_code_kind", "")).strip().upper() == kind)

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
