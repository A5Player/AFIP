from __future__ import annotations

from datetime import datetime, timedelta, timezone

from afip.knowledge.knowledge_quality import KnowledgeQualityEngine
from afip.knowledge.knowledge_runtime import MarketKnowledgeRuntime
from afip.knowledge.market_knowledge_repository import MarketKnowledgeRepository
from afip.knowledge.market_pattern_repository import MarketPatternRepository
from afip.knowledge.market_snapshot_repository import MarketSnapshotRepository
from afip.knowledge.market_statistics_repository import RunningMarketStatistics
from afip.research.market_signature import MarketSignatureEngine
from afip.runtime.production_milestone_c_knowledge_runtime import ProductionMilestoneCMarketKnowledgeRuntime


NOW = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)


def _market_state() -> dict[str, object]:
    return {
        "session": "London",
        "market_regime": "TREND",
        "gold_market_bias": "GOLD_SUPPORTIVE",
        "event_risk_state": "CLEAR",
        "volatility_group": "NORMAL",
        "dxy_change_pct": -0.4,
        "us10y_change_bps": -5.0,
        "real_yield_change_bps": -6.0,
    }


def test_running_market_statistics_updates_compact_outcomes() -> None:
    stats = RunningMarketStatistics()
    stats.update(result_amount=12.0, holding_minutes=18, mae=3, mfe=15)
    stats.update(result_amount=-4.0, holding_minutes=7, mae=6, mfe=2)

    assert stats.observations == 2
    assert stats.win_rate == 50.0
    assert stats.expectancy == 4.0
    assert stats.average_holding_minutes == 12.5
    assert stats.average_mae == 4.5
    assert stats.average_mfe == 8.5


def test_market_knowledge_repository_counts_repeated_signature_once() -> None:
    signature = MarketSignatureEngine().build(_market_state()).as_dict()
    repository = MarketKnowledgeRepository()
    repository.observe(signature=signature, result_amount=10.0, observed_at=NOW)
    repository.observe(signature=signature, result_amount=5.0, observed_at=NOW + timedelta(minutes=5))

    summary = repository.summary()
    assert summary["unique_signatures"] == 1
    assert summary["total_observations"] == 2
    assert summary["compression_ratio"] == 2.0


def test_market_knowledge_repository_preserves_statistics() -> None:
    signature = MarketSignatureEngine().build(_market_state()).as_dict()
    repository = MarketKnowledgeRepository()
    record = repository.observe(signature=signature, result_amount=10.0, holding_minutes=20, mae=2, mfe=12, observed_at=NOW)

    assert record.as_dict()["statistics"]["win_rate"] == 100.0
    assert record.as_dict()["statistics"]["expectancy"] == 10.0


def test_market_pattern_repository_uses_normalized_pattern_key() -> None:
    repository = MarketPatternRepository()
    one = repository.observe({"session": "London", "market_regime": "Trend"}, result_amount=4)
    two = repository.observe({"market_regime": "TREND", "session": "LONDON"}, result_amount=6)

    assert one.pattern_key == two.pattern_key
    assert repository.summary()["unique_patterns"] == 1
    assert repository.summary()["total_observations"] == 2


def test_market_pattern_repository_ranks_by_expectancy() -> None:
    repository = MarketPatternRepository()
    repository.observe({"session": "Asia"}, result_amount=1)
    repository.observe({"session": "London"}, result_amount=12)

    top = repository.top_by_expectancy(limit=1)
    assert top[0].attributes["session"] == "LONDON"


def test_market_snapshot_repository_skips_unimportant_streaming_stage() -> None:
    repository = MarketSnapshotRepository()
    skipped = repository.store(stage="STREAM", signature_id="ABC", data={}, observed_at=NOW)
    stored = repository.store(stage="PRE_ENTRY", signature_id="ABC", data={"price": 2400}, observed_at=NOW)

    assert skipped is None
    assert stored is not None
    assert repository.summary()["stored_snapshots"] == 1


def test_market_snapshot_repository_keeps_recent_window() -> None:
    repository = MarketSnapshotRepository(max_snapshots=2)
    repository.store(stage="DAILY_REVIEW", signature_id="A", data={}, observed_at=NOW)
    repository.store(stage="DAILY_REVIEW", signature_id="B", data={}, observed_at=NOW + timedelta(minutes=1))
    repository.store(stage="DAILY_REVIEW", signature_id="C", data={}, observed_at=NOW + timedelta(minutes=2))

    recent = repository.list_recent(limit=5)
    assert len(recent) == 2
    assert recent[0].signature_id == "B"
    assert recent[1].signature_id == "C"


def test_knowledge_quality_observe_only_for_small_samples() -> None:
    record = {
        "occurrence_count": 3,
        "statistics": {"expectancy": 8.0, "result_std": 2.0},
        "last_seen": NOW.isoformat(),
    }

    quality = KnowledgeQualityEngine().assess_dict(record, now=NOW)
    assert quality["usability"] == "OBSERVE_ONLY"
    assert quality["sample_confidence"] == 12.0


def test_knowledge_quality_ready_for_large_fresh_stable_sample() -> None:
    record = {
        "occurrence_count": 30,
        "statistics": {"expectancy": 8.0, "result_std": 2.0},
        "last_seen": NOW.isoformat(),
    }

    quality = KnowledgeQualityEngine().assess_dict(record, now=NOW)
    assert quality["usability"] == "DECISION_SUPPORT_READY"
    assert quality["quality_score"] >= 75.0


def test_market_knowledge_runtime_builds_signature_record_pattern_and_snapshot() -> None:
    runtime = MarketKnowledgeRuntime()
    state = runtime.observe_dict(
        market_state=_market_state(),
        result_amount=10.0,
        holding_minutes=22,
        mae=3,
        mfe=14,
        stage="PRE_ENTRY",
        observed_at=NOW,
    )

    assert state["status"] == "MARKET_KNOWLEDGE_RUNTIME_READY"
    assert state["signature"]["status"] == "MARKET_SIGNATURE_READY"
    assert state["knowledge_record"]["occurrence_count"] == 1
    assert state["pattern_record"]["occurrence_count"] == 1
    assert state["snapshot"]["stage"] == "PRE_ENTRY"


def test_production_milestone_c_knowledge_runtime_aggregates_observations() -> None:
    runtime = ProductionMilestoneCMarketKnowledgeRuntime()
    observations = [
        {"market_state": _market_state(), "result_amount": 10.0, "holding_minutes": 20, "mae": 2, "mfe": 12},
        {"market_state": _market_state(), "result_amount": -4.0, "holding_minutes": 8, "mae": 5, "mfe": 3},
    ]

    state = runtime.run_dict(observations, now=NOW)

    assert state["status"] == "PRODUCTION_MILESTONE_C_KNOWLEDGE_RUNTIME_READY"
    assert state["processed_observations"] == 2
    assert state["repository_summary"]["unique_signatures"] == 1
    assert state["repository_summary"]["total_observations"] == 2
    assert state["pattern_summary"]["unique_patterns"] == 1
