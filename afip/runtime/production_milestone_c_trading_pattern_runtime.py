"""Production Milestone C Pack 12 trading pattern runtime entrypoint."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from afip.trading_patterns.trade_pattern_quality import TradePatternQuality
from afip.trading_patterns.trade_pattern_record import TradePatternRecord
from afip.trading_patterns.trading_pattern_runtime import TradingPatternRuntime


def sample_records() -> list[TradePatternRecord]:
    base = datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc)
    records: list[TradePatternRecord] = []
    results = [24.0, 18.0, 12.0, -6.0, 16.0, 20.0]
    for index, result in enumerate(results):
        records.append(
            TradePatternRecord(
                observed_at=base + timedelta(hours=index),
                symbol="GOLD#",
                position_direction="BUY",
                market_regime="TREND",
                session="LONDON",
                macro_bias="SUPPORTIVE",
                institutional_bias="SUPPORTIVE",
                liquidity_state="BALANCED",
                volatility_bucket="NORMAL",
                strategy_profile="DAY_TRADE",
                entry_quality=82.0,
                result_amount=result,
                holding_minutes=42.0 + index,
                mae_points=110.0,
                mfe_points=260.0,
                execution_cost_points=24.0,
                tags=("PULLBACK", "MACRO_ALIGNED"),
            )
        )
    records.append(
        TradePatternRecord(
            observed_at=base + timedelta(hours=8),
            symbol="GOLD#",
            position_direction="SELL",
            market_regime="EXPANSION",
            session="NEW_YORK",
            macro_bias="PRESSURE",
            institutional_bias="NEUTRAL",
            liquidity_state="SELL_SIDE_SWEEP",
            volatility_bucket="HIGH",
            strategy_profile="INTRADAY_MOMENTUM",
            entry_quality=74.0,
            result_amount=-8.0,
            holding_minutes=18.0,
            mae_points=160.0,
            mfe_points=90.0,
            execution_cost_points=31.0,
            tags=("NEWS_REVIEW",),
        )
    )
    return records


def run() -> object:
    runtime = TradingPatternRuntime(quality=TradePatternQuality(minimum_observations=5))
    return runtime.run(sample_records())


def run_dict() -> dict[str, object]:
    return run().as_dict()
