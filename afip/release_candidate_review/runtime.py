"""Milestone R Pack 12: deterministic Release Candidate review."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ReleaseCandidateReviewReport:
    review_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    review_timestamp: int
    preparation_count: int
    valid_preparation_count: int
    blocked_preparation_count: int
    preparation_ids_unique: bool
    chronology_valid: bool
    preparation_schema_valid: bool
    release_candidate_preparation_confirmed: bool
    reviewer_manifest_valid: bool
    validation_manifest_valid: bool
    documentation_manifest_valid: bool
    execution_lock_confirmed: bool
    review_score: float
    release_candidate_prepared: bool
    release_candidate_granted: bool
    version_1_final_granted: bool
    next_stage: str
    review_required: bool
    immutable_record: bool
    block_reasons: tuple[str, ...]
    preparation_ids: tuple[str, ...]
    blocked_preparation_ids: tuple[str, ...]
    required_reviewers: tuple[str, ...]
    explanation_reason_en: str
    explanation_reason_th: str
    broker: str = "XM"
    symbol: str = "GOLD#"
    base_lot_per_unit: float = 0.01
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    direct_execution: bool = False
    live_execution_enabled: bool = False
    order_status: str = "NO_ORDER_SENT"
    execution_unlock_authorized: bool = False
    broker_request_created: bool = False
    order_transmission_attempted: bool = False
    position_modification_attempted: bool = False
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReleaseCandidateReviewRuntime:
    REQUIRED_REVIEWERS = (
        "PRODUCTION_CERTIFICATION_REVIEW",
        "REGRESSION_REVIEW",
        "SAFETY_REVIEW",
        "SECURITY_REVIEW",
        "DATA_INTEGRITY_REVIEW",
        "PERFORMANCE_REVIEW",
    )
    REQUIRED_VALIDATIONS = (
        "TARGETED_PYTEST",
        "FULL_PYTEST",
        "LOCAL_QUALITY_CHECK",
        "DASHBOARD_BUILD",
        "FINANCIAL_NAMING_VALIDATION",
        "MT5_DATA_CHECK",
    )

    def review(
        self,
        preparation_reports: Iterable[Mapping[str, Any]],
        *,
        review_timestamp: int,
        reviewer_manifest: Mapping[str, Any],
        validation_manifest: Mapping[str, Any],
        documentation_manifest: Mapping[str, Any],
        minimum_review_score: float = 1.0,
    ) -> ReleaseCandidateReviewReport:
        rows = tuple(dict(item) for item in preparation_reports)
        ts = self._int(review_timestamp)
        ids = tuple(str(row.get("preparation_id", "")).strip().upper() for row in rows)
        unique = bool(ids) and len(ids) == len(set(ids)) and all(i.startswith("RCPREP-") for i in ids)
        chronology = all(0 < self._int(row.get("preparation_timestamp", 0)) <= ts for row in rows)
        schema = all(self._preparation_schema(row) for row in rows)
        valid_rows = tuple(row for row in rows if self._preparation_valid(row))
        blocked_rows = tuple(row for row in rows if not self._preparation_valid(row))
        preparation_confirmed = len(rows) == 1 and len(valid_rows) == 1

        reviewer_valid = self._manifest_complete(reviewer_manifest, self.REQUIRED_REVIEWERS)
        validation_valid = self._manifest_complete(validation_manifest, self.REQUIRED_VALIDATIONS)
        documentation_valid = self._documentation_valid(documentation_manifest)
        policy = all(self._policy(row) for row in rows) and self._policy({})

        checks_passed = sum(int(value) for value in (
            preparation_confirmed,
            unique,
            chronology,
            schema,
            reviewer_valid,
            validation_valid,
            documentation_valid,
            policy,
        ))
        score = round(checks_passed / 8.0, 6)
        threshold = self._score(minimum_review_score)
        checks = (
            (not preparation_confirmed, "release_candidate_preparation_not_confirmed"),
            (not unique, "duplicate_or_invalid_preparation_id"),
            (not chronology, "release_candidate_review_chronology_invalid"),
            (not schema, "release_candidate_preparation_schema_invalid"),
            (not reviewer_valid, "release_candidate_reviewer_manifest_incomplete"),
            (not validation_valid, "release_candidate_review_validation_manifest_incomplete"),
            (not documentation_valid, "release_candidate_review_documentation_manifest_incomplete"),
            (not policy, "feature_freeze_or_execution_policy_violation"),
            (score < threshold, "release_candidate_review_score_below_threshold"),
        )
        block_reasons = tuple(sorted({reason for condition, reason in checks if condition}))
        granted = not block_reasons

        identity = {
            "preparation_ids": ids,
            "review_timestamp": ts,
            "reviewer_manifest": dict(sorted((str(k), bool(v)) for k, v in reviewer_manifest.items())),
            "validation_manifest": dict(sorted((str(k), bool(v)) for k, v in validation_manifest.items())),
            "documentation_manifest": dict(sorted((str(k), bool(v)) for k, v in documentation_manifest.items())),
            "score": score,
            "blocked": block_reasons,
        }
        review_id = "RCREV-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        return ReleaseCandidateReviewReport(
            review_id=review_id,
            status="APPROVED" if granted else "BLOCKED",
            reason="RELEASE_CANDIDATE_REVIEW_APPROVED" if granted else "RELEASE_CANDIDATE_REVIEW_BLOCKED",
            milestone="R",
            pack="12",
            review_timestamp=ts,
            preparation_count=len(rows),
            valid_preparation_count=len(valid_rows),
            blocked_preparation_count=len(blocked_rows),
            preparation_ids_unique=unique,
            chronology_valid=chronology,
            preparation_schema_valid=schema,
            release_candidate_preparation_confirmed=preparation_confirmed,
            reviewer_manifest_valid=reviewer_valid,
            validation_manifest_valid=validation_valid,
            documentation_manifest_valid=documentation_valid,
            execution_lock_confirmed=policy,
            review_score=score,
            release_candidate_prepared=preparation_confirmed,
            release_candidate_granted=granted,
            version_1_final_granted=False,
            next_stage="R_VERSION_1_FINAL_REVIEW" if granted else "R_RELEASE_CANDIDATE_REVIEW_REQUIRED",
            review_required=not granted,
            immutable_record=True,
            block_reasons=block_reasons,
            preparation_ids=ids,
            blocked_preparation_ids=tuple(str(row.get("preparation_id", "")).upper() for row in blocked_rows),
            required_reviewers=self.REQUIRED_REVIEWERS,
            explanation_reason_en=(
                "Release Candidate review is approved. Version 1.0 Final remains ungranted and execution remains locked."
                if granted else
                "Release Candidate review is blocked by preparation, chronology, schema, reviewer, validation, documentation, score, or locked-policy evidence."
            ),
            explanation_reason_th=(
                "การทบทวน Release Candidate ผ่านแล้ว แต่ยังไม่ให้สถานะ Version 1.0 Final และ execution ยังคงถูกล็อก"
                if granted else
                "การทบทวน Release Candidate ถูกระงับจากหลักฐานการเตรียม ลำดับเวลา schema ผู้ทบทวน validation เอกสาร คะแนน หรือนโยบายล็อก"
            ),
        )

    def _preparation_schema(self, row: Mapping[str, Any]) -> bool:
        return (
            str(row.get("milestone", "")).upper() == "R"
            and str(row.get("pack", "")).strip() == "11"
            and str(row.get("status", "")).upper() == "PREPARED"
            and str(row.get("reason", "")).upper() == "RELEASE_CANDIDATE_PREPARATION_COMPLETE"
            and bool(row.get("release_candidate_prepared", False))
            and not bool(row.get("release_candidate_granted", False))
            and not bool(row.get("version_1_final_granted", False))
        )

    def _preparation_valid(self, row: Mapping[str, Any]) -> bool:
        return self._preparation_schema(row) and self._policy(row)

    def _manifest_complete(self, manifest: Mapping[str, Any], required: Iterable[str]) -> bool:
        return all(bool(manifest.get(key, False)) for key in required)

    def _documentation_valid(self, manifest: Mapping[str, Any]) -> bool:
        return all(bool(manifest.get(key, False)) for key in (
            "README_EN", "README_TH", "AFIP_PROJECT_DATABASE", "HANDOFF", "FILE_LIST", "VALIDATION_RECORD"
        ))

    def _policy(self, row: Mapping[str, Any]) -> bool:
        return (
            str(row.get("broker", "XM")) == "XM"
            and str(row.get("symbol", "GOLD#")) == "GOLD#"
            and float(row.get("base_lot_per_unit", 0.01)) == 0.01
            and str(row.get("execution_status", "LOCKED_SIMULATION_ONLY")) == "LOCKED_SIMULATION_ONLY"
            and not bool(row.get("direct_execution", False))
            and not bool(row.get("live_execution_enabled", False))
            and str(row.get("order_status", "NO_ORDER_SENT")) == "NO_ORDER_SENT"
            and not any(bool(row.get(key, False)) for key in (
                "execution_unlock_authorized", "broker_request_created", "order_transmission_attempted",
                "position_modification_attempted", "trading_logic_changed"
            ))
        )

    @staticmethod
    def _int(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _score(value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 1.0
