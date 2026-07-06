"""Production entrypoint for Milestone C Pack 17 decision enhancement."""

from __future__ import annotations

from afip.decision_enhancement import DecisionEnhancementRuntime, DecisionEvidence


def sample_regime_classification() -> dict[str, object]:
    return {
        "status": "REGIME_CLASSIFICATION_READY",
        "market_regime": "EXPANSION",
        "volatility_bucket": "HIGH",
        "direction_bias": "BUY",
        "confidence": 80.0,
    }


def sample_decision_evidence() -> list[DecisionEvidence]:
    values = [
        ("EXPANSION", "HIGH", "BUY", "trend_quality", 82.0, 9.0, 22.0, 84.0),
        ("EXPANSION", "HIGH", "BUY", "participation_quality", 78.0, 7.0, 24.0, 80.0),
        ("EXPANSION", "HIGH", "SELL", "mean_reversion_risk", 54.0, 1.0, 28.0, 55.0),
        ("NORMAL", "NORMAL", "SELL", "inactive_profile", 88.0, 12.0, 18.0, 90.0),
    ]
    return [
        DecisionEvidence(
            market_regime=regime,
            volatility_bucket=volatility,
            direction=direction,
            source=source,
            confidence=confidence,
            expectancy=expectancy,
            execution_cost_points=cost,
            reliability=reliability,
        )
        for regime, volatility, direction, source, confidence, expectancy, cost, reliability in values
    ]


def run_dict() -> dict[str, object]:
    return DecisionEnhancementRuntime().run(sample_regime_classification(), sample_decision_evidence()).as_dict()
