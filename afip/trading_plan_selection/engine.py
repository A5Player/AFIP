from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence

CONTRACT_VERSION = "AFIP-W4-TRADING-PLAN-1.0"


class TradingPlanSelectionError(ValueError):
    pass


def _text(value: Any) -> str:
    return str(value or "").strip().upper()


def _score(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 4)


@dataclass(frozen=True)
class TradingPlanTemplate:
    plan_id: str
    plan_family: str
    supported_strategy_ids: tuple[str, ...]
    supported_strategy_families: tuple[str, ...] = ()
    minimum_strategy_score: float = 80.0
    minimum_evidence_count: int = 3
    minimum_total_sample_size: int = 100
    minimum_evidence_quality_score: float = 70.0
    active: bool = True

    def validate(self) -> None:
        if not self.plan_id.strip():
            raise TradingPlanSelectionError("plan_id_required")
        if not self.plan_family.strip():
            raise TradingPlanSelectionError("plan_family_required")
        if not self.supported_strategy_ids and not self.supported_strategy_families:
            raise TradingPlanSelectionError("supported_strategy_required")
        if not 0 <= self.minimum_strategy_score <= 100:
            raise TradingPlanSelectionError("minimum_strategy_score_out_of_range")
        if self.minimum_evidence_count < 1 or self.minimum_total_sample_size < 1:
            raise TradingPlanSelectionError("minimum_evidence_requirements_must_be_positive")
        if not 0 <= self.minimum_evidence_quality_score <= 100:
            raise TradingPlanSelectionError("minimum_evidence_quality_score_out_of_range")


@dataclass(frozen=True)
class StrategyCandidateView:
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
    authority: str
    execution_authority: bool
    order_send_allowed: bool
    lot_authority: bool
    sl_tp_authority: bool

    @classmethod
    def from_candidate(cls, candidate: Any) -> "StrategyCandidateView":
        if isinstance(candidate, Mapping):
            get = candidate.get
        else:
            get = lambda key, default=None: getattr(candidate, key, default)
        return cls(
            strategy_id=_text(get("strategy_id", "")),
            strategy_family=_text(get("strategy_family", "")),
            advisory_score=float(get("advisory_score", 0.0)),
            status=_text(get("status", "WAIT")),
            evidence_count=int(get("evidence_count", 0)),
            total_sample_size=int(get("total_sample_size", 0)),
            weighted_similarity=float(get("weighted_similarity", 0.0)),
            weighted_win_rate=float(get("weighted_win_rate", 0.0)),
            weighted_expectancy=float(get("weighted_expectancy", 0.0)),
            evidence_quality_score=float(get("evidence_quality_score", 0.0)),
            authority=_text(get("authority", "UNKNOWN")),
            execution_authority=bool(get("execution_authority", False)),
            order_send_allowed=bool(get("order_send_allowed", False)),
            lot_authority=bool(get("lot_authority", False)),
            sl_tp_authority=bool(get("sl_tp_authority", False)),
        )

    def validate(self) -> None:
        for name in ("advisory_score", "weighted_similarity", "weighted_win_rate", "evidence_quality_score"):
            value = getattr(self, name)
            if not 0 <= value <= 100:
                raise TradingPlanSelectionError(f"{name}_out_of_range")
        if self.evidence_count < 0 or self.total_sample_size < 0:
            raise TradingPlanSelectionError("negative_evidence_value")
        if self.execution_authority or self.order_send_allowed or self.lot_authority or self.sl_tp_authority:
            raise TradingPlanSelectionError("upstream_candidate_claims_forbidden_authority")


@dataclass(frozen=True)
class TradingPlanCandidate:
    plan_id: str
    plan_family: str
    strategy_id: str
    strategy_family: str
    plan_advisory_score: float
    status: str
    evidence_count: int
    total_sample_size: int
    evidence_quality_score: float
    reasons: tuple[str, ...]
    authority: str = "ADVISORY_ONLY"
    final_decision_authority: bool = False
    execution_authority: bool = False
    order_send_allowed: bool = False
    lot_authority: bool = False
    final_sl_tp_authority: bool = False
    bypass_gate_allowed: bool = False
    contract_version: str = CONTRACT_VERSION

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class TradingPlanSelector:
    """Selects evidence-backed plan candidates. It never creates a final trade decision or order."""

    def evaluate(self, template: TradingPlanTemplate, candidate: Any) -> TradingPlanCandidate:
        template.validate()
        view = StrategyCandidateView.from_candidate(candidate)
        view.validate()
        if not template.active:
            return self._blocked(template, view, "plan_inactive")
        if view.authority != "ADVISORY_ONLY":
            return self._blocked(template, view, "strategy_authority_not_advisory")
        if view.status != "ELIGIBLE_FOR_PLAN_REVIEW":
            return self._blocked(template, view, "strategy_not_eligible_for_plan_review")

        supported_ids = {_text(value) for value in template.supported_strategy_ids}
        supported_families = {_text(value) for value in template.supported_strategy_families}
        if view.strategy_id not in supported_ids and view.strategy_family not in supported_families:
            return self._blocked(template, view, "strategy_not_supported_by_plan")
        if view.advisory_score < template.minimum_strategy_score:
            return self._blocked(template, view, "strategy_score_below_plan_minimum")
        if view.evidence_count < template.minimum_evidence_count:
            return self._blocked(template, view, "evidence_count_below_plan_minimum")
        if view.total_sample_size < template.minimum_total_sample_size:
            return self._blocked(template, view, "sample_size_below_plan_minimum")
        if view.evidence_quality_score < template.minimum_evidence_quality_score:
            return self._blocked(template, view, "evidence_quality_below_plan_minimum")

        expectancy_score = _score(50.0 + view.weighted_expectancy * 10.0)
        plan_score = _score(
            view.advisory_score * 0.40
            + view.weighted_similarity * 0.20
            + view.weighted_win_rate * 0.15
            + view.evidence_quality_score * 0.15
            + expectancy_score * 0.10
        )
        status = "ELIGIBLE_FOR_OQS_REVIEW" if plan_score >= 80.0 else "WAIT"
        reasons = (
            "plan_requirements_pass",
            "forward_to_oqs_review",
            "advisory_only",
        ) if status != "WAIT" else (
            "plan_advisory_score_below_80",
            "fail_closed",
            "advisory_only",
        )
        return TradingPlanCandidate(
            plan_id=template.plan_id,
            plan_family=template.plan_family,
            strategy_id=view.strategy_id,
            strategy_family=view.strategy_family,
            plan_advisory_score=plan_score,
            status=status,
            evidence_count=view.evidence_count,
            total_sample_size=view.total_sample_size,
            evidence_quality_score=_score(view.evidence_quality_score),
            reasons=reasons,
        )

    def rank(self, templates: Sequence[TradingPlanTemplate], candidates: Iterable[Any]) -> tuple[TradingPlanCandidate, ...]:
        candidate_views = tuple(candidates)
        results = [self.evaluate(template, candidate) for template in templates for candidate in candidate_views]
        results.sort(
            key=lambda item: (
                item.status == "ELIGIBLE_FOR_OQS_REVIEW",
                item.plan_advisory_score,
                item.total_sample_size,
                item.plan_id,
            ),
            reverse=True,
        )
        return tuple(results)

    @staticmethod
    def _blocked(template: TradingPlanTemplate, view: StrategyCandidateView, reason: str) -> TradingPlanCandidate:
        return TradingPlanCandidate(
            plan_id=template.plan_id,
            plan_family=template.plan_family,
            strategy_id=view.strategy_id,
            strategy_family=view.strategy_family,
            plan_advisory_score=0.0,
            status="WAIT",
            evidence_count=view.evidence_count,
            total_sample_size=view.total_sample_size,
            evidence_quality_score=_score(view.evidence_quality_score),
            reasons=(reason, "fail_closed", "advisory_only"),
        )
