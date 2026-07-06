from datetime import datetime, timedelta, timezone

from afip.macro.news_cache import MacroNewsCache
from afip.macro.news_confidence_engine import MacroNewsConfidenceEngine
from afip.macro.news_impact_engine import MacroNewsImpactEngine
from afip.macro.news_provider import CombinedMacroNewsProvider, EmptyMacroNewsProvider, StaticMacroNewsProvider
from afip.runtime.production_milestone_c_news_runtime import ProductionMilestoneCNewsRuntime


def test_static_news_provider_returns_deterministic_articles():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    provider = StaticMacroNewsProvider([
        {"title": "Fed signals dovish rate outlook", "source": "FED", "topic": "FED", "published_at": now.isoformat()}
    ])

    result = provider.fetch_news(now)

    assert result.status == "NEWS_PROVIDER_READY"
    assert result.source == "STATIC_FREE_NEWS"
    assert len(result.articles) == 1
    assert result.articles[0]["topic"] == "FED"


def test_empty_news_provider_is_safe_fallback():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    result = EmptyMacroNewsProvider().fetch_news(now)

    assert result.status == "NEWS_PROVIDER_EMPTY"
    assert result.articles == ()
    assert result.reason == "no_news_provider_configured"


def test_combined_news_provider_merges_sources():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    first = StaticMacroNewsProvider([{"title": "CPI inflation cool", "topic": "CPI", "published_at": now.isoformat()}], source="BLS")
    second = StaticMacroNewsProvider([{"title": "Treasury yield lower", "topic": "TREASURY_YIELD", "published_at": now.isoformat()}], source="TREASURY")

    result = CombinedMacroNewsProvider([first, second]).fetch_news(now)

    assert result.status == "NEWS_PROVIDER_READY"
    assert len(result.articles) == 2
    assert "BLS" in result.reason


def test_news_cache_returns_recent_result_before_expiry():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    result = StaticMacroNewsProvider([]).fetch_news(now)
    cache = MacroNewsCache(ttl_seconds=120)

    cache.set(result, now)

    assert cache.get(now + timedelta(seconds=60)) is result
    assert cache.state(now + timedelta(seconds=60)).status == "NEWS_CACHE_READY"


def test_news_cache_expires_old_result():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    result = StaticMacroNewsProvider([]).fetch_news(now)
    cache = MacroNewsCache(ttl_seconds=30)

    cache.set(result, now)

    assert cache.get(now + timedelta(seconds=45)) is None
    assert cache.state(now + timedelta(seconds=45)).status == "NEWS_CACHE_EXPIRED"


def test_news_impact_engine_scores_fed_article_as_high_impact():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    impact = MacroNewsImpactEngine().assess(
        {
            "title": "Fed signals dovish rate cut path as dollar fall supports gold",
            "source": "FED",
            "topic": "FED",
            "published_at": now.isoformat(),
        },
        now,
    )

    assert impact.direction == "GOLD_SUPPORTIVE"
    assert impact.impact_score >= 90
    assert impact.confidence_score >= 90


def test_news_impact_engine_detects_gold_pressure():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    impact = MacroNewsImpactEngine().assess(
        {
            "title": "Higher yield and dollar rise pressure gold",
            "source": "TREASURY",
            "topic": "TREASURY_YIELD",
            "published_at": now.isoformat(),
        },
        now,
    )

    assert impact.direction == "GOLD_PRESSURE"
    assert impact.impact_score >= 80


def test_news_confidence_engine_aggregates_supportive_bias():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    engine = MacroNewsImpactEngine()
    impacts = [
        engine.assess({"title": "DXY down after inflation cool", "topic": "CPI", "source": "BLS", "published_at": now.isoformat()}, now),
        engine.assess({"title": "Lower yield supports gold", "topic": "REAL_YIELD", "source": "TREASURY", "published_at": now.isoformat()}, now),
    ]

    confidence = MacroNewsConfidenceEngine().aggregate(impacts)

    assert confidence.status == "NEWS_CONFIDENCE_READY"
    assert confidence.gold_bias == "SUPPORTIVE"
    assert confidence.supportive_count == 2


def test_news_confidence_engine_routes_mixed_news_to_review():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    engine = MacroNewsImpactEngine()
    impacts = [
        engine.assess({"title": "DXY down supports gold", "topic": "DXY", "source": "STATIC_FREE_NEWS", "published_at": now.isoformat()}, now),
        engine.assess({"title": "Higher yield pressures gold", "topic": "TREASURY_YIELD", "source": "STATIC_FREE_NEWS", "published_at": now.isoformat()}, now),
    ]

    confidence = MacroNewsConfidenceEngine().aggregate(impacts)

    assert confidence.gold_bias == "MIXED"
    assert confidence.trade_instruction == "MACRO_REVIEW"


def test_production_milestone_c_news_runtime_builds_ready_state():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    runtime = ProductionMilestoneCNewsRuntime()

    state = runtime.run_dict(
        [
            {
                "title": "Inflation cool and lower yield supports gold",
                "source": "BLS",
                "topic": "CPI",
                "published_at": now.isoformat(),
            }
        ],
        now,
    )

    assert state["runtime"] == "PRODUCTION_MILESTONE_C_NEWS_RUNTIME"
    assert state["status"] == "NEWS_CONFIDENCE_READY"
    assert state["article_count"] == 1
    assert state["gold_bias"] == "SUPPORTIVE"


def test_production_milestone_c_news_runtime_is_deterministic():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    article = {"title": "Dollar rise pressures gold", "source": "STATIC_FREE_NEWS", "topic": "DXY", "published_at": now.isoformat()}
    runtime = ProductionMilestoneCNewsRuntime()

    first = runtime.run_dict([article], now)
    second = runtime.run_dict([article], now)

    assert first == second
    assert first["gold_bias"] == "PRESSURE"
