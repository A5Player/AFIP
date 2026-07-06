"""Production Milestone C Pack 11 historical replay runtime entry point."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from afip.replay.historical_replay_provider import StaticHistoricalReplayProvider
from afip.replay.replay_runtime import ReplayRuntime, ReplayRuntimeState
from afip.replay.replay_snapshot import ReplaySnapshot


def _default_replay_snapshots() -> list[ReplaySnapshot]:
    base = datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc)
    return [
        ReplaySnapshot(
            observed_at=base,
            symbol="GOLD#",
            timeframe="H1",
            session="LONDON",
            market_regime="TREND",
            direction="BUY",
            close_price=2320.10,
            confidence=82.0,
            spread_points=24.0,
            volatility_points=210.0,
            macro_bias="SUPPORTIVE",
            institutional_bias="SUPPORTIVE",
            signature_id="MSIG-GOLD-SUPPORTIVE-001",
        ),
        ReplaySnapshot(
            observed_at=base + timedelta(hours=1),
            symbol="GOLD#",
            timeframe="H1",
            session="LONDON",
            market_regime="TREND",
            direction="BUY",
            close_price=2328.40,
            confidence=86.0,
            spread_points=23.0,
            volatility_points=230.0,
            macro_bias="SUPPORTIVE",
            institutional_bias="SUPPORTIVE",
            signature_id="MSIG-GOLD-SUPPORTIVE-001",
        ),
        ReplaySnapshot(
            observed_at=base + timedelta(hours=2),
            symbol="GOLD#",
            timeframe="H1",
            session="NEW_YORK",
            market_regime="EXPANSION",
            direction="BUY",
            close_price=2336.70,
            confidence=88.0,
            spread_points=25.0,
            volatility_points=260.0,
            macro_bias="SUPPORTIVE",
            institutional_bias="SUPPORTIVE",
            signature_id="MSIG-GOLD-SUPPORTIVE-002",
        ),
    ]


def build_production_milestone_c_replay_runtime() -> ReplayRuntime:
    """Build the deterministic Pack 11 replay runtime."""
    return ReplayRuntime(provider=StaticHistoricalReplayProvider(_default_replay_snapshots()))


def run_production_milestone_c_replay_runtime() -> ReplayRuntimeState:
    """Run the deterministic Pack 11 replay runtime."""
    base = datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc)
    return build_production_milestone_c_replay_runtime().run(
        start_at=base,
        end_at=base + timedelta(hours=3),
        symbol="GOLD#",
    )


def run_dict() -> dict[str, object]:
    """Return runtime state as a serializable dictionary."""
    return run_production_milestone_c_replay_runtime().as_dict()
