from __future__ import annotations

from datetime import datetime, timedelta, timezone

from afip.runtime.production_milestone_c_trading_pattern_runtime import run_dict, sample_records
from afip.trading_patterns.trade_outcome_statistics import TradeOutcomeStatistics
from afip.trading_patterns.trade_pattern_quality import TradePatternQuality
from afip.trading_patterns.trade_pattern_record import TradePatternRecord
from afip.trading_patterns.trade_pattern_repository import TradePatternRepository, TradingSetupRepository
from afip.trading_patterns.trading_pattern_runtime import TradingPatternRuntime


def _record(result: float = 10.0, *, direction: str = "buy", quality: float = 83.0) -> TradePatternRecord:
    return TradePatternRecord(
        observed_at=datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc),
        symbol="gold#",
        position_direction=direction,
        market_regime="trend",
        session="london",
        macro_bias="supportive",
        institutional_bias="supportive",
        liquidity_state="balanced",
        volatility_bucket="normal",
        strategy_profile="day trade",
        entry_quality=quality,
        result_amount=result,
        holding_minutes=45.0,
        mae_points=-120.0,
        mfe_points=260.0,
        execution_cost_points=24.0,
        tags=("macro aligned", "pullback"),
    )


def test_trade_outcome_statistics_tracks_compact_profitability() -> None:
    stats = TradeOutcomeStatistics()
    stats.observe(result_amount=20.0, holding_minutes=30, mae_points=50, mfe_points=120, execution_cost_points=20)
    stats.observe(result_amount=-10.0, holding_minutes=20, mae_points=80, mfe_points=40, execution_cost_points=30)
    assert stats.observations == 2
    assert stats.win_rate == 50.0
    assert stats.expectancy == 5.0
    assert stats.profit_factor == 2.0
    assert stats.average_execution_cost_points == 25.0


def test_trade_pattern_record_normalizes_key_fields() -> None:
    record = _record()
    assert record.symbol == "GOLD#"
    assert record.position_direction == "BUY"
    assert "DAY_TRADE" in record.pattern_key
    assert "MACRO_ALIGNED+PULLBACK" in record.setup_key


def test_trade_pattern_repository_counts_repeated_pattern_once() -> None:
    repository = TradePatternRepository()
    repository.observe(_record(12.0))
    repository.observe(_record(-4.0))
    data = repository.as_dict()
    assert data["unique_patterns"] == 1
    assert data["patterns"][0]["statistics"]["observations"] == 2


def test_trade_pattern_repository_ranks_by_expectancy() -> None:
    repository = TradePatternRepository()
    repository.observe(_record(-10.0, direction="sell"))
    repository.observe(_record(25.0, direction="buy"))
    assert repository.ranked()[0].statistics.expectancy == 25.0


def test_trading_setup_repository_separates_entry_quality_bucket() -> None:
    repository = TradingSetupRepository()
    repository.observe(_record(10.0, quality=83.0))
    repository.observe(_record(10.0, quality=67.0))
    assert repository.as_dict()["unique_setups"] == 2


def test_trade_pattern_quality_observe_only_for_small_sample() -> None:
    repository = TradePatternRepository()
    summary = repository.observe(_record(20.0))
    result = TradePatternQuality(minimum_observations=3).assess(summary)
    assert result.status == "PATTERN_OBSERVE_ONLY"
    assert "insufficient_pattern_observations" in result.reasons


def test_trade_pattern_quality_ready_for_profitable_sample() -> None:
    repository = TradePatternRepository()
    summary = None
    for index in range(5):
        summary = repository.observe(_record(12.0 + index))
    assert summary is not None
    result = TradePatternQuality(minimum_observations=5, minimum_profit_factor=1.0).assess(summary)
    assert result.status == "PATTERN_RESEARCH_READY"


def test_trade_pattern_quality_blocks_high_execution_cost() -> None:
    repository = TradePatternRepository()
    summary = None
    for index in range(5):
        record = TradePatternRecord(
            observed_at=datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc) + timedelta(hours=index),
            position_direction="BUY",
            market_regime="TREND",
            session="LONDON",
            result_amount=20.0,
            execution_cost_points=80.0,
        )
        summary = repository.observe(record)
    assert summary is not None
    result = TradePatternQuality(maximum_average_cost_points=45.0).assess(summary)
    assert result.status == "PATTERN_OBSERVE_ONLY"
    assert "execution_cost_above_research_threshold" in result.reasons


def test_trading_pattern_runtime_builds_ready_state() -> None:
    runtime = TradingPatternRuntime(quality=TradePatternQuality(minimum_observations=5))
    state = runtime.run(sample_records())
    assert state.status == "TRADING_PATTERN_READY"
    assert state.pattern_repository["unique_patterns"] == 2
    assert state.best_pattern_quality["status"] == "PATTERN_RESEARCH_READY"


def test_trading_pattern_runtime_handles_empty_records() -> None:
    state = TradingPatternRuntime().run([])
    assert state.status == "TRADING_PATTERN_REVIEW"
    assert state.reason == "no_trading_pattern_records"


def test_production_milestone_c_trading_pattern_runtime_is_deterministic() -> None:
    first = run_dict()
    second = run_dict()
    assert first == second
    assert first["status"] == "TRADING_PATTERN_READY"
