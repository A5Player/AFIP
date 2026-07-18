from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Mapping
import json


@dataclass(frozen=True)
class QualityDimensions:
    completeness: float
    consistency: float
    validity: float
    freshness: float
    lineage: float
    documentation: float
    integrity: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class QualityAssessment:
    assessment_id: str
    dataset_id: str
    overall_score: float
    readiness_level: str
    usage_restriction: str
    dimensions: QualityDimensions
    reasons: tuple[str, ...]
    assessed_at: str
    execution_authority: str = "NONE"
    automatic_strategy_change: str = "PROHIBITED"

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["dimensions"] = self.dimensions.to_dict()
        payload["reasons"] = list(self.reasons)
        return payload


class DataQualityScorer:
    """Deterministic research-readiness scorer. It never changes trading behavior."""

    REQUIRED_WEIGHTS = {
        "completeness",
        "consistency",
        "validity",
        "freshness",
        "lineage",
        "documentation",
        "integrity",
    }

    def __init__(self, policy: Mapping[str, object] | None = None) -> None:
        self.policy = dict(policy or {})
        self._validate_policy()

    def _validate_policy(self) -> None:
        if self.policy.get("execution_authority", "NONE") != "NONE":
            raise ValueError("execution_authority_must_be_none")
        if self.policy.get("automatic_strategy_change", "PROHIBITED") != "PROHIBITED":
            raise ValueError("automatic_strategy_change_must_be_prohibited")
        if self.policy.get("automatic_dataset_promotion", "PROHIBITED") != "PROHIBITED":
            raise ValueError("automatic_dataset_promotion_must_be_prohibited")

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(100.0, float(value)))

    def assess(
        self,
        dataset_id: str,
        dimensions: QualityDimensions,
        integrity_status: str = "HEALTHY",
        certification_status: str = "UNCERTIFIED",
        catalog_registered: bool = True,
    ) -> QualityAssessment:
        weights = self.policy.get("weights") or {
            "completeness": 0.20,
            "consistency": 0.15,
            "validity": 0.15,
            "freshness": 0.10,
            "lineage": 0.10,
            "documentation": 0.10,
            "integrity": 0.20,
        }
        missing = self.REQUIRED_WEIGHTS.difference(weights)
        if missing:
            raise ValueError("missing_weights:" + ",".join(sorted(missing)))
        total_weight = sum(float(weights[name]) for name in self.REQUIRED_WEIGHTS)
        if abs(total_weight - 1.0) > 1e-9:
            raise ValueError("weights_must_sum_to_one")

        normalized = QualityDimensions(
            completeness=self._clamp(dimensions.completeness),
            consistency=self._clamp(dimensions.consistency),
            validity=self._clamp(dimensions.validity),
            freshness=self._clamp(dimensions.freshness),
            lineage=self._clamp(dimensions.lineage),
            documentation=self._clamp(dimensions.documentation),
            integrity=self._clamp(dimensions.integrity),
        )

        score = round(sum(
            getattr(normalized, name) * float(weights[name])
            for name in sorted(self.REQUIRED_WEIGHTS)
        ), 2)

        reasons: list[str] = []
        if integrity_status in {"CORRUPTED", "QUARANTINED"}:
            score = min(score, 39.99)
            reasons.append(f"integrity_status_{integrity_status.lower()}")
        if not catalog_registered:
            score = min(score, 59.99)
            reasons.append("dataset_not_registered_in_catalog")
        if certification_status != "CERTIFIED":
            reasons.append("dataset_not_certified")
        for name, value in normalized.to_dict().items():
            if value < 50.0:
                reasons.append(f"low_{name}")

        level, restriction = self._classify(score, integrity_status, certification_status)
        canonical = {
            "dataset_id": dataset_id,
            "score": score,
            "level": level,
            "restriction": restriction,
            "dimensions": normalized.to_dict(),
            "reasons": sorted(reasons),
        }
        assessment_id = "dqa_" + sha256(
            json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:24]

        return QualityAssessment(
            assessment_id=assessment_id,
            dataset_id=dataset_id,
            overall_score=score,
            readiness_level=level,
            usage_restriction=restriction,
            dimensions=normalized,
            reasons=tuple(sorted(reasons)),
            assessed_at=datetime.now(timezone.utc).isoformat(),
        )

    def _classify(self, score: float, integrity_status: str, certification_status: str) -> tuple[str, str]:
        if integrity_status == "QUARANTINED":
            return "NOT_READY", "PROHIBITED"
        if integrity_status == "CORRUPTED":
            return "NOT_READY", "RECOVERY_ONLY"
        if score >= 90.0 and certification_status == "CERTIFIED":
            return "RESEARCH_READY", "APPROVED_RESEARCH_ONLY"
        if score >= 75.0:
            return "CONDITIONALLY_READY", "LIMITED_RESEARCH"
        if score >= 60.0:
            return "REVIEW_REQUIRED", "EXPLORATORY_ONLY"
        return "NOT_READY", "PROHIBITED"

    @staticmethod
    def append_assessment_ledger(assessment: QualityAssessment, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(assessment.to_dict(), sort_keys=True, separators=(",", ":"))
        with target.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line + "\n")
