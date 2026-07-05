from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from afip.fusion.intelligence_conflict_analyzer import IntelligenceConflictAnalyzer


@dataclass(frozen=True)
class IntelligenceConsensusResult:
    status: str
    consensus_level: str
    consensus_direction: str
    consensus_score: float
    participation_count: int
    reason: str


class IntelligenceConsensusEngine:
    """Convert multi-source directional inputs into a consensus profile."""

    def evaluate(self, intelligence_inputs: Iterable[Mapping[str, object]] | None = None) -> IntelligenceConsensusResult:
        inputs = list(intelligence_inputs or [])
        analysis = IntelligenceConflictAnalyzer().analyze(inputs)
        participation_count = len(inputs)

        if participation_count == 0:
            return IntelligenceConsensusResult(
                status="CONSENSUS_READY",
                consensus_level="LOW",
                consensus_direction="FLAT",
                consensus_score=0.0,
                participation_count=0,
                reason="insufficient_intelligence_participation",
            )

        dominant_pressure = max(analysis.buy_pressure, analysis.sell_pressure, analysis.flat_pressure)
        conflict_penalty = analysis.conflict_ratio * 0.35
        participation_factor = min(participation_count / 5.0, 1.0)
        consensus_score = max(0.0, min(1.0, dominant_pressure - conflict_penalty + participation_factor * 0.10))
        consensus_level = self._level(consensus_score, analysis.conflict_level)

        return IntelligenceConsensusResult(
            status="CONSENSUS_READY",
            consensus_level=consensus_level,
            consensus_direction=analysis.dominant_direction,
            consensus_score=round(consensus_score, 4),
            participation_count=participation_count,
            reason=self._reason(consensus_level, analysis.conflict_level),
        )

    @staticmethod
    def _level(score: float, conflict_level: str) -> str:
        if conflict_level == "HIGH":
            return "LOW" if score < 0.78 else "MODERATE"
        if score >= 0.72:
            return "HIGH"
        if score >= 0.48:
            return "MODERATE"
        return "LOW"

    @staticmethod
    def _reason(consensus_level: str, conflict_level: str) -> str:
        if conflict_level == "HIGH":
            return "consensus_reduced_by_directional_conflict"
        if consensus_level == "HIGH":
            return "broad_intelligence_consensus"
        if consensus_level == "MODERATE":
            return "partial_intelligence_consensus"
        return "limited_intelligence_consensus"
