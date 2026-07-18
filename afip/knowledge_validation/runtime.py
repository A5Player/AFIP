"""Conservative validation pipeline for AFIP candidate knowledge.

This module validates research knowledge across independent periods and market
regimes. It can promote knowledge only inside the research lifecycle. It has no
broker, order, position-sizing, profile, or live-execution authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable, Mapping, Sequence


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def deterministic_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ValidationEvidence:
    evidence_id: str
    candidate_id: str
    hypothesis_key: str
    validation_period: str
    market_regime: str
    sample_count: int
    expectancy_points: float
    confidence_interval_95_low: float
    stability_score: float
    knowledge_confidence_score: float
    source_report_id: str
    source_lifecycle_status: str

    def validate(self) -> None:
        if not all((self.evidence_id, self.candidate_id, self.hypothesis_key,
                    self.validation_period, self.market_regime, self.source_report_id)):
            raise ValueError("validation evidence identity is required")
        if self.sample_count < 0:
            raise ValueError("sample_count cannot be negative")
        if not 0 <= self.stability_score <= 100:
            raise ValueError("stability_score must be between 0 and 100")
        if not 0 <= self.knowledge_confidence_score <= 100:
            raise ValueError("knowledge_confidence_score must be between 0 and 100")


@dataclass(frozen=True)
class PromotionDecision:
    schema_version: str
    decision_id: str
    candidate_id: str
    hypothesis_key: str
    validation_status: str
    research_promotion_status: str
    evidence_count: int
    independent_period_count: int
    market_regime_count: int
    total_samples: int
    positive_expectancy_ratio: float
    positive_confidence_interval_ratio: float
    average_stability_score: float
    average_knowledge_confidence_score: float
    validation_score: float
    reasons: tuple[str, ...]
    source_evidence_ids: tuple[str, ...]
    execution_authority: str
    promotion_to_execution: str
    human_approval_required: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationReport:
    schema_version: str
    report_id: str
    evidence_count: int
    decisions: tuple[PromotionDecision, ...]
    execution_authority: str
    promotion_to_execution: str
    automatic_trading_policy_change: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class KnowledgeValidationEngine:
    """Validate candidate knowledge without granting trading authority."""

    def __init__(
        self,
        minimum_independent_periods: int = 3,
        minimum_market_regimes: int = 2,
        minimum_total_samples: int = 200,
        minimum_positive_expectancy_ratio: float = 0.75,
        minimum_positive_ci_ratio: float = 0.67,
        minimum_average_stability: float = 70.0,
        minimum_validation_score: float = 75.0,
    ) -> None:
        if minimum_independent_periods <= 0 or minimum_market_regimes <= 0 or minimum_total_samples <= 0:
            raise ValueError("minimum validation requirements must be positive")
        for value in (minimum_positive_expectancy_ratio, minimum_positive_ci_ratio):
            if not 0 <= value <= 1:
                raise ValueError("ratio thresholds must be between 0 and 1")
        for value in (minimum_average_stability, minimum_validation_score):
            if not 0 <= value <= 100:
                raise ValueError("score thresholds must be between 0 and 100")
        self.minimum_independent_periods = minimum_independent_periods
        self.minimum_market_regimes = minimum_market_regimes
        self.minimum_total_samples = minimum_total_samples
        self.minimum_positive_expectancy_ratio = minimum_positive_expectancy_ratio
        self.minimum_positive_ci_ratio = minimum_positive_ci_ratio
        self.minimum_average_stability = minimum_average_stability
        self.minimum_validation_score = minimum_validation_score

    def validate(self, evidence: Sequence[ValidationEvidence]) -> ValidationReport:
        unique: dict[str, ValidationEvidence] = {}
        for item in evidence:
            item.validate()
            unique.setdefault(deterministic_hash(asdict(item)), item)
        groups: dict[str, list[ValidationEvidence]] = {}
        for item in unique.values():
            groups.setdefault(item.candidate_id, []).append(item)
        decisions = tuple(sorted(
            (self._decision(candidate_id, members) for candidate_id, members in groups.items()),
            key=lambda x: (-x.validation_score, x.hypothesis_key, x.candidate_id),
        ))
        stable = {
            "evidence": [asdict(x) for x in sorted(unique.values(), key=lambda x: (x.candidate_id, x.validation_period, x.market_regime, x.evidence_id))],
            "decisions": [x.to_dict() for x in decisions],
            "execution_authority": "NONE",
            "promotion_to_execution": "PROHIBITED",
            "automatic_trading_policy_change": "PROHIBITED",
        }
        return ValidationReport(
            "knowledge-validation-report.v1",
            deterministic_hash(stable),
            len(unique),
            decisions,
            "NONE",
            "PROHIBITED",
            "PROHIBITED",
        )

    def _decision(self, candidate_id: str, members: Sequence[ValidationEvidence]) -> PromotionDecision:
        ordered = sorted(members, key=lambda x: (x.validation_period, x.market_regime, x.evidence_id))
        hypothesis_keys = {x.hypothesis_key for x in ordered}
        if len(hypothesis_keys) != 1:
            raise ValueError("candidate evidence must share one hypothesis_key")
        periods = {x.validation_period for x in ordered}
        regimes = {x.market_regime for x in ordered}
        total_samples = sum(x.sample_count for x in ordered)
        positive_expectancy_ratio = sum(x.expectancy_points > 0 for x in ordered) / len(ordered)
        positive_ci_ratio = sum(x.confidence_interval_95_low > 0 for x in ordered) / len(ordered)
        avg_stability = fmean(x.stability_score for x in ordered)
        avg_confidence = fmean(x.knowledge_confidence_score for x in ordered)
        period_score = min(100.0, len(periods) / self.minimum_independent_periods * 100.0)
        regime_score = min(100.0, len(regimes) / self.minimum_market_regimes * 100.0)
        sample_score = min(100.0, total_samples / self.minimum_total_samples * 100.0)
        validation_score = max(0.0, min(100.0,
            0.15 * period_score + 0.10 * regime_score + 0.15 * sample_score +
            0.20 * positive_expectancy_ratio * 100.0 +
            0.20 * positive_ci_ratio * 100.0 +
            0.10 * avg_stability + 0.10 * avg_confidence
        ))
        reasons: list[str] = []
        if len(periods) < self.minimum_independent_periods:
            reasons.append("MINIMUM_INDEPENDENT_PERIODS_NOT_MET")
        if len(regimes) < self.minimum_market_regimes:
            reasons.append("MINIMUM_MARKET_REGIMES_NOT_MET")
        if total_samples < self.minimum_total_samples:
            reasons.append("MINIMUM_TOTAL_SAMPLES_NOT_MET")
        if positive_expectancy_ratio < self.minimum_positive_expectancy_ratio:
            reasons.append("POSITIVE_EXPECTANCY_RATIO_BELOW_THRESHOLD")
        if positive_ci_ratio < self.minimum_positive_ci_ratio:
            reasons.append("POSITIVE_CONFIDENCE_INTERVAL_RATIO_BELOW_THRESHOLD")
        if avg_stability < self.minimum_average_stability:
            reasons.append("AVERAGE_STABILITY_BELOW_THRESHOLD")
        if validation_score < self.minimum_validation_score:
            reasons.append("VALIDATION_SCORE_BELOW_THRESHOLD")
        if any(x.source_lifecycle_status == "REJECTED" for x in ordered):
            reasons.append("REJECTED_SOURCE_EVIDENCE_PRESENT")
        if "REJECTED_SOURCE_EVIDENCE_PRESENT" in reasons or positive_ci_ratio == 0:
            validation_status = "REJECTED"
            promotion_status = "NOT_PROMOTED"
        elif reasons:
            validation_status = "VALIDATION_PENDING"
            promotion_status = "NOT_PROMOTED"
        else:
            validation_status = "VALIDATED_FOR_RESEARCH_REVIEW"
            promotion_status = "RESEARCH_REVIEW_READY"
        stable = {
            "candidate_id": candidate_id,
            "hypothesis_key": ordered[0].hypothesis_key,
            "source_evidence_ids": [x.evidence_id for x in ordered],
        }
        return PromotionDecision(
            "knowledge-promotion-decision.v1",
            deterministic_hash(stable),
            candidate_id,
            ordered[0].hypothesis_key,
            validation_status,
            promotion_status,
            len(ordered),
            len(periods),
            len(regimes),
            total_samples,
            round(positive_expectancy_ratio, 8),
            round(positive_ci_ratio, 8),
            round(avg_stability, 8),
            round(avg_confidence, 8),
            round(validation_score, 8),
            tuple(reasons),
            tuple(x.evidence_id for x in ordered),
            "NONE",
            "PROHIBITED",
            True,
        )


def evidence_from_evolution_report(
    report: Mapping[str, Any], validation_period: str, market_regime: str
) -> tuple[ValidationEvidence, ...]:
    if str(report.get("execution_authority")) != "NONE":
        raise ValueError("knowledge report must have execution_authority NONE")
    if str(report.get("promotion_to_execution")) != "PROHIBITED":
        raise ValueError("knowledge report must prohibit execution promotion")
    report_id = str(report["report_id"])
    output: list[ValidationEvidence] = []
    for row in report.get("candidates", ()):
        stable = {
            "source_report_id": report_id,
            "candidate_id": row["candidate_id"],
            "validation_period": validation_period,
            "market_regime": market_regime,
        }
        output.append(ValidationEvidence(
            deterministic_hash(stable), str(row["candidate_id"]), str(row["hypothesis_key"]),
            validation_period, market_regime, int(row["total_samples"]),
            float(row["weighted_expectancy_points"]), float(row["latest_confidence_interval_low"]),
            float(row["latest_stability_score"]), float(row["knowledge_confidence_score"]),
            report_id, str(row["lifecycle_status"]),
        ))
    return tuple(output)


def load_evidence_from_json(paths: Iterable[str | Path], market_regime: str = "UNKNOWN") -> tuple[ValidationEvidence, ...]:
    output: list[ValidationEvidence] = []
    for path in sorted(Path(x) for x in paths):
        value = json.loads(path.read_text(encoding="utf-8"))
        period = str(value.get("generated_at_utc", path.stem))
        output.extend(evidence_from_evolution_report(value, period, market_regime))
    return tuple(output)


def write_validation_report(report: ValidationReport, path: str | Path) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json(report.to_dict()) + "\n"
    target.write_text(payload, encoding="utf-8", newline="\n")
    return sha256(payload.encode("utf-8")).hexdigest()
