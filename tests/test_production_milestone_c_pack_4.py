from datetime import datetime, timedelta, timezone

from afip.macro.dxy_runtime import DxyRuntime
from afip.macro.gold_market_bias_engine import GoldMarketBiasEngine
from afip.macro.market_factor_cache import MarketFactorCache
from afip.macro.market_factor_provider import EmptyMarketFactorProvider, StaticMarketFactorProvider
from afip.macro.macro_market_factor_runtime import MacroMarketFactorRuntime
from afip.macro.real_yield_runtime import RealYieldRuntime
from afip.macro.treasury_yield_runtime import TreasuryYieldRuntime
from afip.research.market_signature import MarketSignatureEngine
from afip.runtime.production_milestone_c_market_factor_runtime import ProductionMilestoneCMarketFactorRuntime


def test_static_market_factor_provider_returns_deterministic_factors():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    provider = StaticMarketFactorProvider({"dxy_change_percent": -0.42, "us10y_change_bps": -7})

    result = provider.fetch_factors(now)

    assert result.status == "MARKET_FACTOR_PROVIDER_READY"
    assert result.source == "STATIC_FREE_MARKET_FACTORS"
    assert result.factors["dxy_change_percent"] == -0.42


def test_empty_market_factor_provider_is_safe_fallback():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    result = EmptyMarketFactorProvider().fetch_factors(now)

    assert result.status == "MARKET_FACTOR_PROVIDER_EMPTY"
    assert result.factors == {}
    assert result.reason == "no_market_factor_provider_configured"


def test_market_factor_cache_returns_recent_result_before_expiry():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    result = StaticMarketFactorProvider({"dxy_change_percent": -0.3}).fetch_factors(now)
    cache = MarketFactorCache(ttl_seconds=120)

    cache.set(result, now)

    assert cache.get(now + timedelta(seconds=60)) is result
    assert cache.state(now + timedelta(seconds=60)).status == "MARKET_FACTOR_CACHE_READY"


def test_market_factor_cache_expires_old_result():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    result = StaticMarketFactorProvider({"dxy_change_percent": -0.3}).fetch_factors(now)
    cache = MarketFactorCache(ttl_seconds=30)

    cache.set(result, now)

    assert cache.get(now + timedelta(seconds=45)) is None
    assert cache.state(now + timedelta(seconds=45)).status == "MARKET_FACTOR_CACHE_EXPIRED"


def test_dxy_runtime_scores_dollar_softness_as_gold_supportive():
    assessment = DxyRuntime().assess({"dxy_change_percent": -0.35, "dxy_momentum_percent": -0.40})

    assert assessment.status == "DXY_READY"
    assert assessment.direction == "GOLD_SUPPORTIVE"
    assert assessment.pressure_score >= 80


def test_treasury_yield_runtime_scores_higher_yields_as_gold_pressure():
    assessment = TreasuryYieldRuntime().assess({"us02y_change_bps": 3, "us10y_change_bps": 8})

    assert assessment.status == "TREASURY_YIELD_READY"
    assert assessment.direction == "GOLD_PRESSURE"
    assert assessment.curve_change_bps == 5


def test_real_yield_runtime_estimates_change_when_explicit_value_missing():
    assessment = RealYieldRuntime().assess(
        {
            "us10y_change_bps": -6,
            "inflation_expectation_change_bps": 1,
            "us10y_yield_percent": 4.2,
            "inflation_expectation_percent": 2.4,
        }
    )

    assert assessment.direction == "GOLD_SUPPORTIVE"
    assert assessment.real_yield_change_bps == -7
    assert assessment.estimated_real_yield_percent == 1.8


def test_gold_market_bias_engine_aggregates_supportive_macro_factors():
    dxy = DxyRuntime().assess({"dxy_change_percent": -0.45})
    treasury = TreasuryYieldRuntime().assess({"us10y_change_bps": -8})
    real_yield = RealYieldRuntime().assess({"real_yield_change_bps": -5})

    bias = GoldMarketBiasEngine().evaluate(dxy, treasury, real_yield)

    assert bias.status == "GOLD_MARKET_BIAS_READY"
    assert bias.bias == "GOLD_SUPPORTIVE"
    assert bias.supportive_count == 3
    assert bias.score > 60


def test_macro_market_factor_runtime_builds_ready_state_from_provider():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    provider = StaticMarketFactorProvider(
        {
            "dxy_change_percent": -0.5,
            "us10y_change_bps": -7,
            "us02y_change_bps": -3,
            "real_yield_change_bps": -4,
        }
    )

    result = MacroMarketFactorRuntime(provider=provider).run(now)

    assert result.status == "MACRO_MARKET_FACTOR_READY"
    assert result.gold_market_bias["bias"] == "GOLD_SUPPORTIVE"
    assert result.source == "STATIC_FREE_MARKET_FACTORS"


def test_market_signature_engine_compacts_repeated_market_conditions():
    engine = MarketSignatureEngine()
    first = engine.build({"dxy": "GOLD_SUPPORTIVE", "real_yield_change_bps": -4.2, "session": "London"})
    second = engine.build({"session": "London", "real_yield_change_bps": -4.1, "dxy": "GOLD_SUPPORTIVE"})

    assert first.status == "MARKET_SIGNATURE_READY"
    assert first.signature_id == second.signature_id
    assert first.components["real_yield_change_bps"] == "DOWN"


def test_production_milestone_c_market_factor_runtime_includes_signature():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    runtime = ProductionMilestoneCMarketFactorRuntime()

    result = runtime.run(
        now,
        {
            "dxy_change_percent": 0.45,
            "us10y_change_bps": 7,
            "real_yield_change_bps": 4,
        },
    )

    assert result["package"] == "Production Milestone C Pack 4"
    assert result["status"] == "MACRO_MARKET_FACTOR_READY"
    assert result["gold_market_bias"]["bias"] == "GOLD_PRESSURE"
    assert result["market_signature"]["status"] == "MARKET_SIGNATURE_READY"
