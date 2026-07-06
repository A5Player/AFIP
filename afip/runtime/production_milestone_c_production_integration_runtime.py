"""Production entrypoint for Milestone C Pack 19 production integration."""

from __future__ import annotations

from afip.production_integration import ProductionIntegrationRuntime


def sample_regime_state() -> dict[str, object]:
    return {
        "status": "MARKET_REGIME_INTELLIGENCE_READY",
        "reason": "learned_regime_thresholds_applied_before_signal",
        "classification": {"regime_first_key": "EXPANSION|HIGH|BUY"},
    }


def sample_decision_state() -> dict[str, object]:
    return {
        "status": "DECISION_INTELLIGENCE_READY",
        "reason": "decision_candidate_selected_from_regime_evidence",
        "decision": {"action": "BUY", "confidence": 82.0, "score": 68.5, "regime_first_key": "EXPANSION|HIGH|BUY"},
    }


def sample_execution_state() -> dict[str, object]:
    return {
        "status": "EXECUTION_READY",
        "reason": "execution_readiness_confirmed_from_data",
        "input": {
            "regime_first_key": "EXPANSION|HIGH|BUY",
            "decision_confidence": 82.0,
            "spread_points": 24.0,
            "maximum_spread_points": 35.0,
        },
        "decision": {"action": "BUY", "readiness_score": 72.25, "reason": "execution_readiness_confirmed_from_data"},
    }


def run_dict() -> dict[str, object]:
    return ProductionIntegrationRuntime().run(sample_regime_state(), sample_decision_state(), sample_execution_state()).as_dict()
