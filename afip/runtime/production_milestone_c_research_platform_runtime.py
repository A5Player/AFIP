"""Production Milestone C Pack 14 research platform runtime entrypoint."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from afip.research import ResearchPlatformRuntime, ResearchSample


def sample_research_records() -> list[ResearchSample]:
    base = datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc)
    records: list[ResearchSample] = []
    for index, result in enumerate((12.0, 14.0, 10.0, -4.0, 16.0)):
        records.append(
            ResearchSample(
                observed_at=base + timedelta(hours=index),
                symbol="gold#",
                market_regime="trend",
                volatility_bucket="normal",
                direction="buy",
                signal_family="pullback continuation",
                confidence=72.0 + index,
                result_amount=result,
                execution_cost_points=24.0,
                holding_minutes=40.0 + index,
                source="pack 14 deterministic sample",
            )
        )
    for index, result in enumerate((-6.0, 5.0, -3.0)):
        records.append(
            ResearchSample(
                observed_at=base + timedelta(hours=10 + index),
                symbol="gold#",
                market_regime="range",
                volatility_bucket="high",
                direction="sell",
                signal_family="mean reversion",
                confidence=61.0 + index,
                result_amount=result,
                execution_cost_points=52.0,
                holding_minutes=25.0 + index,
                source="pack 14 deterministic sample",
            )
        )
    return records


def run_dict() -> dict[str, object]:
    return ResearchPlatformRuntime().run(sample_research_records()).as_dict()
