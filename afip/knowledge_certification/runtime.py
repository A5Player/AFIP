"""Deterministic, research-only knowledge certification framework.

This module has no broker, order, position, lot, MT5, or execution authority.
It turns validated research evidence into auditable certification records only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

ALLOWED_LEVELS = (
    "CANDIDATE",
    "VALIDATED",
    "RESEARCH_REVIEW_READY",
    "RESEARCH_CERTIFIED",
    "PRODUCTION_CANDIDATE",
)
LIFECYCLE_STATES = (
    "CREATED",
    "VALIDATED",
    "CERTIFIED",
    "ACTIVE_RESEARCH",
    "SUSPENDED",
    "DEPRECATED",
    "ARCHIVED",
)


@dataclass(frozen=True)
class CertificationPolicy:
    schema_version: str
    execution_authority: str
    promotion_to_execution: str
    automatic_strategy_change: str
    human_review_required: bool
    minimum_evidence_count: int
    minimum_independent_periods: int
    minimum_regime_coverage: int
    minimum_sample_size: int
    minimum_validation_score: float
    minimum_stability_score: float
    maximum_drift_score: float

    def validate(self) -> None:
        if self.execution_authority != "NONE":
            raise ValueError("execution_authority_must_be_none")
        if self.promotion_to_execution != "PROHIBITED":
            raise ValueError("promotion_to_execution_must_be_prohibited")
        if self.automatic_strategy_change != "PROHIBITED":
            raise ValueError("automatic_strategy_change_must_be_prohibited")
        if not self.human_review_required:
            raise ValueError("human_review_is_required")
        if min(
            self.minimum_evidence_count,
            self.minimum_independent_periods,
            self.minimum_regime_coverage,
            self.minimum_sample_size,
        ) < 1:
            raise ValueError("minimum_thresholds_must_be_positive")
        for value in (
            self.minimum_validation_score,
            self.minimum_stability_score,
            self.maximum_drift_score,
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError("ratio_threshold_out_of_range")


def load_policy(path: str | Path) -> CertificationPolicy:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    policy = CertificationPolicy(**payload)
    policy.validate()
    return policy


def _canonical(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    return f"{prefix}_{sha256(_canonical(payload).encode('utf-8')).hexdigest()[:24]}"


def append_jsonl(path: str | Path, record: Mapping[str, Any]) -> None:
    """Append one immutable record to a JSONL ledger."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(_canonical(record) + "\n")


class KnowledgeCertificationFramework:
    """Builds auditable research certification decisions without execution rights."""

    def __init__(self, policy: CertificationPolicy):
        policy.validate()
        self.policy = policy

    def certify(
        self,
        *,
        knowledge_id: str,
        knowledge_version: str,
        evidence: Iterable[Mapping[str, Any]],
        reviewer: str,
        parent_certification_id: str | None = None,
        evaluated_at: str | None = None,
    ) -> dict[str, Any]:
        rows = self._deduplicate(evidence)
        if not knowledge_id or not knowledge_version or not reviewer:
            raise ValueError("knowledge_identity_and_reviewer_are_required")

        sample_size = sum(max(0, int(row.get("sample_size", 0))) for row in rows)
        periods = sorted({str(row.get("period_id", "")) for row in rows if row.get("period_id")})
        regimes = sorted({str(row.get("market_regime", "")) for row in rows if row.get("market_regime")})
        validation_scores = [float(row.get("validation_score", 0.0)) for row in rows]
        stability_scores = [float(row.get("stability_score", 0.0)) for row in rows]
        drift_scores = [float(row.get("drift_score", 1.0)) for row in rows]
        statuses = {str(row.get("status", "")) for row in rows}

        avg_validation = sum(validation_scores) / len(validation_scores) if validation_scores else 0.0
        avg_stability = sum(stability_scores) / len(stability_scores) if stability_scores else 0.0
        max_drift = max(drift_scores) if drift_scores else 1.0

        reasons: list[str] = []
        level = "CANDIDATE"
        lifecycle = "CREATED"

        if "REJECTED" in statuses:
            reasons.append("rejected_evidence_present")
        if len(rows) < self.policy.minimum_evidence_count:
            reasons.append("insufficient_evidence_count")
        if len(periods) < self.policy.minimum_independent_periods:
            reasons.append("insufficient_independent_periods")
        if len(regimes) < self.policy.minimum_regime_coverage:
            reasons.append("insufficient_regime_coverage")
        if sample_size < self.policy.minimum_sample_size:
            reasons.append("insufficient_sample_size")
        if avg_validation < self.policy.minimum_validation_score:
            reasons.append("validation_score_below_threshold")
        if avg_stability < self.policy.minimum_stability_score:
            reasons.append("stability_score_below_threshold")
        if max_drift > self.policy.maximum_drift_score:
            reasons.append("drift_above_threshold")

        hard_reject = "rejected_evidence_present" in reasons
        if hard_reject:
            decision = "REJECTED"
            lifecycle = "ARCHIVED"
        elif reasons:
            decision = "CERTIFICATION_PENDING"
        else:
            decision = "RESEARCH_CERTIFIED"
            level = "RESEARCH_CERTIFIED"
            lifecycle = "CERTIFIED"
            reasons.append("all_research_certification_thresholds_passed")

        evaluated_at = evaluated_at or datetime.now(timezone.utc).isoformat()
        identity = {
            "knowledge_id": knowledge_id,
            "knowledge_version": knowledge_version,
            "evidence_ids": [row["evidence_id"] for row in rows],
            "policy": asdict(self.policy),
            "decision": decision,
            "parent_certification_id": parent_certification_id,
        }
        certification_id = _stable_id("kcert", identity)
        return {
            "schema_name": "afip.knowledge.certification",
            "schema_version": self.policy.schema_version,
            "certification_id": certification_id,
            "knowledge_id": knowledge_id,
            "knowledge_version": knowledge_version,
            "parent_certification_id": parent_certification_id,
            "certification_level": level,
            "decision": decision,
            "lifecycle_state": lifecycle,
            "reviewer": reviewer,
            "evaluated_at": evaluated_at,
            "evidence_count": len(rows),
            "evidence_ids": [row["evidence_id"] for row in rows],
            "independent_periods": periods,
            "market_regimes": regimes,
            "sample_size": sample_size,
            "average_validation_score": round(avg_validation, 8),
            "average_stability_score": round(avg_stability, 8),
            "maximum_drift_score": round(max_drift, 8),
            "reasons": reasons,
            "execution_authority": "NONE",
            "promotion_to_execution": "PROHIBITED",
            "automatic_strategy_change": "PROHIBITED",
            "human_review_required": True,
            "data_root": "data/knowledge/certification",
        }

    @staticmethod
    def lineage_record(certification: Mapping[str, Any]) -> dict[str, Any]:
        payload = {
            "schema_name": "afip.knowledge.lineage",
            "schema_version": certification["schema_version"],
            "certification_id": certification["certification_id"],
            "knowledge_id": certification["knowledge_id"],
            "knowledge_version": certification["knowledge_version"],
            "parent_certification_id": certification.get("parent_certification_id"),
            "decision": certification["decision"],
            "lifecycle_state": certification["lifecycle_state"],
        }
        return {"lineage_id": _stable_id("kline", payload), **payload}

    @staticmethod
    def _deduplicate(evidence: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
        unique: dict[str, dict[str, Any]] = {}
        for source in evidence:
            row = dict(source)
            evidence_id = str(row.get("evidence_id", "")).strip()
            if not evidence_id:
                evidence_id = _stable_id("kevd", row)
            row["evidence_id"] = evidence_id
            unique[evidence_id] = row
        return [unique[key] for key in sorted(unique)]
