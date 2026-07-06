"""Production entry point for Milestone D Pack 2 data pipeline integration."""

from __future__ import annotations

from afip.data_pipeline import DataPipelineRuntime


def build_production_milestone_d_data_pipeline_state() -> dict[str, object]:
    records = [
        {
            "source_key": "MARKET_DATA",
            "market_regime": "TRENDING",
            "timeframe": "H1",
            "close_price": 2350.25,
            "spread_points": 24.0,
            "liquidity_score": 82.0,
            "completeness_ratio": 0.96,
            "reason": "market_data_ready",
        },
        {
            "source_key": "REGIME_STATE",
            "market_regime": "TRENDING",
            "timeframe": "H1",
            "close_price": 2350.25,
            "spread_points": 24.0,
            "liquidity_score": 80.0,
            "completeness_ratio": 0.94,
            "reason": "regime_state_ready",
        },
        {
            "source_key": "DECISION_STATE",
            "market_regime": "TRENDING",
            "timeframe": "H1",
            "close_price": 2350.25,
            "spread_points": 24.0,
            "liquidity_score": 78.0,
            "completeness_ratio": 0.92,
            "reason": "decision_state_ready",
        },
        {
            "source_key": "EXECUTION_STATE",
            "market_regime": "TRENDING",
            "timeframe": "H1",
            "close_price": 2350.25,
            "spread_points": 24.0,
            "liquidity_score": 76.0,
            "completeness_ratio": 0.91,
            "reason": "execution_state_ready",
        },
    ]
    return DataPipelineRuntime().run(records).as_dict()
