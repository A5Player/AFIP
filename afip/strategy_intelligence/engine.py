from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence

CONTRACT_VERSION = "AFIP-W3-STRATEGY-1.0"


class StrategyIntelligenceError(ValueError):
    pass


def _text(value: Any) -> str:
    return str(value or "").strip().upper()


def _score(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 4)


EVIDENCE_QUALITY_SCORE = {"ELITE": 100.0, "HIGH": 90.0, "MEDIUM": 70.0, "LOW": 40.0, "UNKNOWN": 0.0}


@dataclass(frozen=True)
class StrategyTemplate:
    strategy_id: str
    strategy_family: str
    supported_pattern_families: tuple[str, ...]
    supported_market_regimes: tuple[str, ...]
    minimum_similarity: float = 80.0
    minimum_sample_size: int = 30
    active: bool = True

    def validate(self) -> None:
        if not self.strategy_id.strip():
            raise StrategyIntelligenceError("strategy_id_required")
        if not self.strategy_family.strip():
            raise StrategyIntelligenceError("strategy_family_required")
        if not self.supported_pattern_families:
            raise StrategyIntelligenceError("supported_pattern_families_required")
        if not self.supported_market_regimes:
            raise StrategyIntelligenceError("supported_market_regimes_required")
        if not 0 <= self.minimum_similarity <= 100:
            raise StrategyIntelligenceError("minimum_similarity_out_of_range")
        if self.minimum_sample_size < 1:
            raise StrategyIntelligenceError("minimum_sample_size_must_be_positive")


@dataclass(frozen=True)
class StrategyEvidence:
    historical_context_id: str
    similarity_score: float
    sample_size: int
    evidence_quality: str
    outcome: str
    historical_expectancy: float = 0.0
    historical_win_rate: float = 0.0
    pattern_family: str = ""
    market_regime: str = ""
    hierarchical_research_required: bool = False
    hierarchical_research_ready: bool = True
    family_research_score: float = 100.0
    exact_shape_research_score: float = 100.0
    shape_similarity_score: float = 100.0

    @classmethod
    def from_match(cls, match: Any) -> "StrategyEvidence":
        if isinstance(match, Mapping):
            get = match.get
        else:
            get = lambda key, default=None: getattr(match, key, default)
        metadata = get("metadata", {}) or {}
        return cls(
            historical_context_id=str(get("historical_context_id", "UNKNOWN")),
            similarity_score=float(get("similarity_score", 0.0)),
            sample_size=int(get("sample_size", 0)),
            evidence_quality=_text(get("evidence_quality", "UNKNOWN")),
            outcome=_text(get("outcome", "UNKNOWN")),
            historical_expectancy=float(metadata.get("historical_expectancy", get("historical_expectancy", 0.0))),
            historical_win_rate=float(metadata.get("historical_win_rate", get("historical_win_rate", 0.0))),
            pattern_family=_text(metadata.get("pattern_family", get("pattern_family", ""))),
            market_regime=_text(metadata.get("market_regime", get("market_regime", ""))),
            hierarchical_research_required=bool(
                metadata.get("hierarchical_research_required", get("hierarchical_research_required", False))
                or metadata.get("research_scope", get("research_scope", "")) == "HIERARCHICAL_FAMILY_AND_EXACT_SHAPE"
            ),
            hierarchical_research_ready=bool(metadata.get("hierarchical_research_ready", get("hierarchical_research_ready", True))),
            family_research_score=float(metadata.get("family_research_score", get("family_research_score", 100.0))),
            exact_shape_research_score=float(metadata.get("exact_shape_research_score", get("exact_shape_research_score", 100.0))),
            shape_similarity_score=float(metadata.get("shape_similarity_score", get("shape_similarity_score", 100.0))),
        )

    def validate(self) -> None:
        if not 0 <= self.similarity_score <= 100:
            raise StrategyIntelligenceError("similarity_score_out_of_range")
        if self.sample_size < 0:
            raise StrategyIntelligenceError("sample_size_negative")
        if not 0 <= self.historical_win_rate <= 100:
            raise StrategyIntelligenceError("historical_win_rate_out_of_range")
        for value in (self.family_research_score, self.exact_shape_research_score, self.shape_similarity_score):
            if not 0 <= value <= 100:
                raise StrategyIntelligenceError("hierarchical_research_score_out_of_range")


@dataclass(frozen=True)
class StrategyCandidate:
    strategy_id: str
    strategy_family: str
    advisory_score: float
    status: str
    evidence_count: int
    total_sample_size: int
    weighted_similarity: float
    weighted_win_rate: float
    weighted_expectancy: float
    evidence_quality_score: float
    reasons: tuple[str, ...]
    weighted_family_research_score: float = 0.0
    weighted_exact_shape_research_score: float = 0.0
    weighted_shape_similarity_score: float = 0.0
    hierarchical_research_applied: bool = False
    authority: str = "ADVISORY_ONLY"
    execution_authority: bool = False
    order_send_allowed: bool = False
    lot_authority: bool = False
    sl_tp_authority: bool = False
    contract_version: str = CONTRACT_VERSION

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class StrategyIntelligenceEngine:
    """Ranks evidence-backed strategy templates. It never creates orders or final trade decisions."""

    def __init__(self, minimum_evidence_count: int = 3, minimum_total_sample_size: int = 100, minimum_hierarchical_research_score: float = 80.0) -> None:
        if minimum_evidence_count < 1 or minimum_total_sample_size < 1:
            raise StrategyIntelligenceError("minimum_evidence_requirements_must_be_positive")
        self.minimum_evidence_count = minimum_evidence_count
        self.minimum_total_sample_size = minimum_total_sample_size
        if not 0 <= minimum_hierarchical_research_score <= 100:
            raise StrategyIntelligenceError("minimum_hierarchical_research_score_out_of_range")
        self.minimum_hierarchical_research_score = float(minimum_hierarchical_research_score)

    def evaluate(self, template: StrategyTemplate, matches: Iterable[Any]) -> StrategyCandidate:
        template.validate()
        if not template.active:
            return self._blocked(template, "strategy_inactive")

        evidence = [StrategyEvidence.from_match(item) for item in matches]
        for item in evidence:
            item.validate()

        supported_patterns = {_text(v) for v in template.supported_pattern_families}
        supported_regimes = {_text(v) for v in template.supported_market_regimes}
        eligible = [
            item for item in evidence
            if item.similarity_score >= template.minimum_similarity
            and item.sample_size >= template.minimum_sample_size
            and (not item.pattern_family or item.pattern_family in supported_patterns)
            and (not item.market_regime or item.market_regime in supported_regimes)
            and (
                not item.hierarchical_research_required
                or (
                    item.hierarchical_research_ready
                    and item.family_research_score >= self.minimum_hierarchical_research_score
                    and item.exact_shape_research_score >= self.minimum_hierarchical_research_score
                    and item.shape_similarity_score >= template.minimum_similarity
                )
            )
        ]
        if len(eligible) < self.minimum_evidence_count:
            return self._blocked(template, "insufficient_evidence_count", len(eligible), sum(i.sample_size for i in eligible))

        total_sample = sum(item.sample_size for item in eligible)
        if total_sample < self.minimum_total_sample_size:
            return self._blocked(template, "insufficient_total_sample_size", len(eligible), total_sample)

        weight_total = sum(max(1, item.sample_size) for item in eligible)
        weighted_similarity = sum(item.similarity_score * max(1, item.sample_size) for item in eligible) / weight_total
        weighted_win_rate = sum(item.historical_win_rate * max(1, item.sample_size) for item in eligible) / weight_total
        weighted_expectancy = sum(item.historical_expectancy * max(1, item.sample_size) for item in eligible) / weight_total
        quality_score = sum(EVIDENCE_QUALITY_SCORE.get(item.evidence_quality, 0.0) * max(1, item.sample_size) for item in eligible) / weight_total
        expectancy_score = _score(50.0 + weighted_expectancy * 10.0)
        hierarchical = any(item.hierarchical_research_required for item in eligible)
        weighted_family = sum(item.family_research_score * max(1, item.sample_size) for item in eligible) / weight_total
        weighted_exact = sum(item.exact_shape_research_score * max(1, item.sample_size) for item in eligible) / weight_total
        weighted_shape = sum(item.shape_similarity_score * max(1, item.sample_size) for item in eligible) / weight_total
        if hierarchical:
            hierarchical_score = weighted_family * 0.30 + weighted_exact * 0.40 + weighted_shape * 0.30
            advisory_score = _score(
                weighted_similarity * 0.20
                + weighted_win_rate * 0.20
                + quality_score * 0.15
                + expectancy_score * 0.15
                + hierarchical_score * 0.30
            )
        else:
            advisory_score = _score(
                weighted_similarity * 0.40
                + weighted_win_rate * 0.25
                + quality_score * 0.20
                + expectancy_score * 0.15
            )
        status = "ELIGIBLE_FOR_PLAN_REVIEW" if advisory_score >= 80.0 else "WAIT"
        reasons = ("evidence_requirements_pass", "advisory_only") if status != "WAIT" else ("advisory_score_below_80", "advisory_only")
        return StrategyCandidate(
            strategy_id=template.strategy_id,
            strategy_family=template.strategy_family,
            advisory_score=advisory_score,
            status=status,
            evidence_count=len(eligible),
            total_sample_size=total_sample,
            weighted_similarity=_score(weighted_similarity),
            weighted_win_rate=_score(weighted_win_rate),
            weighted_expectancy=round(weighted_expectancy, 6),
            evidence_quality_score=_score(quality_score),
            reasons=reasons,
            weighted_family_research_score=_score(weighted_family) if hierarchical else 0.0,
            weighted_exact_shape_research_score=_score(weighted_exact) if hierarchical else 0.0,
            weighted_shape_similarity_score=_score(weighted_shape) if hierarchical else 0.0,
            hierarchical_research_applied=hierarchical,
        )

    def rank(self, templates: Sequence[StrategyTemplate], matches: Iterable[Any]) -> tuple[StrategyCandidate, ...]:
        cached = tuple(matches)
        candidates = [self.evaluate(template, cached) for template in templates]
        candidates.sort(key=lambda item: (item.status == "ELIGIBLE_FOR_PLAN_REVIEW", item.advisory_score, item.total_sample_size), reverse=True)
        return tuple(candidates)

    @staticmethod
    def _blocked(template: StrategyTemplate, reason: str, evidence_count: int = 0, total_sample_size: int = 0) -> StrategyCandidate:
        return StrategyCandidate(
            strategy_id=template.strategy_id,
            strategy_family=template.strategy_family,
            advisory_score=0.0,
            status="WAIT",
            evidence_count=evidence_count,
            total_sample_size=total_sample_size,
            weighted_similarity=0.0,
            weighted_win_rate=0.0,
            weighted_expectancy=0.0,
            evidence_quality_score=0.0,
            reasons=(reason, "fail_closed", "advisory_only"),
        )
