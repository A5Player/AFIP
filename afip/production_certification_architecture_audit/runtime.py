"""Milestone R Pack 4: deterministic production architecture audit.

The audit evaluates supplied architecture evidence only. It never rewires
runtime dependencies, refactors modules, grants Production Certification, or
enables execution.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ProductionArchitectureAuditReport:
    audit_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    audit_timestamp: int
    dead_code_audit_id: str
    finding_count: int
    reviewed_finding_count: int
    boundary_violation_count: int
    dependency_direction_violation_count: int
    cycle_count: int
    public_api_violation_count: int
    policy_violation_count: int
    expected_exception_count: int
    actionable_architecture_count: int
    critical_architecture_count: int
    high_architecture_count: int
    medium_architecture_count: int
    low_architecture_count: int
    architecture_score: float
    minimum_architecture_score: float
    dead_code_audit_lineage_valid: bool
    evidence_unique: bool
    chronology_valid: bool
    finding_schema_valid: bool
    all_findings_reviewed: bool
    architecture_score_valid: bool
    no_critical_architecture_violation: bool
    locked_policy_valid: bool
    architecture_audit_passed: bool
    next_audit: str
    review_required: bool
    cleanup_required: bool
    immutable_record: bool
    production_certification_granted: bool
    release_candidate_granted: bool
    block_reasons: tuple[str, ...]
    finding_ids: tuple[str, ...]
    actionable_finding_ids: tuple[str, ...]
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
    architecture_change_performed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProductionArchitectureAuditRuntime:
    """Audit architecture evidence while preserving Feature Freeze and execution lock."""

    ALLOWED_KINDS = frozenset({
        "BOUNDARY_VIOLATION", "DEPENDENCY_DIRECTION", "DEPENDENCY_CYCLE",
        "PUBLIC_API", "POLICY_VIOLATION", "ACCEPTED_EXCEPTION",
    })
    ALLOWED_SEVERITIES = frozenset({"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"})
    ACCEPTED_REVIEW_STATUSES = frozenset({"REVIEWED", "ACCEPTED", "REMEDIATION_REQUIRED"})

    def audit(
        self,
        dead_code_report: Mapping[str, Any],
        findings: Iterable[Mapping[str, Any]],
        *,
        audit_timestamp: int,
        inspected_component_count: int,
        minimum_architecture_score: float = 0.90,
    ) -> ProductionArchitectureAuditReport:
        rows = tuple(dict(item) for item in findings)
        audit_ts = self._integer(audit_timestamp)
        component_count = self._integer(inspected_component_count)
        minimum_score = self._ratio(minimum_architecture_score)
        finding_ids = tuple(str(row.get("finding_id", "")).strip().upper() for row in rows)
        timestamps = tuple(self._integer(row.get("timestamp", 0)) for row in rows)

        lineage = (
            str(dead_code_report.get("milestone", "")).strip().upper() == "R"
            and str(dead_code_report.get("pack", "")).strip() == "3"
            and str(dead_code_report.get("status", "")).strip().upper() == "PASS"
            and bool(dead_code_report.get("dead_code_audit_passed", False))
            and str(dead_code_report.get("audit_id", "")).strip().upper().startswith("DCAUD-")
        )
        unique = all(item.startswith("ARCH-") for item in finding_ids) and len(finding_ids) == len(set(finding_ids))
        chronology = all(ts > 0 and ts <= audit_ts for ts in timestamps)
        schema_valid = all(self._finding_schema_valid(row) for row in rows)
        reviewed_count = sum(1 for row in rows if self._reviewed(row))
        all_reviewed = reviewed_count == len(rows)
        actionable = tuple(row for row in rows if self._actionable(row))
        accepted = tuple(row for row in rows if self._accepted_exception(row))
        actionable_ids = tuple(str(row.get("finding_id", "")).strip().upper() for row in actionable)
        accepted_ids = tuple(str(row.get("finding_id", "")).strip().upper() for row in accepted)

        weighted_penalty = sum(self._severity_weight(row.get("severity")) for row in actionable)
        denominator = max(component_count * 4, 1)
        architecture_score = round(max(0.0, 1.0 - (weighted_penalty / denominator)), 12)
        score_valid = component_count > 0 and 0.0 <= minimum_score <= 1.0 and architecture_score >= minimum_score
        critical_count = self._severity_count(actionable, "CRITICAL")
        no_critical = critical_count == 0
        policy_valid = self._policy_valid(dead_code_report) and all(self._policy_valid(row) for row in rows)

        checks = (
            (not lineage, "dead_code_audit_lineage_invalid"),
            (not unique, "duplicate_or_invalid_architecture_finding_id"),
            (not chronology, "architecture_audit_chronology_invalid"),
            (not schema_valid, "architecture_finding_schema_invalid"),
            (not all_reviewed, "architecture_finding_review_incomplete"),
            (not score_valid, "architecture_score_below_minimum_or_component_count_invalid"),
            (not no_critical, "critical_architecture_violation_detected"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        passed = not blocked
        identity = {
            "dead_code_audit_id": str(dead_code_report.get("audit_id", "")),
            "finding_ids": finding_ids,
            "audit_timestamp": audit_ts,
            "component_count": component_count,
            "architecture_score": architecture_score,
            "minimum_score": minimum_score,
            "blocked": blocked,
        }
        audit_id = "ARAUD-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if passed:
            reason = "ARCHITECTURE_AUDIT_PASSED"
            en = (
                "Architecture evidence passed deterministic audit. Actionable findings remain recorded for controlled "
                "Milestone R cleanup; no refactor, dependency rewiring, or runtime change was performed."
            )
            th = (
                "หลักฐานสถาปัตยกรรมผ่านการตรวจสอบแบบ deterministic โดยรายการที่ต้องดำเนินการยังถูกบันทึกไว้ "
                "สำหรับ cleanup แบบควบคุมใน Milestone R และยังไม่มีการ refactor เปลี่ยน dependency หรือ runtime"
            )
        else:
            reason = "ARCHITECTURE_AUDIT_BLOCKED"
            en = "Architecture audit was blocked by lineage, evidence, chronology, review, score, severity, or frozen-policy controls."
            th = "Architecture Audit ถูกระงับจาก lineage หลักฐาน ลำดับเวลา การทบทวน คะแนน ความรุนแรง หรือนโยบายล็อก"

        return ProductionArchitectureAuditReport(
            audit_id=audit_id,
            status="PASS" if passed else "BLOCKED",
            reason=reason,
            milestone="R",
            pack="4",
            audit_timestamp=audit_ts,
            dead_code_audit_id=str(dead_code_report.get("audit_id", "")).strip().upper(),
            finding_count=len(rows),
            reviewed_finding_count=reviewed_count,
            boundary_violation_count=self._kind_count(rows, "BOUNDARY_VIOLATION"),
            dependency_direction_violation_count=self._kind_count(rows, "DEPENDENCY_DIRECTION"),
            cycle_count=self._kind_count(rows, "DEPENDENCY_CYCLE"),
            public_api_violation_count=self._kind_count(rows, "PUBLIC_API"),
            policy_violation_count=self._kind_count(rows, "POLICY_VIOLATION"),
            expected_exception_count=len(accepted),
            actionable_architecture_count=len(actionable),
            critical_architecture_count=critical_count,
            high_architecture_count=self._severity_count(actionable, "HIGH"),
            medium_architecture_count=self._severity_count(actionable, "MEDIUM"),
            low_architecture_count=self._severity_count(actionable, "LOW"),
            architecture_score=architecture_score,
            minimum_architecture_score=minimum_score,
            dead_code_audit_lineage_valid=lineage,
            evidence_unique=unique,
            chronology_valid=chronology,
            finding_schema_valid=schema_valid,
            all_findings_reviewed=all_reviewed,
            architecture_score_valid=score_valid,
            no_critical_architecture_violation=no_critical,
            locked_policy_valid=policy_valid,
            architecture_audit_passed=passed,
            next_audit="R_REPOSITORY_CLEANUP" if passed else "R_ARCHITECTURE_REVIEW_REQUIRED",
            review_required=not passed,
            cleanup_required=bool(actionable),
            immutable_record=True,
            production_certification_granted=False,
            release_candidate_granted=False,
            block_reasons=blocked,
            finding_ids=finding_ids,
            actionable_finding_ids=actionable_ids,
            accepted_exception_ids=accepted_ids,
            explanation_reason_en=en,
            explanation_reason_th=th,
        )

    def _finding_schema_valid(self, row: Mapping[str, Any]) -> bool:
        kind = str(row.get("architecture_kind", "")).strip().upper()
        severity = str(row.get("severity", "")).strip().upper()
        fingerprint = str(row.get("fingerprint", "")).strip().lower()
        source = str(row.get("source_component", "")).strip()
        target = str(row.get("target_component", "")).strip()
        accepted = bool(row.get("accepted_exception", False))
        return (
            kind in self.ALLOWED_KINDS
            and severity in self.ALLOWED_SEVERITIES
            and len(fingerprint) == 64
            and all(char in "0123456789abcdef" for char in fingerprint)
            and bool(source)
            and bool(target)
            and (kind == "ACCEPTED_EXCEPTION") == accepted
        )

    def _reviewed(self, row: Mapping[str, Any]) -> bool:
        return str(row.get("review_status", "")).strip().upper() in self.ACCEPTED_REVIEW_STATUSES

    def _accepted_exception(self, row: Mapping[str, Any]) -> bool:
        return str(row.get("architecture_kind", "")).strip().upper() == "ACCEPTED_EXCEPTION" and bool(row.get("accepted_exception", False))

    def _actionable(self, row: Mapping[str, Any]) -> bool:
        return not self._accepted_exception(row) and str(row.get("review_status", "")).strip().upper() == "REMEDIATION_REQUIRED"

    @staticmethod
    def _kind_count(rows: Iterable[Mapping[str, Any]], kind: str) -> int:
        return sum(1 for row in rows if str(row.get("architecture_kind", "")).strip().upper() == kind)

    @staticmethod
    def _severity_count(rows: Iterable[Mapping[str, Any]], severity: str) -> int:
        return sum(1 for row in rows if str(row.get("severity", "")).strip().upper() == severity)

    @staticmethod
    def _severity_weight(value: Any) -> int:
        return {"CRITICAL": 8, "HIGH": 4, "MEDIUM": 2, "LOW": 1, "INFO": 0}.get(str(value).strip().upper(), 8)

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
