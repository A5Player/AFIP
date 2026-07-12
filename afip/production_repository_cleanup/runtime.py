"""Milestone R Pack 5: deterministic production repository cleanup governance.

This layer validates evidence for narrowly scoped repository cleanup. It does
not delete source files, alter trading logic, rewire dependencies, grant
Production Certification, or enable execution.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ProductionRepositoryCleanupReport:
    cleanup_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    cleanup_timestamp: int
    architecture_audit_id: str
    action_count: int
    reviewed_action_count: int
    completed_action_count: int
    generated_artifact_count: int
    cache_artifact_count: int
    obsolete_document_count: int
    stale_test_artifact_count: int
    retained_policy_artifact_count: int
    rejected_action_count: int
    authorized_action_count: int
    architecture_audit_lineage_valid: bool
    action_ids_unique: bool
    chronology_valid: bool
    action_schema_valid: bool
    all_actions_reviewed: bool
    all_authorized_actions_completed: bool
    no_protected_source_targeted: bool
    locked_policy_valid: bool
    repository_cleanup_passed: bool
    next_audit: str
    review_required: bool
    immutable_record: bool
    production_certification_granted: bool
    release_candidate_granted: bool
    block_reasons: tuple[str, ...]
    action_ids: tuple[str, ...]
    authorized_action_ids: tuple[str, ...]
    retained_action_ids: tuple[str, ...]
    rejected_action_ids: tuple[str, ...]
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
    dependency_wiring_changed: bool = False
    protected_source_removed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProductionRepositoryCleanupRuntime:
    """Validate controlled cleanup evidence under Version 1.0 Feature Freeze."""

    ALLOWED_ACTION_KINDS = frozenset({
        "GENERATED_ARTIFACT", "CACHE_ARTIFACT", "OBSOLETE_DOCUMENT",
        "STALE_TEST_ARTIFACT", "POLICY_RETAINED",
    })
    ALLOWED_REVIEW_STATUSES = frozenset({"REVIEWED", "ACCEPTED", "REJECTED"})
    ALLOWED_COMPLETION_STATUSES = frozenset({"COMPLETED", "RETAINED", "REJECTED"})

    def validate(
        self,
        architecture_report: Mapping[str, Any],
        actions: Iterable[Mapping[str, Any]],
        *,
        cleanup_timestamp: int,
    ) -> ProductionRepositoryCleanupReport:
        rows = tuple(dict(item) for item in actions)
        cleanup_ts = self._integer(cleanup_timestamp)
        action_ids = tuple(str(row.get("action_id", "")).strip().upper() for row in rows)
        timestamps = tuple(self._integer(row.get("timestamp", 0)) for row in rows)

        lineage = (
            str(architecture_report.get("milestone", "")).strip().upper() == "R"
            and str(architecture_report.get("pack", "")).strip() == "4"
            and str(architecture_report.get("status", "")).strip().upper() == "PASS"
            and bool(architecture_report.get("architecture_audit_passed", False))
            and str(architecture_report.get("audit_id", "")).strip().upper().startswith("ARAUD-")
        )
        unique = all(item.startswith("CLEAN-") for item in action_ids) and len(action_ids) == len(set(action_ids))
        chronology = all(ts > 0 and ts <= cleanup_ts for ts in timestamps)
        schema_valid = all(self._action_schema_valid(row) for row in rows)
        reviewed_count = sum(1 for row in rows if self._reviewed(row))
        all_reviewed = reviewed_count == len(rows)

        authorized = tuple(row for row in rows if self._authorized(row))
        retained = tuple(row for row in rows if self._retained(row))
        rejected = tuple(row for row in rows if self._rejected(row))
        completed_count = sum(1 for row in authorized if str(row.get("completion_status", "")).strip().upper() == "COMPLETED")
        all_completed = completed_count == len(authorized)
        no_protected = not any(
            bool(row.get("protected_source", False)) and bool(row.get("cleanup_authorized", False))
            for row in rows
        )
        policy_valid = self._policy_valid(architecture_report) and all(self._policy_valid(row) for row in rows)

        checks = (
            (not lineage, "architecture_audit_lineage_invalid"),
            (not unique, "duplicate_or_invalid_cleanup_action_id"),
            (not chronology, "repository_cleanup_chronology_invalid"),
            (not schema_valid, "repository_cleanup_action_schema_invalid"),
            (not all_reviewed, "repository_cleanup_review_incomplete"),
            (not all_completed, "authorized_cleanup_action_incomplete"),
            (not no_protected, "protected_source_cleanup_attempt_detected"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        passed = not blocked
        identity = {
            "architecture_audit_id": str(architecture_report.get("audit_id", "")),
            "action_ids": action_ids,
            "cleanup_timestamp": cleanup_ts,
            "authorized": tuple(str(row.get("action_id", "")).upper() for row in authorized),
            "blocked": blocked,
        }
        cleanup_id = "RCLEAN-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if passed:
            reason = "REPOSITORY_CLEANUP_PASSED"
            en = (
                "Controlled repository cleanup evidence passed deterministic validation. Only reviewed non-source "
                "artifacts were authorized; trading logic, protected source, dependency wiring, and execution remain unchanged."
            )
            th = (
                "หลักฐาน Repository Cleanup แบบควบคุมผ่านการตรวจสอบ deterministic โดยอนุญาตเฉพาะรายการที่ผ่านการทบทวน "
                "และไม่ใช่ source ที่ได้รับการคุ้มครอง ส่วน trading logic, dependency wiring และ execution ไม่เปลี่ยนแปลง"
            )
        else:
            reason = "REPOSITORY_CLEANUP_BLOCKED"
            en = "Repository cleanup was blocked by lineage, evidence, chronology, review, completion, protected-source, or frozen-policy controls."
            th = "Repository Cleanup ถูกระงับจาก lineage หลักฐาน ลำดับเวลา การทบทวน ความครบถ้วน source ที่คุ้มครอง หรือนโยบายล็อก"

        return ProductionRepositoryCleanupReport(
            cleanup_id=cleanup_id,
            status="PASS" if passed else "BLOCKED",
            reason=reason,
            milestone="R",
            pack="5",
            cleanup_timestamp=cleanup_ts,
            architecture_audit_id=str(architecture_report.get("audit_id", "")).strip().upper(),
            action_count=len(rows),
            reviewed_action_count=reviewed_count,
            completed_action_count=completed_count,
            generated_artifact_count=self._kind_count(rows, "GENERATED_ARTIFACT"),
            cache_artifact_count=self._kind_count(rows, "CACHE_ARTIFACT"),
            obsolete_document_count=self._kind_count(rows, "OBSOLETE_DOCUMENT"),
            stale_test_artifact_count=self._kind_count(rows, "STALE_TEST_ARTIFACT"),
            retained_policy_artifact_count=len(retained),
            rejected_action_count=len(rejected),
            authorized_action_count=len(authorized),
            architecture_audit_lineage_valid=lineage,
            action_ids_unique=unique,
            chronology_valid=chronology,
            action_schema_valid=schema_valid,
            all_actions_reviewed=all_reviewed,
            all_authorized_actions_completed=all_completed,
            no_protected_source_targeted=no_protected,
            locked_policy_valid=policy_valid,
            repository_cleanup_passed=passed,
            next_audit="R_SAFETY_AUDIT" if passed else "R_REPOSITORY_CLEANUP_REVIEW_REQUIRED",
            review_required=not passed,
            immutable_record=True,
            production_certification_granted=False,
            release_candidate_granted=False,
            block_reasons=blocked,
            action_ids=action_ids,
            authorized_action_ids=tuple(str(row.get("action_id", "")).strip().upper() for row in authorized),
            retained_action_ids=tuple(str(row.get("action_id", "")).strip().upper() for row in retained),
            rejected_action_ids=tuple(str(row.get("action_id", "")).strip().upper() for row in rejected),
            explanation_reason_en=en,
            explanation_reason_th=th,
        )

    def _action_schema_valid(self, row: Mapping[str, Any]) -> bool:
        kind = str(row.get("action_kind", "")).strip().upper()
        review = str(row.get("review_status", "")).strip().upper()
        completion = str(row.get("completion_status", "")).strip().upper()
        fingerprint = str(row.get("fingerprint", "")).strip().lower()
        target_path = str(row.get("target_path", "")).strip()
        return (
            kind in self.ALLOWED_ACTION_KINDS
            and review in self.ALLOWED_REVIEW_STATUSES
            and completion in self.ALLOWED_COMPLETION_STATUSES
            and len(fingerprint) == 64
            and all(ch in "0123456789abcdef" for ch in fingerprint)
            and bool(target_path)
        )

    def _authorized(self, row: Mapping[str, Any]) -> bool:
        return (
            str(row.get("review_status", "")).strip().upper() in {"REVIEWED", "ACCEPTED"}
            and str(row.get("action_kind", "")).strip().upper() != "POLICY_RETAINED"
            and not bool(row.get("protected_source", False))
            and bool(row.get("cleanup_authorized", False))
        )

    @staticmethod
    def _retained(row: Mapping[str, Any]) -> bool:
        return (
            str(row.get("action_kind", "")).strip().upper() == "POLICY_RETAINED"
            and str(row.get("completion_status", "")).strip().upper() == "RETAINED"
        )

    @staticmethod
    def _rejected(row: Mapping[str, Any]) -> bool:
        return str(row.get("completion_status", "")).strip().upper() == "REJECTED"

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
    def _kind_count(rows: Iterable[Mapping[str, Any]], kind: str) -> int:
        return sum(1 for row in rows if str(row.get("action_kind", "")).strip().upper() == kind)

    @staticmethod
    def _integer(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
