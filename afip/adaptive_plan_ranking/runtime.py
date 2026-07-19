"""Milestone T Pack 10: adaptive multi-objective plan ranking.

The ranking engine protects capital first, requires sufficient evidence, selects
for the current market context, and then balances risk-adjusted performance,
stability, conservative win rate, and profit. It never grants execution permission.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from statistics import fmean
from typing import Any, Mapping, Sequence

from afip.historical_replay_research import AppendOnlyResearchDataset


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, float(value)))


def _checksum(value: Mapping[str, Any]) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


@dataclass(frozen=True)
class CapitalPreservationPolicy:
    maximum_drawdown_percent: float = 20.0
    maximum_risk_of_ruin_percent: float = 2.0
    maximum_losing_streak: int = 12
    maximum_tail_loss_r: float = 5.0
    minimum_capital_survival_rate: float = 95.0


@dataclass(frozen=True)
class EvidenceReliabilityPolicy:
    minimum_sample_size: int = 100
    minimum_walk_forward_score: float = 60.0
    minimum_robustness_score: float = 60.0
    minimum_data_quality_score: float = 80.0


@dataclass(frozen=True)
class ProfileRankingWeights:
    capital_preservation: float
    context_match: float
    stability: float
    risk_adjusted_return: float
    evidence_reliability: float
    conservative_win_rate: float
    normalized_profit: float

    def normalized(self) -> "ProfileRankingWeights":
        values = asdict(self)
        total = sum(float(value) for value in values.values())
        if total <= 0:
            raise ValueError("ranking weights must have a positive total")
        return ProfileRankingWeights(**{key: float(value) / total for key, value in values.items()})


DEFAULT_PROFILE_WEIGHTS: Mapping[str, ProfileRankingWeights] = {
    "P1": ProfileRankingWeights(40, 25, 15, 10, 8, 1, 1),
    "P2": ProfileRankingWeights(30, 25, 15, 15, 10, 3, 2),
    "P3": ProfileRankingWeights(22, 25, 13, 20, 10, 5, 5),
    "P4": ProfileRankingWeights(25, 20, 15, 15, 15, 5, 5),
}


@dataclass(frozen=True)
class MarketRankingContext:
    regime: str = "UNKNOWN"
    volatility: str = "NORMAL"
    liquidity: str = "NORMAL"
    session: str = "UNKNOWN"
    news_state: str = "NORMAL"
    direction: str = "FLAT"


@dataclass(frozen=True)
class PlanEvidence:
    plan_id: str
    plan_name: str
    pattern_name: str
    situation_name: str
    sample_size: int
    maximum_drawdown_percent: float
    average_drawdown_percent: float
    drawdown_duration_score: float
    risk_of_ruin_percent: float
    worst_losing_streak: int
    tail_loss_r: float
    capital_survival_rate: float
    context_match_score: float
    walk_forward_score: float
    robustness_score: float
    data_quality_score: float
    temporal_stability_score: float
    parameter_stability_score: float
    return_to_drawdown_score: float
    profit_factor_score: float
    expectancy_score: float
    conservative_win_rate: float
    normalized_profit_score: float
    raw_net_profit: float
    context_tags: Mapping[str, str]


@dataclass(frozen=True)
class RankedPlan:
    rank: int
    plan_id: str
    plan_name: str
    pattern_name: str
    situation_name: str
    eligible: bool
    capital_preservation_passed: bool
    evidence_reliability_passed: bool
    context_match_score: float
    capital_preservation_score: float
    evidence_reliability_score: float
    stability_score: float
    risk_adjusted_return_score: float
    conservative_win_rate: float
    normalized_profit_score: float
    adaptive_composite_score: float
    maximum_drawdown_percent: float
    sample_size: int
    raw_net_profit: float
    rejection_reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RankingResult:
    ranking_id: str
    profile_id: str
    generated_at: str
    context: Mapping[str, str]
    selected_plan_id: str | None
    selected_plan_name: str | None
    eligible_plan_count: int
    rejected_plan_count: int
    ranked_plans: tuple[RankedPlan, ...]
    selection_reason: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["ranking_checksum"] = _checksum(payload)
        return payload


class ContextAwareWeightAdapter:
    """Apply bounded context adjustments while preserving profile intent."""

    MAXIMUM_RELATIVE_ADJUSTMENT = 0.25

    def adapt(self, base: ProfileRankingWeights, context: MarketRankingContext) -> ProfileRankingWeights:
        values = asdict(base.normalized())

        def shift(key: str, relative: float) -> None:
            bounded = max(-self.MAXIMUM_RELATIVE_ADJUSTMENT, min(self.MAXIMUM_RELATIVE_ADJUSTMENT, relative))
            values[key] *= 1.0 + bounded

        volatility = context.volatility.upper()
        regime = context.regime.upper()
        news = context.news_state.upper()
        if volatility in {"HIGH", "EXTREME"}:
            shift("capital_preservation", 0.20)
            shift("risk_adjusted_return", 0.10)
            shift("normalized_profit", -0.20)
        if news in {"HIGH_IMPACT", "RESTRICTED"}:
            shift("capital_preservation", 0.25)
            shift("evidence_reliability", 0.15)
            shift("normalized_profit", -0.25)
        if regime in {"TREND", "STRONG_TREND", "BULL_TREND", "BEAR_TREND"}:
            shift("context_match", 0.15)
            shift("risk_adjusted_return", 0.10)
        if regime in {"RANGE", "SIDEWAY", "CHOPPY"}:
            shift("capital_preservation", 0.12)
            shift("stability", 0.12)
            shift("conservative_win_rate", 0.08)
        return ProfileRankingWeights(**values).normalized()


class AdaptiveMultiObjectivePlanRanker:
    """Rank plans with hard survival/evidence gates before multi-objective scoring."""

    def __init__(self, dataset_root: str | Path | None = None,
                 capital_policy: CapitalPreservationPolicy | None = None,
                 evidence_policy: EvidenceReliabilityPolicy | None = None,
                 profile_weights: Mapping[str, ProfileRankingWeights] | None = None) -> None:
        self.dataset = AppendOnlyResearchDataset(dataset_root) if dataset_root is not None else None
        self.capital_policy = capital_policy or CapitalPreservationPolicy()
        self.evidence_policy = evidence_policy or EvidenceReliabilityPolicy()
        self.profile_weights = dict(profile_weights or DEFAULT_PROFILE_WEIGHTS)
        self.weight_adapter = ContextAwareWeightAdapter()

    def _capital_evaluation(self, plan: PlanEvidence) -> tuple[bool, float, tuple[str, ...]]:
        reasons = []
        policy = self.capital_policy
        if plan.maximum_drawdown_percent > policy.maximum_drawdown_percent:
            reasons.append("maximum_drawdown_above_policy")
        if plan.risk_of_ruin_percent > policy.maximum_risk_of_ruin_percent:
            reasons.append("risk_of_ruin_above_policy")
        if plan.worst_losing_streak > policy.maximum_losing_streak:
            reasons.append("losing_streak_above_policy")
        if plan.tail_loss_r > policy.maximum_tail_loss_r:
            reasons.append("tail_loss_above_policy")
        if plan.capital_survival_rate < policy.minimum_capital_survival_rate:
            reasons.append("capital_survival_below_policy")
        drawdown_score = 100.0 * (1.0 - min(plan.maximum_drawdown_percent / max(policy.maximum_drawdown_percent, 0.01), 1.0))
        ruin_score = 100.0 * (1.0 - min(plan.risk_of_ruin_percent / max(policy.maximum_risk_of_ruin_percent, 0.01), 1.0))
        tail_score = 100.0 * (1.0 - min(plan.tail_loss_r / max(policy.maximum_tail_loss_r, 0.01), 1.0))
        score = fmean((_clamp(drawdown_score), _clamp(ruin_score), _clamp(tail_score),
                       _clamp(plan.capital_survival_rate), _clamp(plan.drawdown_duration_score)))
        return not reasons, score, tuple(reasons)

    def _evidence_evaluation(self, plan: PlanEvidence) -> tuple[bool, float, tuple[str, ...]]:
        reasons = []
        policy = self.evidence_policy
        if plan.sample_size < policy.minimum_sample_size:
            reasons.append("sample_size_below_policy")
        if plan.walk_forward_score < policy.minimum_walk_forward_score:
            reasons.append("walk_forward_below_policy")
        if plan.robustness_score < policy.minimum_robustness_score:
            reasons.append("robustness_below_policy")
        if plan.data_quality_score < policy.minimum_data_quality_score:
            reasons.append("data_quality_below_policy")
        sample_score = _clamp(100.0 * min(plan.sample_size / max(policy.minimum_sample_size * 5, 1), 1.0))
        score = fmean((sample_score, _clamp(plan.walk_forward_score), _clamp(plan.robustness_score), _clamp(plan.data_quality_score)))
        return not reasons, score, tuple(reasons)

    def rank(self, plans: Sequence[PlanEvidence], *, ranking_id: str, profile_id: str,
             context: MarketRankingContext) -> RankingResult:
        profile = profile_id.upper()
        if profile not in self.profile_weights:
            raise ValueError(f"unsupported profile: {profile_id}")
        weights = self.weight_adapter.adapt(self.profile_weights[profile], context)
        scored: list[RankedPlan] = []
        for plan in plans:
            capital_passed, capital_score, capital_reasons = self._capital_evaluation(plan)
            evidence_passed, evidence_score, evidence_reasons = self._evidence_evaluation(plan)
            stability = fmean((_clamp(plan.temporal_stability_score), _clamp(plan.parameter_stability_score)))
            risk_adjusted = fmean((_clamp(plan.return_to_drawdown_score), _clamp(plan.profit_factor_score), _clamp(plan.expectancy_score)))
            eligible = capital_passed and evidence_passed
            composite = (
                capital_score * weights.capital_preservation
                + _clamp(plan.context_match_score) * weights.context_match
                + stability * weights.stability
                + risk_adjusted * weights.risk_adjusted_return
                + evidence_score * weights.evidence_reliability
                + _clamp(plan.conservative_win_rate) * weights.conservative_win_rate
                + _clamp(plan.normalized_profit_score) * weights.normalized_profit
            ) if eligible else 0.0
            scored.append(RankedPlan(0, plan.plan_id, plan.plan_name, plan.pattern_name, plan.situation_name,
                eligible, capital_passed, evidence_passed, _clamp(plan.context_match_score), capital_score,
                evidence_score, stability, risk_adjusted, _clamp(plan.conservative_win_rate),
                _clamp(plan.normalized_profit_score), round(composite, 6), plan.maximum_drawdown_percent,
                plan.sample_size, plan.raw_net_profit, capital_reasons + evidence_reasons))

        scored.sort(key=lambda item: (
            not item.eligible,
            -item.context_match_score,
            -item.adaptive_composite_score,
            item.maximum_drawdown_percent,
            -item.risk_adjusted_return_score,
            -item.stability_score,
            -item.sample_size,
            -item.conservative_win_rate,
            -item.normalized_profit_score,
            item.plan_name,
            item.plan_id,
        ))
        ranked = tuple(RankedPlan(index, **{key: value for key, value in asdict(item).items() if key != "rank"})
                       for index, item in enumerate(scored, start=1))
        selected = next((item for item in ranked if item.eligible), None)
        result = RankingResult(ranking_id, profile, _utc_now(), asdict(context),
            selected.plan_id if selected else None, selected.plan_name if selected else None,
            sum(1 for item in ranked if item.eligible), sum(1 for item in ranked if not item.eligible), ranked,
            "capital_preserving_context_appropriate_plan_selected" if selected else "no_plan_passed_capital_and_evidence_gates")
        if self.dataset is not None:
            self.dataset.append("adaptive_plan_rankings", result.as_dict())
            self.dataset.append("dashboard_research_rankings", {
                "ranking_id": ranking_id, "category": "ADAPTIVE_PLAN", "profile_id": profile,
                "generated_at": result.generated_at, "top_10": [item.as_dict() for item in ranked[:10]],
                "top_100": [item.as_dict() for item in ranked[:100]], "total_ranked": len(ranked),
                "hidden_record_count": max(0, len(ranked) - 100), "selection_reason": result.selection_reason,
            })
        return result
