"""Deterministic decision selection policy for enhanced decision intelligence."""

from __future__ import annotations

from dataclasses import dataclass

from .evidence_aggregator import DecisionEvidenceGroup


@dataclass(frozen=True)
class DecisionCandidate:
    action: str
    confidence: float
    score: float
    regime_first_key: str
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "confidence": self.confidence,
            "score": self.score,
            "regime_first_key": self.regime_first_key,
            "reasons": list(self.reasons),
        }


class DecisionSelectionPolicy:
    minimum_observations: int = 2
    minimum_score: float = 55.0
    minimum_edge: float = 5.0
    maximum_execution_cost_points: float = 45.0

    def select(self, groups: list[DecisionEvidenceGroup]) -> DecisionCandidate:
        if not groups:
            return DecisionCandidate("WAIT", 0.0, 0.0, "UNKNOWN", ("decision_evidence_required",))
        candidates = [
            group for group in groups
            if group.direction in {"BUY", "SELL"}
            and group.observations >= self.minimum_observations
            and group.average_execution_cost_points <= self.maximum_execution_cost_points
        ]
        if not candidates:
            return DecisionCandidate("WAIT", 0.0, 0.0, groups[0].regime_first_key, ("decision_group_failed_policy",))
        ranked = sorted(candidates, key=lambda item: (-item.evidence_score, item.regime_first_key))
        best = ranked[0]
        second_score = ranked[1].evidence_score if len(ranked) > 1 else 0.0
        edge = best.evidence_score - second_score
        if best.evidence_score < self.minimum_score:
            return DecisionCandidate("WAIT", round(best.average_confidence, 4), best.evidence_score, best.regime_first_key, ("decision_score_below_policy",))
        if len(ranked) > 1 and edge < self.minimum_edge:
            return DecisionCandidate("WAIT", round(best.average_confidence, 4), best.evidence_score, best.regime_first_key, ("decision_edge_below_policy",))
        confidence = round(min(100.0, best.average_confidence * 0.55 + best.average_reliability * 0.3 + edge * 0.15), 4)
        return DecisionCandidate(best.direction, confidence, best.evidence_score, best.regime_first_key, ("decision_policy_selected_data_derived_candidate",))
