from __future__ import annotations

from datetime import datetime, timedelta, timezone

from afip.market_history.historical_market_runtime import HistoricalMarketRuntime
from afip.replay.historical_replay_provider import StaticHistoricalReplayProvider
from afip.replay.replay_report import ReplayReportBuilder
from afip.replay.replay_runtime import ReplayRuntime
from afip.replay.replay_session import ReplaySessionEngine
from afip.replay.replay_snapshot import ReplaySnapshot
from afip.replay.replay_timeline import ReplayTimeline
from afip.replay.replay_validation import ReplayValidationEngine
from afip.runtime.production_milestone_c_replay_runtime import run_dict


def _snapshots() -> list[ReplaySnapshot]:
    base = datetime(2026, 1, 2, 8, 0, tzinfo=timezone.utc)
    return [
        ReplaySnapshot(
            observed_at=base,
            symbol="GOLD#",
            timeframe="H1",
            session="LONDON",
            market_regime="TREND",
            direction="BUY",
            close_price=2300.0,
            confidence=80.0,
            spread_points=22.0,
            volatility_points=190.0,
            macro_bias="SUPPORTIVE",
            institutional_bias="SUPPORTIVE",
            signature_id="MSIG-A",
        ),
        ReplaySnapshot(
            observed_at=base + timedelta(hours=1),
            symbol="GOLD#",
            timeframe="H1",
            session="LONDON",
            market_regime="TREND",
            direction="BUY",
            close_price=2308.0,
            confidence=84.0,
            spread_points=24.0,
            volatility_points=220.0,
            macro_bias="SUPPORTIVE",
            institutional_bias="SUPPORTIVE",
            signature_id="MSIG-A",
        ),
        ReplaySnapshot(
            observed_at=base + timedelta(hours=2),
            symbol="GOLD#",
            timeframe="H1",
            session="NEW_YORK",
            market_regime="EXPANSION",
            direction="SELL",
            close_price=2296.0,
            confidence=78.0,
            spread_points=26.0,
            volatility_points=250.0,
            macro_bias="PRESSURE",
            institutional_bias="NEUTRAL",
            signature_id="MSIG-B",
        ),
    ]


def test_static_historical_replay_provider_filters_period_and_symbol() -> None:
    snapshots = _snapshots()
    provider = StaticHistoricalReplayProvider(snapshots)
    result = provider.load(snapshots[0].observed_at, snapshots[1].observed_at, symbol="GOLD#")
    assert len(result) == 2
    assert result[0].close_price == 2300.0


def test_replay_snapshot_normalizes_values_and_converts_to_observation() -> None:
    snapshot = ReplaySnapshot(
        observed_at=datetime(2026, 1, 2, 8, 0),
        symbol="gold#",
        timeframe="h1",
        market_regime="trend",
        direction="buy",
        close_price=2300.0,
    )
    observation = snapshot.to_observation()
    assert snapshot.symbol == "GOLD#"
    assert snapshot.observed_at.tzinfo is not None
    assert observation.stage == "REPLAY_STEP"


def test_replay_timeline_sorts_snapshots_and_counts_direction() -> None:
    snapshots = list(reversed(_snapshots()))
    timeline = ReplayTimeline(snapshots)
    assert timeline.first().close_price == 2300.0
    assert timeline.direction_counts() == {"BUY": 2, "SELL": 1}


def test_replay_timeline_builds_average_cost_and_volatility() -> None:
    timeline = ReplayTimeline(_snapshots())
    assert timeline.average_spread() == 24.0
    assert timeline.average_volatility() == 220.0


def test_replay_validation_ready_for_sufficient_clean_timeline() -> None:
    result = ReplayValidationEngine().validate(ReplayTimeline(_snapshots()))
    assert result.status == "REPLAY_VALIDATION_READY"
    assert result.quality_score == 100.0


def test_replay_validation_blocks_insufficient_high_cost_timeline() -> None:
    snapshot = ReplaySnapshot(
        observed_at=datetime(2026, 1, 2, 8, 0, tzinfo=timezone.utc),
        symbol="GOLD#",
        timeframe="H1",
        market_regime="TREND",
        direction="BUY",
        close_price=2300.0,
        spread_points=80.0,
    )
    result = ReplayValidationEngine(minimum_snapshots=3, maximum_average_spread_points=45).validate(
        ReplayTimeline([snapshot])
    )
    assert result.status == "REPLAY_VALIDATION_BLOCKED"
    assert "insufficient_replay_snapshots" in result.reasons


def test_replay_session_engine_processes_timeline_into_history() -> None:
    engine = ReplaySessionEngine(history_runtime=HistoricalMarketRuntime())
    result = engine.run(ReplayTimeline(_snapshots()))
    assert result.status == "REPLAY_SESSION_READY"
    assert result.processed_snapshots == 3
    assert result.history_summary["database_summary"]["unique_records"] >= 2


def test_replay_session_engine_handles_empty_timeline() -> None:
    result = ReplaySessionEngine().run(ReplayTimeline([]))
    assert result.status == "REPLAY_SESSION_EMPTY"
    assert result.processed_snapshots == 0


def test_replay_report_builder_creates_dashboard_friendly_rows() -> None:
    session_result = ReplaySessionEngine().run(ReplayTimeline(_snapshots()))
    validation = ReplayValidationEngine().validate(ReplayTimeline(_snapshots()))
    report = ReplayReportBuilder().build(session_result, validation)
    assert "Replay 3 snapshots" in report.summary
    assert len(report.rows) == 5


def test_replay_runtime_builds_ready_state() -> None:
    base = _snapshots()[0].observed_at
    runtime = ReplayRuntime(provider=StaticHistoricalReplayProvider(_snapshots()))
    state = runtime.run(base, base + timedelta(hours=3), symbol="GOLD#")
    assert state.status == "REPLAY_RUNTIME_READY"
    assert state.session["processed_snapshots"] == 3


def test_production_milestone_c_replay_runtime_is_deterministic() -> None:
    first = run_dict()
    second = run_dict()
    assert first == second
    assert first["status"] == "REPLAY_RUNTIME_READY"
