from types import SimpleNamespace

from afip.automatic_research_runtime.runtime import AutomaticResearchRuntime


def _gap(*, after, before, missing):
    return SimpleNamespace(
        timeframe="M30",
        after_timestamp_utc=after,
        before_timestamp_utc=before,
        unexpected_missing_bar_count=missing,
    )


def test_backfill_target_evidence_reports_partial_recovery():
    target = _gap(after="2026-01-01T00:00:00Z", before="2026-01-01T02:00:00Z", missing=3)
    remaining = _gap(after="2026-01-01T01:00:00Z", before="2026-01-01T02:00:00Z", missing=1)

    evidence = AutomaticResearchRuntime._backfill_target_evidence(
        (target,),
        ({"timeframe": "M30", "timestamp_utc": "2026-01-01T00:30:00Z"},),
        {"M30": SimpleNamespace(gaps=(remaining,))},
    )

    assert evidence[0]["outcome"] == "PARTIALLY_RESOLVED"
    assert evidence[0]["returned_bars_in_range"] == 1
    assert evidence[0]["missing_bars_recovered"] == 2


def test_backfill_target_evidence_reports_no_source_bars():
    target = _gap(after="2026-01-01T00:00:00Z", before="2026-01-01T01:00:00Z", missing=1)

    evidence = AutomaticResearchRuntime._backfill_target_evidence(
        (target,), (), {"M30": SimpleNamespace(gaps=(target,))},
    )

    assert evidence[0]["outcome"] == "NO_SOURCE_BARS_RETURNED"
    assert evidence[0]["unexpected_missing_bars_remaining"] == 1
