"""Milestone T Pack 5: exit experiment aggregation and evidence evaluation.

This module aggregates EXPERIMENTAL position outcomes by market context. It is
strictly research-only: it does not select a production policy, promote any
result, or call MT5. All generated records remain quarantined and append-only.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from statistics import median, pstdev
from typing import Any, Iterable, Mapping

from afip.historical_replay_research import AppendOnlyResearchDataset


def _checksum(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


def _bounded(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def _normalized_label(value: str, fallback: str = "UNCLASSIFIED") -> str:
    normalized = str(value).strip().upper().replace(" ", "_")
    return normalized or fallback


@dataclass(frozen=True, order=True)
class ContextSegment:
    market_regime: str
    market_structure: str
    liquidity_state: str
    trend_state: str
    volatility_state: str
    trading_session: str
    direction: str
    pattern_family: str

    def __post_init__(self) -> None:
        if self.direction not in {"BUY", "SELL"}:
            raise ValueError("direction must be BUY or SELL")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ContextSegment":
        return cls(
            market_regime=_normalized_label(value.get("market_regime", "UNCLASSIFIED")),
            market_structure=_normalized_label(value.get("market_structure", "UNCLASSIFIED")),
            liquidity_state=_normalized_label(value.get("liquidity_state", "UNCLASSIFIED")),
            trend_state=_normalized_label(value.get("trend_state", "UNCLASSIFIED")),
            volatility_state=_normalized_label(value.get("volatility_state", "UNCLASSIFIED")),
            trading_session=_normalized_label(value.get("trading_session", "UNCLASSIFIED")),
            direction=_normalized_label(value.get("direction", ""), ""),
            pattern_family=_normalized_label(value.get("pattern_family", "UNCLASSIFIED")),
        )

    @property
    def segment_id(self) -> str:
        return "|".join(asdict(self).values())

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["segment_id"] = self.segment_id
        return payload


@dataclass(frozen=True)
class EvidenceObservation:
    observation_id: str
    position_case_id: str
    policy_id: str
    realized_r: float
    exit_quality_score: float
    capital_preservation_score: float
    profit_capture_ratio: float
    maximum_adverse_excursion_r: float
    bars_held: int
    segment: ContextSegment
    research_state: str = "EXPERIMENTAL"
    production_usable: bool = False

    def __post_init__(self) -> None:
        if not self.observation_id.strip() or not self.position_case_id.strip() or not self.policy_id.strip():
            raise ValueError("observation, position case, and policy identifiers are required")
        if not 0 <= self.exit_quality_score <= 100:
            raise ValueError("exit_quality_score must be between 0 and 100")
        if not 0 <= self.capital_preservation_score <= 100:
            raise ValueError("capital_preservation_score must be between 0 and 100")
        if not 0 <= self.profit_capture_ratio <= 1:
            raise ValueError("profit_capture_ratio must be between 0 and 1")
        if self.maximum_adverse_excursion_r < 0 or self.bars_held <= 0:
            raise ValueError("adverse excursion and bars held are invalid")
        if self.research_state != "EXPERIMENTAL" or self.production_usable:
            raise ValueError("evidence observations must remain experimental and quarantined")

    @classmethod
    def from_mappings(
        cls,
        *,
        observation_id: str,
        outcome: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> "EvidenceObservation":
        return cls(
            observation_id=observation_id,
            position_case_id=str(outcome["position_case_id"]),
            policy_id=str(outcome["policy_id"]),
            realized_r=float(outcome["realized_r"]),
            exit_quality_score=float(outcome["exit_quality_score"]),
            capital_preservation_score=float(outcome["capital_preservation_score"]),
            profit_capture_ratio=float(outcome["profit_capture_ratio"]),
            maximum_adverse_excursion_r=float(outcome["maximum_adverse_excursion_r"]),
            bars_held=int(outcome["bars_held"]),
            segment=ContextSegment.from_mapping(context),
        )

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["segment"] = self.segment.as_dict()
        return payload


@dataclass(frozen=True)
class SegmentEvidenceSummary:
    policy_id: str
    segment_id: str
    sample_size: int
    profitable_count: int
    loss_count: int
    break_even_count: int
    win_rate: float
    average_realized_r: float
    median_realized_r: float
    worst_realized_r: float
    best_realized_r: float
    realized_r_dispersion: float
    average_exit_quality_score: float
    average_capital_preservation_score: float
    average_profit_capture_ratio: float
    average_maximum_adverse_excursion_r: float
    average_bars_held: float
    positive_expectancy: bool
    consistency_score: float
    evidence_score: float
    research_state: str
    production_usable: bool
    summary_checksum: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceEvaluation:
    policy_id: str
    segment_id: str
    sample_size: int
    minimum_sample_size: int
    evidence_score: float
    evidence_level: str
    evidence_eligible: bool
    eligibility_reasons: tuple[str, ...]
    quarantine_status: str
    automatic_promotion_allowed: bool
    research_state: str
    production_usable: bool
    evaluation_checksum: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PolicyComparison:
    segment_id: str
    policy_a: str
    policy_b: str
    shared_sample_size: int
    average_realized_r_difference: float
    exit_quality_difference: float
    capital_preservation_difference: float
    evidence_score_difference: float
    comparison_status: str
    selected_policy_id: None
    research_state: str
    production_usable: bool
    comparison_checksum: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExitEvidenceResearchEngine:
    """Aggregate observations into auditable, quarantined evidence records."""

    def __init__(self, dataset: AppendOnlyResearchDataset, *, minimum_sample_size: int = 30) -> None:
        if minimum_sample_size <= 0:
            raise ValueError("minimum_sample_size must be positive")
        self.dataset = dataset
        self.minimum_sample_size = minimum_sample_size

    def record_observations(self, observations: Iterable[EvidenceObservation]) -> tuple[EvidenceObservation, ...]:
        values = tuple(observations)
        identifiers = [value.observation_id for value in values]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("observation identifiers must be unique")
        for value in values:
            self.dataset.append("exit_evidence_observations", value.as_dict())
        return values

    @staticmethod
    def _group(observations: Iterable[EvidenceObservation]) -> dict[tuple[str, str], list[EvidenceObservation]]:
        grouped: dict[tuple[str, str], list[EvidenceObservation]] = {}
        for item in observations:
            grouped.setdefault((item.policy_id, item.segment.segment_id), []).append(item)
        return grouped

    @staticmethod
    def _summarize(policy_id: str, segment_id: str, values: list[EvidenceObservation]) -> SegmentEvidenceSummary:
        realized = [item.realized_r for item in values]
        sample_size = len(values)
        profitable_count = sum(value > 0 for value in realized)
        loss_count = sum(value < 0 for value in realized)
        break_even_count = sample_size - profitable_count - loss_count
        average_realized = sum(realized) / sample_size
        dispersion = pstdev(realized) if sample_size > 1 else 0.0
        average_exit_quality = sum(item.exit_quality_score for item in values) / sample_size
        average_preservation = sum(item.capital_preservation_score for item in values) / sample_size
        average_capture = sum(item.profit_capture_ratio for item in values) / sample_size
        average_adverse = sum(item.maximum_adverse_excursion_r for item in values) / sample_size
        average_bars = sum(item.bars_held for item in values) / sample_size
        consistency = _bounded(100.0 - (dispersion * 25.0) - (max(0.0, -min(realized)) * 10.0))
        expectancy_component = _bounded(50.0 + average_realized * 20.0)
        evidence_score = _bounded(
            (average_exit_quality * 0.25)
            + (average_preservation * 0.25)
            + (consistency * 0.20)
            + (expectancy_component * 0.20)
            + (min(sample_size, 100) * 0.10)
        )
        base = {
            "policy_id": policy_id,
            "segment_id": segment_id,
            "sample_size": sample_size,
            "profitable_count": profitable_count,
            "loss_count": loss_count,
            "break_even_count": break_even_count,
            "win_rate": profitable_count / sample_size,
            "average_realized_r": average_realized,
            "median_realized_r": median(realized),
            "worst_realized_r": min(realized),
            "best_realized_r": max(realized),
            "realized_r_dispersion": dispersion,
            "average_exit_quality_score": average_exit_quality,
            "average_capital_preservation_score": average_preservation,
            "average_profit_capture_ratio": average_capture,
            "average_maximum_adverse_excursion_r": average_adverse,
            "average_bars_held": average_bars,
            "positive_expectancy": average_realized > 0,
            "consistency_score": consistency,
            "evidence_score": evidence_score,
            "research_state": "EXPERIMENTAL",
            "production_usable": False,
        }
        return SegmentEvidenceSummary(summary_checksum=_checksum(base), **base)

    def _evaluate(self, summary: SegmentEvidenceSummary) -> EvidenceEvaluation:
        reasons: list[str] = []
        if summary.sample_size < self.minimum_sample_size:
            reasons.append("minimum_sample_size_not_met")
        if not summary.positive_expectancy:
            reasons.append("positive_expectancy_not_demonstrated")
        if summary.consistency_score < 60:
            reasons.append("consistency_below_research_threshold")
        if summary.evidence_score < 65:
            reasons.append("evidence_score_below_research_threshold")
        eligible = not reasons
        if summary.evidence_score >= 80 and summary.sample_size >= self.minimum_sample_size * 3:
            level = "STRONG_RESEARCH_EVIDENCE"
        elif summary.evidence_score >= 65 and summary.sample_size >= self.minimum_sample_size:
            level = "MODERATE_RESEARCH_EVIDENCE"
        else:
            level = "INSUFFICIENT_RESEARCH_EVIDENCE"
        base = {
            "policy_id": summary.policy_id,
            "segment_id": summary.segment_id,
            "sample_size": summary.sample_size,
            "minimum_sample_size": self.minimum_sample_size,
            "evidence_score": summary.evidence_score,
            "evidence_level": level,
            "evidence_eligible": eligible,
            "eligibility_reasons": tuple(reasons or ("research_evidence_thresholds_met",)),
            "quarantine_status": "RESEARCH_QUARANTINE",
            "automatic_promotion_allowed": False,
            "research_state": "EXPERIMENTAL",
            "production_usable": False,
        }
        return EvidenceEvaluation(evaluation_checksum=_checksum(base), **base)

    def aggregate(self, observations: Iterable[EvidenceObservation]) -> tuple[SegmentEvidenceSummary, ...]:
        values = self.record_observations(observations)
        if not values:
            raise ValueError("at least one evidence observation is required")
        summaries: list[SegmentEvidenceSummary] = []
        for (policy_id, segment_id), group in sorted(self._group(values).items()):
            summary = self._summarize(policy_id, segment_id, group)
            evaluation = self._evaluate(summary)
            self.dataset.append("exit_context_segments", {
                "policy_id": policy_id,
                "segment_id": segment_id,
                "context": group[0].segment.as_dict(),
                "sample_size": len(group),
                "research_state": "EXPERIMENTAL",
                "production_usable": False,
            })
            self.dataset.append("exit_evidence_summaries", summary.as_dict())
            self.dataset.append("exit_evidence_evaluations", evaluation.as_dict())
            summaries.append(summary)
        return tuple(summaries)

    def compare(self, summaries: Iterable[SegmentEvidenceSummary]) -> tuple[PolicyComparison, ...]:
        by_segment: dict[str, list[SegmentEvidenceSummary]] = {}
        for item in summaries:
            by_segment.setdefault(item.segment_id, []).append(item)
        comparisons: list[PolicyComparison] = []
        for segment_id, values in sorted(by_segment.items()):
            ordered = sorted(values, key=lambda item: item.policy_id)
            for index, left in enumerate(ordered):
                for right in ordered[index + 1:]:
                    base = {
                        "segment_id": segment_id,
                        "policy_a": left.policy_id,
                        "policy_b": right.policy_id,
                        "shared_sample_size": min(left.sample_size, right.sample_size),
                        "average_realized_r_difference": left.average_realized_r - right.average_realized_r,
                        "exit_quality_difference": left.average_exit_quality_score - right.average_exit_quality_score,
                        "capital_preservation_difference": left.average_capital_preservation_score - right.average_capital_preservation_score,
                        "evidence_score_difference": left.evidence_score - right.evidence_score,
                        "comparison_status": "RESEARCH_ONLY_NO_SELECTION",
                        "selected_policy_id": None,
                        "research_state": "EXPERIMENTAL",
                        "production_usable": False,
                    }
                    comparison = PolicyComparison(comparison_checksum=_checksum(base), **base)
                    self.dataset.append("exit_policy_comparisons", comparison.as_dict())
                    comparisons.append(comparison)
        return tuple(comparisons)
