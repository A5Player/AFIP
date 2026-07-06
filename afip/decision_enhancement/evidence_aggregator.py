"""Aggregate decision evidence by market regime before signal direction."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .decision_context import DecisionContext
from .decision_evidence import DecisionEvidence


@dataclass(frozen=True)
class DecisionEvidenceGroup:
    regime_first_key: str
    direction: str
    observations: int
    average_confidence: float
    average_expectancy: float
    average_execution_cost_points: float
    average_reliability: float
    evidence_score: float
    sources: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "regime_first_key": self.regime_first_key,
            "direction": self.direction,
            "observations": self.observations,
            "average_confidence": self.average_confidence,
            "average_expectancy": self.average_expectancy,
            "average_execution_cost_points": self.average_execution_cost_points,
            "average_reliability": self.average_reliability,
            "evidence_score": self.evidence_score,
            "sources": list(self.sources),
        }


class DecisionEvidenceAggregator:
    """Create data-derived directional groups for the active regime."""

    def aggregate(self, context: DecisionContext, evidence: list[DecisionEvidence]) -> list[DecisionEvidenceGroup]:
        if context.status != "DECISION_CONTEXT_READY":
            return []
        active = [
            item for item in evidence
            if item.market_regime == context.market_regime and item.volatility_bucket == context.volatility_bucket
        ]
        grouped: dict[str, list[DecisionEvidence]] = defaultdict(list)
        for item in active:
            grouped[item.direction].append(item)
        groups: list[DecisionEvidenceGroup] = []
        for direction in sorted(grouped):
            items = grouped[direction]
            observations = len(items)
            avg_confidence = sum(item.confidence for item in items) / observations
            avg_expectancy = sum(item.expectancy for item in items) / observations
            avg_cost = sum(item.execution_cost_points for item in items) / observations
            avg_reliability = sum(item.reliability for item in items) / observations
            score = avg_confidence * 0.45 + max(avg_expectancy, 0.0) * 2.0 + avg_reliability * 0.35 - avg_cost * 0.25
            groups.append(DecisionEvidenceGroup(
                regime_first_key=f"{context.market_regime}|{context.volatility_bucket}|{direction}",
                direction=direction,
                observations=observations,
                average_confidence=round(avg_confidence, 4),
                average_expectancy=round(avg_expectancy, 4),
                average_execution_cost_points=round(avg_cost, 4),
                average_reliability=round(avg_reliability, 4),
                evidence_score=round(max(0.0, score), 4),
                sources=tuple(sorted(item.source for item in items)),
            ))
        return sorted(groups, key=lambda item: (-item.evidence_score, item.regime_first_key))
