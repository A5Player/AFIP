"""Strategy evolution observation contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class StrategyEvolutionObservation:
    """Normalized knowledge-backed evidence for deterministic strategy evolution."""

    market_regime: str
    signal_context: str
    experience_score: float
    expectancy: float
    sample_count: float
    positive_rate: float
    data_quality: float
    knowledge_quality: float
    reliability_score: float
    current_strategy_weight: float
    evidence_source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "StrategyEvolutionObservation":
        market_regime = str(value.get("market_regime", "")).strip().upper()
        signal_context = str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        experience_score = _ratio(value.get("experience_score", value.get("knowledge_score", 0.0)))
        expectancy = _expectancy(value.get("expectancy", value.get("expected_result", 0.0)))
        sample_count = max(float(value.get("sample_count", value.get("samples", 1.0))), 0.0)
        positive_rate = _ratio(value.get("positive_rate", value.get("win_rate", 0.0)))
        data_quality = _ratio(value.get("average_data_quality", value.get("data_quality", 0.0)))
        knowledge_quality = _ratio(value.get("average_knowledge_quality", value.get("knowledge_quality", data_quality)))
        reliability_score = _ratio(value.get("average_reliability_score", value.get("reliability_score", knowledge_quality)))
        current_strategy_weight = _ratio(value.get("current_strategy_weight", value.get("strategy_weight", 0.50)))
        evidence_source = str(value.get("evidence_source", value.get("source", "EXPERIENCE_KNOWLEDGE"))).strip().upper() or "EXPERIENCE_KNOWLEDGE"
        return cls(
            market_regime=market_regime,
            signal_context=signal_context,
            experience_score=experience_score,
            expectancy=expectancy,
            sample_count=sample_count,
            positive_rate=positive_rate,
            data_quality=data_quality,
            knowledge_quality=knowledge_quality,
            reliability_score=reliability_score,
            current_strategy_weight=current_strategy_weight,
            evidence_source=evidence_source,
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def evidence_quality(self) -> float:
        value = (self.data_quality + self.knowledge_quality + self.reliability_score) / 3.0
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def weighted_experience_score(self) -> float:
        return self.experience_score * self.sample_count

    @property
    def weighted_expectancy(self) -> float:
        return self.expectancy * self.sample_count

    @property
    def weighted_positive_rate(self) -> float:
        return self.positive_rate * self.sample_count

    @property
    def weighted_evidence_quality(self) -> float:
        return self.evidence_quality * self.sample_count


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return min(max(number, 0.0), 1.0)


def _expectancy(value: Any) -> float:
    number = float(value)
    if abs(number) > 1.0:
        number = number / 100.0
    return min(max(number, -1.0), 1.0)
