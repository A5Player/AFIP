from types import SimpleNamespace

from afip.automatic_research_runtime.runtime import AutomaticResearchRuntime, _TIMEFRAMES


def test_backfill_selection_excludes_expected_market_closures(tmp_path):
    expected = SimpleNamespace(
        backfill_eligible=True,
        unexpected_missing_bar_count=0,
        missing_bar_count=61,
    )
    unresolved = SimpleNamespace(
        backfill_eligible=True,
        unexpected_missing_bar_count=2,
        missing_bar_count=2,
    )
    ineligible = SimpleNamespace(
        backfill_eligible=False,
        unexpected_missing_bar_count=3,
        missing_bar_count=3,
    )
    quality = {
        timeframe: SimpleNamespace(gaps=())
        for timeframe in _TIMEFRAMES
    }
    quality[_TIMEFRAMES[0]] = SimpleNamespace(gaps=(expected, unresolved, ineligible))

    selected = AutomaticResearchRuntime(tmp_path)._unexpected_backfill_gaps(quality)

    assert selected == (unresolved,)


def test_legacy_gap_without_unexpected_counter_remains_backfill_compatible(tmp_path):
    legacy_unresolved = SimpleNamespace(backfill_eligible=True, missing_bar_count=1)
    quality = {
        timeframe: SimpleNamespace(gaps=())
        for timeframe in _TIMEFRAMES
    }
    quality[_TIMEFRAMES[0]] = SimpleNamespace(gaps=(legacy_unresolved,))

    selected = AutomaticResearchRuntime(tmp_path)._unexpected_backfill_gaps(quality)

    assert selected == (legacy_unresolved,)
