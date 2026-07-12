"""Milestone R Pack 11: deterministic Release Candidate preparation."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ReleaseCandidatePreparationReport:
    preparation_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    preparation_timestamp: int
    certification_count: int
    valid_certification_count: int
    blocked_certification_count: int
    certification_ids_unique: bool
    chronology_valid: bool
    certification_schema_valid: bool
    production_certification_confirmed: bool
    artifact_manifest_valid: bool
    validation_manifest_valid: bool
    documentation_manifest_valid: bool
    execution_lock_confirmed: bool
    readiness_score: float
    release_candidate_prepared: bool
    release_candidate_granted: bool
    version_1_final_granted: bool
    next_stage: str
    review_required: bool
    immutable_record: bool
    block_reasons: tuple[str, ...]
    certification_ids: tuple[str, ...]
    blocked_certification_ids: tuple[str, ...]
    required_artifacts: tuple[str, ...]
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


class ReleaseCandidatePreparationRuntime:
    REQUIRED_ARTIFACTS = (
        "AFIP_PROJECT_DATABASE",
        "HANDOFF",
        "README_EN",
        "README_TH",
        "FILE_LIST",
        "VALIDATION_RECORD",
        "RUN_BAT",
        "RUN_PS1",
    )
    REQUIRED_VALIDATIONS = (
        "TARGETED_PYTEST",
        "FULL_PYTEST",
        "LOCAL_QUALITY_CHECK",
        "DASHBOARD_BUILD",
        "FINANCIAL_NAMING_VALIDATION",
        "MT5_DATA_CHECK",
    )

    def prepare(
        self,
        certification_reports: Iterable[Mapping[str, Any]],
        *,
        preparation_timestamp: int,
        artifact_manifest: Mapping[str, Any],
        validation_manifest: Mapping[str, Any],
        documentation_manifest: Mapping[str, Any],
        minimum_readiness_score: float = 1.0,
    ) -> ReleaseCandidatePreparationReport:
        rows = tuple(dict(item) for item in certification_reports)
        ts = self._int(preparation_timestamp)
        ids = tuple(str(row.get("certification_id", "")).strip().upper() for row in rows)
        unique = bool(ids) and len(ids) == len(set(ids)) and all(i.startswith("RCERT-") for i in ids)
        chronology = all(0 < self._int(row.get("certification_timestamp", 0)) <= ts for row in rows)
        schema = all(self._certification_schema(row) for row in rows)
        valid_rows = tuple(row for row in rows if self._certification_valid(row))
        blocked_rows = tuple(row for row in rows if not self._certification_valid(row))
        production_confirmed = len(rows) == 1 and len(valid_rows) == 1

        artifact_valid = self._manifest_complete(artifact_manifest, self.REQUIRED_ARTIFACTS)
        validation_valid = self._manifest_complete(validation_manifest, self.REQUIRED_VALIDATIONS)
        documentation_valid = self._documentation_valid(documentation_manifest)
        policy = all(self._policy(row) for row in rows) and self._policy({})

        checks_passed = sum(
            int(value)
            for value in (
                production_confirmed,
                unique,
                chronology,
                schema,
                artifact_valid,
                validation_valid,
                documentation_valid,
                policy,
            )
        )
        score = round(checks_passed / 8.0, 6)
        threshold = self._score(minimum_readiness_score)

        checks = (
            (not production_confirmed, "production_certification_not_confirmed"),
            (not unique, "duplicate_or_invalid_certification_id"),
            (not chronology, "release_candidate_chronology_invalid"),
            (not schema, "production_certification_schema_invalid"),
            (not artifact_valid, "release_candidate_artifact_manifest_incomplete"),
            (not validation_valid, "release_candidate_validation_manifest_incomplete"),
            (not documentation_valid, "release_candidate_documentation_manifest_incomplete"),
            (not policy, "feature_freeze_or_execution_policy_violation"),
            (score < threshold, "release_candidate_readiness_score_below_threshold"),
        )
        block_reasons = tuple(sorted({reason for condition, reason in checks if condition}))
        prepared = not block_reasons

        identity = {
            "certification_ids": ids,
            "preparation_timestamp": ts,
            "artifact_manifest": dict(sorted((str(k), bool(v)) for k, v in artifact_manifest.items())),
            "validation_manifest": dict(sorted((str(k), bool(v)) for k, v in validation_manifest.items())),
            "documentation_manifest": dict(sorted((str(k), bool(v)) for k, v in documentation_manifest.items())),
            "score": score,
            "blocked": block_reasons,
        }
        preparation_id = "RCPREP-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        return ReleaseCandidatePreparationReport(
            preparation_id=preparation_id,
            status="PREPARED" if prepared else "BLOCKED",
            reason="RELEASE_CANDIDATE_PREPARATION_COMPLETE" if prepared else "RELEASE_CANDIDATE_PREPARATION_BLOCKED",
            milestone="R",
            pack="11",
            preparation_timestamp=ts,
            certification_count=len(rows),
            valid_certification_count=len(valid_rows),
            blocked_certification_count=len(blocked_rows),
            certification_ids_unique=unique,
            chronology_valid=chronology,
            certification_schema_valid=schema,
            production_certification_confirmed=production_confirmed,
            artifact_manifest_valid=artifact_valid,
            validation_manifest_valid=validation_valid,
            documentation_manifest_valid=documentation_valid,
            execution_lock_confirmed=policy,
            readiness_score=score,
            release_candidate_prepared=prepared,
            release_candidate_granted=False,
            version_1_final_granted=False,
            next_stage="R_RELEASE_CANDIDATE_REVIEW" if prepared else "R_RELEASE_CANDIDATE_PREPARATION_REVIEW_REQUIRED",
            review_required=not prepared,
            immutable_record=True,
            block_reasons=block_reasons,
            certification_ids=ids,
            blocked_certification_ids=tuple(str(row.get("certification_id", "")).upper() for row in blocked_rows),
            required_artifacts=self.REQUIRED_ARTIFACTS,
            explanation_reason_en=(
                "Production Certification and all Release Candidate preparation manifests are complete. Release Candidate status remains ungranted pending final review."
                if prepared
                else "Release Candidate preparation is blocked by certification, chronology, schema, manifest, readiness, or locked-policy evidence."
            ),
            explanation_reason_th=(
                "Production Certification และรายการเตรียม Release Candidate ครบถ้วนแล้ว แต่ยังไม่ให้สถานะ Release Candidate จนกว่าจะผ่านการทบทวนขั้นสุดท้าย"
                if prepared
                else "การเตรียม Release Candidate ถูกระงับจากหลักฐานการรับรอง ลำดับเวลา schema รายการไฟล์ คะแนนความพร้อม หรือนโยบายล็อก"
            ),
        )

    def _certification_schema(self, row: Mapping[str, Any]) -> bool:
        return (
            str(row.get("milestone", "")).upper() == "R"
            and str(row.get("pack", "")).strip() == "10"
            and str(row.get("status", "")).upper() == "CERTIFIED"
            and str(row.get("reason", "")).upper() == "PRODUCTION_CERTIFICATION_GRANTED"
            and bool(row.get("production_certification_granted", False))
            and not bool(row.get("release_candidate_granted", False))
            and not bool(row.get("version_1_final_granted", False))
        )

    def _certification_valid(self, row: Mapping[str, Any]) -> bool:
        return self._certification_schema(row) and self._policy(row)

    def _manifest_complete(self, manifest: Mapping[str, Any], required: Iterable[str]) -> bool:
        return all(bool(manifest.get(key, False)) for key in required)

    def _documentation_valid(self, manifest: Mapping[str, Any]) -> bool:
        return all(
            bool(manifest.get(key, False))
            for key in ("README_EN", "README_TH", "AFIP_PROJECT_DATABASE", "HANDOFF")
        )

    def _policy(self, row: Mapping[str, Any]) -> bool:
        return (
            str(row.get("broker", "XM")) == "XM"
            and str(row.get("symbol", "GOLD#")) == "GOLD#"
            and float(row.get("base_lot_per_unit", 0.01)) == 0.01
            and str(row.get("execution_status", "LOCKED_SIMULATION_ONLY")) == "LOCKED_SIMULATION_ONLY"
            and not bool(row.get("direct_execution", False))
            and not bool(row.get("live_execution_enabled", False))
            and str(row.get("order_status", "NO_ORDER_SENT")) == "NO_ORDER_SENT"
            and not any(
                bool(row.get(key, False))
                for key in (
                    "execution_unlock_authorized",
                    "broker_request_created",
                    "order_transmission_attempted",
                    "position_modification_attempted",
                    "trading_logic_changed",
                )
            )
        )

    def _score(self, value: Any) -> float:
        try:
            return min(max(float(value), 0.0), 1.0)
        except (TypeError, ValueError):
            return 1.0

    def _int(self, value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
