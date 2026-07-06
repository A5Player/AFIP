"""Production entrypoint for Milestone F Pack 1 adaptive AI foundation."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.adaptive_ai_foundation import AdaptiveAIFoundationReport, AdaptiveAIFoundationRuntime


def sample_adaptive_ai_observations() -> list[dict[str, object]]:
    return [
        {
            "market_regime": "TREND_EXPANSION",
            "signal_context": "CONTINUATION",
            "result_amount": 14.0,
            "confidence_score": 0.74,
            "knowledge_quality": 0.82,
            "sample_weight": 3.0,
            "source_key": "MARKET_KNOWLEDGE",
        },
        {
            "market_regime": "TREND_EXPANSION",
            "signal_context": "PULLBACK",
            "result_amount": 6.0,
            "confidence_score": 0.68,
            "knowledge_quality": 0.78,
            "sample_weight": 2.0,
            "source_key": "SESSION_INTELLIGENCE",
        },
        {
            "market_regime": "RANGE_COMPRESSION",
            "signal_context": "MEAN_REVERSION",
            "result_amount": -3.0,
            "confidence_score": 0.55,
            "knowledge_quality": 0.66,
            "sample_weight": 1.0,
            "source_key": "VOLATILITY_INTELLIGENCE",
        },
    ]


class ProductionMilestoneFAdaptiveAIFoundationRuntime:
    """Production wrapper for adaptive AI foundation capability."""

    def __init__(self) -> None:
        self.runtime = AdaptiveAIFoundationRuntime()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> AdaptiveAIFoundationReport:
        return self.runtime.run(observations)


def run_dict() -> dict[str, object]:
    return ProductionMilestoneFAdaptiveAIFoundationRuntime().run(sample_adaptive_ai_observations()).as_dict()
