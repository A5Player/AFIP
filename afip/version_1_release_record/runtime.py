"""AFIP Version 1.0 deterministic immutable release record."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class Version1ReleaseRecord:
    release_record_id: str
    status: str
    reason: str
    version: str
    milestone: str
    pack: str
    release_timestamp: int
    final_review_count: int
    valid_final_review_count: int
    final_review_ids_unique: bool
    chronology_valid: bool
    final_review_schema_valid: bool
    final_identity_confirmed: bool
    validation_manifest_valid: bool
    documentation_manifest_valid: bool
    release_metadata_valid: bool
    execution_lock_confirmed: bool
    release_score: float
    production_certification_granted: bool
    release_candidate_granted: bool
    version_1_final_granted: bool
    release_record_granted: bool
    immutable_record: bool
    block_reasons: tuple[str, ...]
    final_review_ids: tuple[str, ...]
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


class Version1ReleaseRecordRuntime:
    REQUIRED_VALIDATIONS = (
        "TARGETED_PYTEST", "FULL_PYTEST", "LOCAL_QUALITY_CHECK", "DASHBOARD_BUILD",
        "FINANCIAL_NAMING_VALIDATION", "MT5_DATA_CHECK",
    )
    REQUIRED_DOCUMENTS = (
        "README_EN", "README_TH", "AFIP_PROJECT_DATABASE", "HANDOFF", "FILE_LIST",
        "VALIDATION_RECORD", "RELEASE_RECORD",
    )
    REQUIRED_METADATA = (
        "VERSION", "RELEASE_NAME", "RELEASE_STATUS", "BROKER_POLICY", "SYMBOL_POLICY",
        "BASE_UNIT_POLICY", "EXECUTION_POLICY",
    )

    def create(
        self,
        final_review_reports: Iterable[Mapping[str, Any]],
        *,
        release_timestamp: int,
        validation_manifest: Mapping[str, Any],
        documentation_manifest: Mapping[str, Any],
        release_metadata: Mapping[str, Any],
        minimum_release_score: float = 1.0,
    ) -> Version1ReleaseRecord:
        rows = tuple(dict(item) for item in final_review_reports)
        ts = self._int(release_timestamp)
        ids = tuple(str(row.get("final_review_id", "")).strip().upper() for row in rows)
        unique = bool(ids) and len(ids) == len(set(ids)) and all(i.startswith("V1FINAL-") for i in ids)
        chronology = all(0 < self._int(row.get("review_timestamp", 0)) <= ts for row in rows)
        schema = all(self._final_review_schema(row) for row in rows)
        valid = tuple(row for row in rows if self._final_review_schema(row) and self._policy(row))
        final_confirmed = len(rows) == 1 and len(valid) == 1
        validation_valid = self._manifest_complete(validation_manifest, self.REQUIRED_VALIDATIONS)
        documentation_valid = self._manifest_complete(documentation_manifest, self.REQUIRED_DOCUMENTS)
        metadata_valid = self._metadata_valid(release_metadata)
        policy = all(self._policy(row) for row in rows) and self._policy({})
        passed = sum(int(v) for v in (
            final_confirmed, unique, chronology, schema, validation_valid,
            documentation_valid, metadata_valid, policy,
        ))
        score = round(passed / 8.0, 6)
        threshold = self._score(minimum_release_score)
        checks = (
            (not final_confirmed, "version_1_final_identity_not_confirmed"),
            (not unique, "duplicate_or_invalid_final_review_id"),
            (not chronology, "release_record_chronology_invalid"),
            (not schema, "final_review_schema_invalid"),
            (not validation_valid, "release_validation_manifest_incomplete"),
            (not documentation_valid, "release_documentation_manifest_incomplete"),
            (not metadata_valid, "release_metadata_invalid"),
            (not policy, "feature_freeze_or_execution_policy_violation"),
            (score < threshold, "release_score_below_threshold"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        granted = not blocked
        identity = {
            "final_review_ids": ids,
            "release_timestamp": ts,
            "validation_manifest": dict(sorted((str(k), bool(v)) for k, v in validation_manifest.items())),
            "documentation_manifest": dict(sorted((str(k), bool(v)) for k, v in documentation_manifest.items())),
            "release_metadata": dict(sorted((str(k), str(v)) for k, v in release_metadata.items())),
            "score": score,
            "blocked": blocked,
        }
        record_id = "V1RELEASE-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()
        return Version1ReleaseRecord(
            release_record_id=record_id,
            status="RELEASED" if granted else "BLOCKED",
            reason="VERSION_1_RELEASE_RECORDED" if granted else "VERSION_1_RELEASE_RECORD_BLOCKED",
            version="1.0" if granted else "UNGRANTED",
            milestone="R",
            pack="14",
            release_timestamp=ts,
            final_review_count=len(rows),
            valid_final_review_count=len(valid),
            final_review_ids_unique=unique,
            chronology_valid=chronology,
            final_review_schema_valid=schema,
            final_identity_confirmed=final_confirmed,
            validation_manifest_valid=validation_valid,
            documentation_manifest_valid=documentation_valid,
            release_metadata_valid=metadata_valid,
            execution_lock_confirmed=policy,
            release_score=score,
            production_certification_granted=granted,
            release_candidate_granted=granted,
            version_1_final_granted=granted,
            release_record_granted=granted,
            immutable_record=True,
            block_reasons=blocked,
            final_review_ids=ids,
            explanation_reason_en=(
                "AFIP Version 1.0 release is recorded while direct and live execution remain locked."
                if granted else "AFIP Version 1.0 release record is blocked by incomplete or invalid evidence."
            ),
            explanation_reason_th=(
                "บันทึกการออก AFIP Version 1.0 สำเร็จ โดย direct และ live execution ยังคงถูกล็อก"
                if granted else "บันทึกการออก AFIP Version 1.0 ถูกระงับจากหลักฐานที่ไม่ครบหรือไม่ถูกต้อง"
            ),
        )

    def _final_review_schema(self, row: Mapping[str, Any]) -> bool:
        return (
            str(row.get("milestone", "")).upper() == "R"
            and str(row.get("pack", "")).strip() == "13"
            and str(row.get("status", "")).upper() == "APPROVED"
            and str(row.get("reason", "")).upper() == "VERSION_1_FINAL_REVIEW_APPROVED"
            and bool(row.get("production_certification_granted", False))
            and bool(row.get("release_candidate_granted", False))
            and bool(row.get("version_1_final_granted", False))
            and str(row.get("version", "")) == "1.0"
        )

    def _metadata_valid(self, metadata: Mapping[str, Any]) -> bool:
        if not self._manifest_complete(metadata, self.REQUIRED_METADATA):
            return False
        return (
            str(metadata.get("VERSION")) == "1.0"
            and str(metadata.get("RELEASE_STATUS")).upper() == "FINAL"
            and str(metadata.get("BROKER_POLICY")) == "XM_ONLY"
            and str(metadata.get("SYMBOL_POLICY")) == "GOLD#_ONLY"
            and str(metadata.get("BASE_UNIT_POLICY")) == "1_UNIT_EQUALS_0.01_LOT"
            and str(metadata.get("EXECUTION_POLICY")) == "LOCKED_SIMULATION_ONLY"
        )

    @staticmethod
    def _manifest_complete(manifest: Mapping[str, Any], required: Iterable[str]) -> bool:
        return all(bool(manifest.get(key, False)) for key in required)

    @staticmethod
    def _policy(row: Mapping[str, Any]) -> bool:
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
                "position_modification_attempted", "trading_logic_changed",
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
