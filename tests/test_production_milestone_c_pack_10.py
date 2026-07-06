from datetime import datetime, timezone, timedelta

from afip.market_history.historical_market_aggregation import HistoricalMarketAggregator
from afip.market_history.historical_market_database import HistoricalMarketDatabase
from afip.market_history.historical_market_observation import HistoricalMarketObservation
from afip.market_history.historical_market_runtime import HistoricalMarketRuntime
from afip.market_history.market_signature_history import MarketSignatureHistoryRepository
from afip.runtime.production_milestone_c_history_runtime import run_dict, run_production_milestone_c_history_runtime


def _observation(**overrides):
    values = {
        "observed_at": datetime(2026, 1, 6, 9, 0, tzinfo=timezone.utc),
        "symbol": "gold#",
        "timeframe": "h1",
        "session": "london",
        "market_regime": "trend",
        "direction": "sell",
        "confidence": 80.0,
        "close_price": 2350.0,
        "spread_points": 28.0,
        "volatility_points": 410.0,
        "macro_bias": "pressure",
        "institutional_bias": "pressure",
        "signature_id": "SIG-TREND-PRESSURE",
        "stage": "entry",
        "source": "test",
    }
    values.update(overrides)
    return HistoricalMarketObservation(**values)


def test_historical_market_observation_normalizes_financial_fields():
    observation = _observation(observed_at=datetime(2026, 1, 6, 9, 0))

    assert observation.symbol == "GOLD#"
    assert observation.timeframe == "H1"
    assert observation.session == "LONDON"
    assert observation.market_regime == "TREND"
    assert observation.direction == "SELL"
    assert observation.observed_at.tzinfo is not None


def test_historical_market_database_compacts_repeated_observations():
    database = HistoricalMarketDatabase()
    first = database.observe(_observation(confidence=80.0))
    second = database.observe(_observation(confidence=90.0, close_price=2349.5))

    assert first is second
    assert database.summary()["unique_records"] == 1
    assert database.summary()["total_observations"] == 2
    assert second.average_confidence == 85.0


def test_historical_market_database_keeps_only_important_observation_stages():
    database = HistoricalMarketDatabase()
    database.observe(_observation(stage="stream"))
    database.observe(_observation(stage="entry"))
    database.observe(_observation(stage="review"))

    important = database.important_observations()

    assert len(important) == 2
    assert [item.stage for item in important] == ["ENTRY", "REVIEW"]


def test_historical_market_aggregator_builds_daily_summary():
    aggregator = HistoricalMarketAggregator()
    aggregator.observe(_observation(direction="sell"))
    aggregator.observe(_observation(direction="buy", confidence=70.0))

    summary = aggregator.daily_summary()[0]

    assert summary["period_key"] == "2026-01-06"
    assert summary["observation_count"] == 2
    assert summary["direction_counts"] == {"BUY": 1, "SELL": 1}
    assert summary["average_confidence"] == 75.0


def test_historical_market_aggregator_builds_session_summary():
    aggregator = HistoricalMarketAggregator()
    aggregator.observe(_observation(session="london"))
    aggregator.observe(_observation(session="newyork", observed_at=datetime(2026, 1, 6, 14, 0, tzinfo=timezone.utc)))

    session_summary = aggregator.session_summary()

    assert len(session_summary) == 2
    assert session_summary[0]["period_key"] == "2026-01-06:LONDON"
    assert session_summary[1]["period_key"] == "2026-01-06:NEWYORK"


def test_market_signature_history_counts_repeated_signature_once_per_record():
    repository = MarketSignatureHistoryRepository()
    repository.observe(_observation(direction="sell"))
    repository.observe(_observation(direction="sell", observed_at=datetime(2026, 1, 6, 10, 0, tzinfo=timezone.utc)))

    record = repository.get("SIG-TREND-PRESSURE")

    assert record is not None
    assert record.occurrence_count == 2
    assert record.as_dict()["dominant_direction"] == "SELL"


def test_market_signature_history_ranks_by_occurrence():
    repository = MarketSignatureHistoryRepository()
    repository.observe(_observation(signature_id="SIG-A"))
    repository.observe(_observation(signature_id="SIG-A", observed_at=datetime(2026, 1, 6, 10, 0, tzinfo=timezone.utc)))
    repository.observe(_observation(signature_id="SIG-B"))

    records = repository.records()

    assert records[0].signature_id == "SIG-A"
    assert records[0].occurrence_count == 2


def test_historical_market_runtime_integrates_database_aggregation_and_signature_history():
    runtime = HistoricalMarketRuntime()
    state = runtime.observe_many([
        _observation(),
        _observation(observed_at=datetime(2026, 1, 6, 10, 0, tzinfo=timezone.utc)),
    ])

    payload = state.as_dict()

    assert payload["status"] == "HISTORICAL_MARKET_RUNTIME_READY"
    assert payload["database_summary"]["compression_ratio"] == 2.0
    assert payload["aggregation_summary"]["daily_periods"] == 1
    assert payload["signature_summary"]["unique_signatures"] == 1


def test_production_milestone_c_history_runtime_builds_ready_state():
    state = run_production_milestone_c_history_runtime()

    assert state.status == "HISTORICAL_MARKET_RUNTIME_READY"
    assert state.database_summary["total_observations"] == 3
    assert state.signature_summary["unique_signatures"] == 2


def test_production_milestone_c_history_runtime_run_dict_is_deterministic():
    first = run_dict()
    second = run_dict()

    assert first["database_summary"]["total_observations"] == second["database_summary"]["total_observations"]
    assert first["signature_summary"] == second["signature_summary"]


def test_production_milestone_c_history_runtime_accepts_custom_observations():
    observations = [
        _observation(signature_id="SIG-CUSTOM", observed_at=datetime(2026, 1, 7, 8, 0, tzinfo=timezone.utc)),
        _observation(signature_id="SIG-CUSTOM", observed_at=datetime(2026, 1, 7, 8, 15, tzinfo=timezone.utc), stage="review"),
        _observation(signature_id="SIG-CUSTOM", observed_at=datetime(2026, 1, 7, 8, 30, tzinfo=timezone.utc), stage="stream"),
    ]

    payload = run_dict(observations)

    assert payload["database_summary"]["compression_ratio"] == 3.0
    assert payload["signature_summary"]["top_signatures"][0]["signature_id"] == "SIG-CUSTOM"
    assert len(payload["important_observations"]) == 2
