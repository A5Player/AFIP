"""Milestone R Pack 10: deterministic production certification."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ProductionCertificationReport:
    certification_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    certification_timestamp: int
    audit_count: int
    passed_audit_count: int
    blocked_audit_count: int
    accepted_exception_count: int
    critical_block_count: int
    required_audits_present: bool
    audit_ids_unique: bool
    chronology_valid: bool
    audit_schema_valid: bool
    all_audits_passed: bool
    locked_policy_valid: bool
    certification_score: float
    production_certification_granted: bool
    release_candidate_granted: bool
    version_1_final_granted: bool
    next_stage: str
    review_required: bool
    immutable_record: bool
    block_reasons: tuple[str, ...]
    audit_ids: tuple[str, ...]
    blocked_audit_ids: tuple[str, ...]
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


class ProductionCertificationRuntime:
    REQUIRED_PACKS = frozenset(str(n) for n in range(1, 10))
    REQUIRED_REASON_PREFIX = {
        "1": "REGRESSION",
        "2": "DUPLICATE",
        "3": "DEAD_CODE",
        "4": "ARCHITECTURE",
        "5": "REPOSITORY_CLEANUP",
        "6": "SAFETY",
        "7": "SECURITY",
        "8": "DATA_INTEGRITY",
        "9": "PERFORMANCE",
    }

    def certify(
        self,
        audit_reports: Iterable[Mapping[str, Any]],
        *,
        certification_timestamp: int,
        minimum_certification_score: float = 1.0,
    ) -> ProductionCertificationReport:
        rows = tuple(dict(item) for item in audit_reports)
        ts = self._int(certification_timestamp)
        ids = tuple(str(row.get("audit_id", "")).strip().upper() for row in rows)
        packs = tuple(str(row.get("pack", "")).strip() for row in rows)

        required_present = self.REQUIRED_PACKS == set(packs)
        unique = bool(ids) and len(ids) == len(set(ids)) and all(self._valid_audit_id(i) for i in ids)
        chronology = all(0 < self._int(row.get("audit_timestamp", 0)) <= ts for row in rows)
        schema = all(self._schema(row) for row in rows)
        passed = tuple(row for row in rows if self._passed(row))
        blocked = tuple(row for row in rows if not self._passed(row))
        accepted_exceptions = sum(self._int(row.get("accepted_exception_count", 0)) for row in rows)
        critical_blocks = sum(self._int(row.get("critical_failure_count", row.get("critical_finding_count", 0))) for row in rows)
        policy = all(self._policy(row) for row in rows)
        all_passed = len(passed) == len(rows) and len(rows) == len(self.REQUIRED_PACKS)
        score = round(len(passed) / max(len(self.REQUIRED_PACKS), 1), 6)
        threshold = self._score(minimum_certification_score)

        checks = (
            (not required_present, "required_production_audit_missing"),
            (not unique, "duplicate_or_invalid_production_audit_id"),
            (not chronology, "production_certification_chronology_invalid"),
            (not schema, "production_audit_schema_invalid"),
            (not all_passed, "production_audit_not_passed"),
            (critical_blocks > 0, "critical_production_audit_block_present"),
            (score < threshold, "production_certification_score_below_threshold"),
            (not policy, "feature_freeze_or_execution_policy_violation"),
        )
        block_reasons = tuple(sorted({reason for condition, reason in checks if condition}))
        granted = not block_reasons

        identity = {
            "audit_ids": ids,
            "packs": packs,
            "certification_timestamp": ts,
            "score": score,
            "blocked": block_reasons,
        }
        certification_id = "RCERT-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        return ProductionCertificationReport(
            certification_id=certification_id,
            status="CERTIFIED" if granted else "BLOCKED",
            reason="PRODUCTION_CERTIFICATION_GRANTED" if granted else "PRODUCTION_CERTIFICATION_BLOCKED",
            milestone="R",
            pack="10",
            certification_timestamp=ts,
            audit_count=len(rows),
            passed_audit_count=len(passed),
            blocked_audit_count=len(blocked),
            accepted_exception_count=accepted_exceptions,
            critical_block_count=critical_blocks,
            required_audits_present=required_present,
            audit_ids_unique=unique,
            chronology_valid=chronology,
            audit_schema_valid=schema,
            all_audits_passed=all_passed,
            locked_policy_valid=policy,
            certification_score=score,
            production_certification_granted=granted,
            release_candidate_granted=False,
            version_1_final_granted=False,
            next_stage="R_RELEASE_CANDIDATE" if granted else "R_CERTIFICATION_REVIEW_REQUIRED",
            review_required=not granted,
            immutable_record=True,
            block_reasons=block_reasons,
            audit_ids=ids,
            blocked_audit_ids=tuple(str(row.get("audit_id", "")).upper() for row in blocked),
            explanation_reason_en=(
                "All required production audits passed deterministic certification. Execution remains locked pending Release Candidate and Version 1.0 Final approval."
                if granted
                else "Production Certification was blocked by missing, invalid, failed, critical, chronological, score, or frozen-policy evidence."
            ),
            explanation_reason_th=(
                "การตรวจสอบสำหรับ production ที่กำหนดผ่านการรับรองแบบ deterministic ครบถ้วน แต่ execution ยังคงถูกล็อกจนกว่าจะผ่าน Release Candidate และ Version 1.0 Final"
                if granted
                else "Production Certification ถูกระงับจากหลักฐานที่ขาด ไม่ถูกต้อง ไม่ผ่าน มีระดับวิกฤต ลำดับเวลา คะแนน หรือนโยบายล็อก"
            ),
        )

    def _schema(self, row: Mapping[str, Any]) -> bool:
        pack = str(row.get("pack", "")).strip()
        expected = self.REQUIRED_REASON_PREFIX.get(pack)
        reason = str(row.get("reason", "")).upper()
        return (
            str(row.get("milestone", "")).upper() == "R"
            and pack in self.REQUIRED_PACKS
            and str(row.get("status", "")).upper() == "PASS"
            and bool(expected)
            and expected in reason
            and bool(row.get(self._pass_field(pack), False))
        )

    def _passed(self, row: Mapping[str, Any]) -> bool:
        pack = str(row.get("pack", "")).strip()
        return str(row.get("status", "")).upper() == "PASS" and bool(row.get(self._pass_field(pack), False))

    def _pass_field(self, pack: str) -> str:
        return {
            "1": "regression_audit_passed",
            "2": "duplicate_code_audit_passed",
            "3": "dead_code_audit_passed",
            "4": "architecture_audit_passed",
            "5": "repository_cleanup_passed",
            "6": "safety_audit_passed",
            "7": "security_audit_passed",
            "8": "data_integrity_audit_passed",
            "9": "performance_audit_passed",
        }.get(pack, "")

    def _valid_audit_id(self, value: str) -> bool:
        return value.startswith("R") and len(value) >= 10

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
