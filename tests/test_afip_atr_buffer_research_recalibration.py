from datetime import datetime, timezone
import json
from pathlib import Path

from afip.automatic_research_runtime import AutomaticResearchRuntime
from afip.historical_data_manager import TimeframeDataQuality
from afip.research_standardization import (
    ATRBufferCandidate,
    ATRBufferCandidateGrid,
    ATRBufferPatternObservation,
    ATRBufferResearchRanker,
    ATRBufferRecalibrationPolicy,
    ATRBufferResearchStandard,
    ATRBufferStandardRecalibrator,
    PatternResearchIdentity,
    PatternShapeSignature,
)
from afip.final_integration.runtime import FinalIntegrationRuntime
from afip.strategy_intelligence import StrategyIntelligenceEngine, StrategyTemplate


def bar(timeframe: str, timestamp: str) -> dict[str, object]:
    return {
        "timeframe": timeframe,
        "timestamp_utc": timestamp,
        "open": 100.0,
        "high": 101.0,
        "low": 99.0,
        "close": 100.0,
    }


def test_weekend_closure_is_not_an_unexpected_h4_gap() -> None:
    evidence = TimeframeDataQuality().evaluate(
        [bar("H4", "2026-07-24T20:00:00Z"), bar("H4", "2026-07-27T00:00:00Z")],
        now_utc=datetime(2026, 7, 27, tzinfo=timezone.utc),
    )["H4"]
    assert evidence.gap_count == 1
    assert evidence.missing_bars == 12
    assert evidence.expected_closure_gap_count == 1
    assert evidence.unexpected_gap_count == 0
    assert evidence.integrity_status == "PASS"
    assert evidence.gaps[0].classification == "EXPECTED_MARKET_CLOSURE"
    assert evidence.gaps[0].backfill_eligible is False


def test_weekday_gap_remains_backfill_eligible() -> None:
    engine = TimeframeDataQuality()
    original = [bar("H1", "2026-07-27T00:00:00Z"), bar("H1", "2026-07-27T03:00:00Z")]
    evidence = engine.evaluate(original, now_utc=datetime(2026, 7, 27, 4, tzinfo=timezone.utc))["H1"]
    assert evidence.unexpected_missing_bars == 2
    assert evidence.integrity_status == "REVIEW"
    assert evidence.gaps[0].classification == "UNEXPECTED_DATA_GAP"
    calls: list[str] = []

    def provider(gap):
        calls.append(gap.classification)
        return [bar("H1", "2026-07-27T01:00:00Z"), bar("H1", "2026-07-27T02:00:00Z")]

    result = engine.backfill(original, {"H1": evidence}, provider)
    assert calls == ["UNEXPECTED_DATA_GAP"]
    assert result.accepted_bars == 2


def test_configured_holiday_is_expected_and_preserved_as_evidence() -> None:
    engine = TimeframeDataQuality(expected_closure_dates=("2026-12-25",))
    evidence = engine.evaluate(
        [bar("D1", "2026-12-24T00:00:00Z"), bar("D1", "2026-12-26T00:00:00Z")],
        now_utc=datetime(2026, 12, 26, tzinfo=timezone.utc),
    )["D1"]
    assert evidence.expected_closure_bars == 1
    assert evidence.unexpected_missing_bars == 0
    assert "CONFIGURED_MARKET_CLOSURE" in evidence.gaps[0].reason_codes


def test_research_segments_split_only_at_unexpected_gap() -> None:
    engine = TimeframeDataQuality()
    rows = [
        bar("H1", "2026-07-24T23:00:00Z"),
        bar("H1", "2026-07-27T00:00:00Z"),
        bar("H1", "2026-07-27T03:00:00Z"),
    ]
    evidence = engine.evaluate(rows, now_utc=datetime(2026, 7, 27, 4, tzinfo=timezone.utc))["H1"]
    segments = engine.research_segments(rows, evidence)
    assert tuple(len(segment) for segment in segments) == (2, 1)


def test_automatic_replay_resets_features_at_unexpected_gap(tmp_path: Path) -> None:
    source = tmp_path / "data" / "historical"
    source.mkdir(parents=True)
    rows = [
        bar("H1", "2026-07-27T00:00:00Z"),
        bar("H1", "2026-07-27T01:00:00Z"),
        bar("H1", "2026-07-27T04:00:00Z"),
    ]
    (source / "h1.json").write_text(json.dumps(rows), encoding="utf-8")
    summary = AutomaticResearchRuntime(tmp_path).run(
        collect_mt5_when_needed=False,
        maximum_replay_bars=10,
    )
    assert summary.unexpected_gap_ranges_detected == 1
    snapshots = (
        tmp_path / "runtime" / "research" / "automatic" / "schema_v2" / "snapshots.jsonl"
    ).read_text(encoding="utf-8").splitlines()
    last = json.loads(snapshots[-1])["record"]["market_snapshot"]
    assert last["quality_segment_start_utc"] == "2026-07-27T04:00:00Z"
    assert last["quality_segment_bar_count"] == 1
    assert last["unexpected_gap_boundary_respected"] is True


def test_grid_enumerates_every_configured_point_unit_lazily() -> None:
    grid = ATRBufferCandidateGrid(0, 2, unit_step_points=1)
    candidates = tuple(grid.iter_candidates())
    assert grid.candidate_count == 18
    assert len(candidates) == 18
    assert {item.sl_buffer_points for item in candidates} == {0, 1, 2}
    assert {item.tp_buffer_points for item in candidates} == {0, 1, 2}
    assert {item.tp_operator for item in candidates} == {"PLUS", "MINUS"}
    assert tuple(len(chunk) for chunk in grid.iter_candidate_chunks(7)) == (7, 7, 4)


def test_candidate_resolves_atr_plus_and_minus_buffer() -> None:
    candidate = ATRBufferCandidate(1.0, 50, "PLUS", 1.0, 25, "MINUS")
    assert candidate.resolve(700.0) == (750.0, 675.0)


def identity(name: str = "BULLISH_PULLBACK", regime: str = "TRENDING") -> PatternResearchIdentity:
    return PatternResearchIdentity(
        symbol="GOLD#", timeframe="H1", pattern_family="TREND_CONTINUATION",
        pattern_name=name, pattern_variant="FIRST_PULLBACK", direction="BUY",
        market_regime=regime, trend_state="UP", momentum_state="RECOVERING",
        volatility_state="NORMAL", trading_session="LONDON",
        liquidity_state="NORMAL", multi_timeframe_context="H4_UP_D1_UP",
        entry_plan="ENTER_ON_PULLBACK_CONFIRMATION",
        management_plan="ATR_BUFFER_POSITION_CARE",
        exit_plan="ATR_BUFFER_EXIT",
    )


def shape(candles: int = 3, upper_wick: float = 0.15) -> PatternShapeSignature:
    return PatternShapeSignature(
        candle_count=candles, duration_seconds=candles * 3600,
        average_body_ratio=0.60, upper_wick_ratio=upper_wick,
        lower_wick_ratio=0.20, pullback_depth_atr=0.60,
        total_range_atr=1.10, slope_strength=0.75,
    )


def observations(
    patterns: int = 3,
    research_identity: PatternResearchIdentity | None = None,
    shape_signature: PatternShapeSignature | None = None,
):
    strong = ATRBufferCandidate(1.0, 50, "PLUS", 1.0, 100, "PLUS")
    weak = ATRBufferCandidate(1.0, 100, "PLUS", 1.0, 50, "MINUS")
    research_identity = research_identity or identity()
    shape_signature = shape_signature or shape()
    rows = []
    for sequence in range(1, patterns + 1):
        rows.append(ATRBufferPatternObservation(
            f"P{sequence}", sequence, "GOLD|H1|TRENDING", strong,
            100.0, "WIN", research_identity=research_identity,
            shape_signature=shape_signature,
            cross_market_context_id=f"XMARKET-{sequence}",
        ))
        rows.append(ATRBufferPatternObservation(
            f"P{sequence}", sequence, "GOLD|H1|TRENDING", weak,
            -40.0 if sequence > 1 else 20.0, "LOSS" if sequence > 1 else "WIN",
            research_identity=research_identity,
            shape_signature=shape_signature,
            cross_market_context_id=f"XMARKET-{sequence}",
        ))
    return strong, weak, tuple(rows)


def test_default_recalibration_boundary_is_exactly_1000_patterns() -> None:
    policy = ATRBufferRecalibrationPolicy()
    assert policy.pattern_batch_size == 1000
    assert policy.minimum_candidate_samples == 1000
    assert policy.cumulative_history_recalibration is True
    assert policy.incremental_cumulative_merge is True


def test_incomplete_pattern_batch_does_not_update_standard() -> None:
    strong, weak, rows = observations(2)
    result = ATRBufferStandardRecalibrator(
        policy=ATRBufferRecalibrationPolicy(3, 3)
    ).evaluate(rows, expected_candidate_ids=(strong.candidate_id, weak.candidate_id))
    assert result[0].status == "WAITING"
    assert result[0].standard is None


def test_complete_batch_selects_strongest_win_probability_standard(tmp_path: Path) -> None:
    strong, weak, rows = observations(3)
    result = ATRBufferStandardRecalibrator(
        str(tmp_path), ATRBufferRecalibrationPolicy(3, 3)
    ).evaluate(rows, expected_candidate_ids=(strong.candidate_id, weak.candidate_id))
    evaluation = result[0]
    assert evaluation.status == "RESEARCH_STANDARD_UPDATED"
    assert evaluation.standard is not None
    assert evaluation.standard.selected_candidate == strong
    assert evaluation.standard.pattern_count == 3
    assert evaluation.standard.production_usable is False
    assert evaluation.standard.automatic_production_promotion_allowed is False
    assert evaluation.standard.execution_authority == "NONE"
    assert (tmp_path / "atr_buffer_batch_evaluations.jsonl").exists()
    assert (tmp_path / "atr_buffer_research_standards.jsonl").exists()


def test_each_milestone_recomputes_from_all_cumulative_pattern_history() -> None:
    strong, weak, rows = observations(6)
    result = ATRBufferStandardRecalibrator(
        policy=ATRBufferRecalibrationPolicy(3, 3)
    ).evaluate(rows, expected_candidate_ids=(strong.candidate_id, weak.candidate_id))

    updated = [item for item in result if item.status == "RESEARCH_STANDARD_UPDATED"]
    assert [item.batch_number for item in updated] == [1, 2]
    assert [item.pattern_count for item in updated] == [3, 6]
    assert [item.standard.pattern_count for item in updated if item.standard] == [3, 6]
    assert updated[1].reason == "incremental_1000_merged_into_cumulative_standard"
    assert updated[1].standard is not None
    assert updated[1].standard.standard_version.endswith("P000000000006")
    assert updated[0].standard is not None
    assert updated[0].standard.net_points == 300.0
    assert updated[1].standard.net_points == 600.0


def test_new_recalibrator_processes_only_new_1000_and_loads_prior_aggregate(tmp_path: Path) -> None:
    strong, weak, first_rows = observations(3)
    first = ATRBufferStandardRecalibrator(
        str(tmp_path), ATRBufferRecalibrationPolicy(3, 3)
    ).evaluate(first_rows, expected_candidate_ids=(strong.candidate_id, weak.candidate_id))
    assert first[0].standard is not None
    assert first[0].standard.pattern_count == 3

    _, _, all_rows = observations(6)
    only_new_rows = tuple(item for item in all_rows if item.pattern_sequence > 3)
    second = ATRBufferStandardRecalibrator(
        str(tmp_path), ATRBufferRecalibrationPolicy(3, 3)
    ).evaluate(only_new_rows, expected_candidate_ids=(strong.candidate_id, weak.candidate_id))

    updated = [item for item in second if item.status == "RESEARCH_STANDARD_UPDATED"]
    assert len(updated) == 1
    assert updated[0].standard is not None
    assert updated[0].standard.pattern_count == 6
    assert updated[0].standard.net_points == 600.0
    assert (tmp_path / "atr_buffer_cumulative_aggregates.jsonl").exists()


def test_missing_candidate_grid_is_quarantined() -> None:
    strong, weak, rows = observations(3)
    missing = ATRBufferCandidate(1.0, 1, "PLUS", 1.0, 1, "PLUS")
    result = ATRBufferStandardRecalibrator(
        policy=ATRBufferRecalibrationPolicy(3, 3)
    ).evaluate(
        rows,
        expected_candidate_ids=(strong.candidate_id, weak.candidate_id, missing.candidate_id),
    )
    assert result[0].status == "QUARANTINED"
    assert result[0].reason == "candidate_grid_coverage_incomplete"


def test_different_named_chart_patterns_never_share_one_recalibration_batch() -> None:
    strong, weak, pullbacks = observations(3, identity("BULLISH_PULLBACK"))
    _, _, breakouts = observations(3, identity("BULLISH_BREAKOUT"))
    result = ATRBufferStandardRecalibrator(
        policy=ATRBufferRecalibrationPolicy(3, 3)
    ).evaluate(
        (*pullbacks, *breakouts),
        expected_candidate_ids=(strong.candidate_id, weak.candidate_id),
    )
    assert len(result) == 2
    assert {item.standard.pattern_identity.pattern_name for item in result if item.standard} == {
        "BULLISH_PULLBACK", "BULLISH_BREAKOUT",
    }
    assert len({item.research_key for item in result}) == 2


def test_missing_exact_pattern_identity_is_quarantined() -> None:
    strong = ATRBufferCandidate(1.0, 50, "PLUS", 1.0, 100, "PLUS")
    rows = tuple(
        ATRBufferPatternObservation(
            f"LEGACY-{sequence}", sequence, "LEGACY", strong, 1.0, "WIN",
            cross_market_context_id=f"X-{sequence}",
        )
        for sequence in range(1, 4)
    )
    result = ATRBufferStandardRecalibrator(
        policy=ATRBufferRecalibrationPolicy(3, 3)
    ).evaluate(rows, expected_candidate_ids=(strong.candidate_id,))
    assert result[0].status == "QUARANTINED"
    assert result[0].reason == "exact_pattern_research_identity_required"


def test_ranker_excludes_unlike_graph_and_uses_cross_market_as_separate_rank_dimension() -> None:
    candidate = ATRBufferCandidate(1.0, 50, "PLUS", 1.0, 100, "PLUS")
    current = identity("BULLISH_PULLBACK")
    same_a = ATRBufferResearchStandard(
        "STD-A", "1", "SEG-A", 1, 1000, candidate, 70, 60, 20, 20000,
        research_key=current.research_key, pattern_identity=current,
        shape_signature=shape(), shape_bucket_key=shape().bucket_key,
        cross_market_context_ids=("OLD-A",),
    )
    same_b = ATRBufferResearchStandard(
        "STD-B", "1", "SEG-B", 1, 1000, candidate, 70, 60, 20, 20000,
        research_key=current.research_key, pattern_identity=current,
        shape_signature=shape(), shape_bucket_key=shape().bucket_key,
        cross_market_context_ids=("OLD-B",),
    )
    unlike = identity("BEARISH_REVERSAL")
    other = ATRBufferResearchStandard(
        "STD-X", "1", "SEG-X", 1, 1000, candidate, 99, 95, 50, 50000,
        research_key=unlike.research_key, pattern_identity=unlike,
        shape_signature=shape(), shape_bucket_key=shape().bucket_key,
        cross_market_context_ids=("OLD-X",),
    )
    ranked = ATRBufferResearchRanker().rank(
        current, (same_a, same_b, other),
        current_shape_signature=shape(),
        current_cross_market_context_id="NOW",
        cross_market_similarity_by_standard={"STD-A": 70, "STD-B": 90, "STD-X": 100},
    )
    assert [item.standard_id for item in ranked] == ["STD-B", "STD-A"]
    assert all(item.graph_key == current.graph_key for item in ranked)
    assert all(item.execution_authority == "NONE" for item in ranked)


def test_same_named_pattern_with_different_length_or_wicks_has_different_shape_partition() -> None:
    short = shape(3, 0.15)
    long_wick = shape(12, 0.75)
    assert short.bucket_key != long_wick.bucket_key
    _, _, short_rows = observations(3, identity(), short)
    _, _, long_rows = observations(3, identity(), long_wick)
    result = ATRBufferStandardRecalibrator(
        policy=ATRBufferRecalibrationPolicy(3, 3)
    ).evaluate((*short_rows, *long_rows))
    assert len(result) == 2
    assert len({item.research_key for item in result}) == 2


def test_hierarchical_evidence_contains_family_and_exact_shape_scores() -> None:
    candidate = ATRBufferCandidate(1.0, 50, "PLUS", 1.0, 100, "PLUS")
    current = identity()
    current_shape = shape()
    standard = ATRBufferResearchStandard(
        "STD-H", "1", "SEG", 1, 1000, candidate, 90, 85, 20, 20000,
        research_key=f"{current.research_key}|{current_shape.bucket_key}",
        pattern_identity=current, shape_signature=current_shape,
        shape_bucket_key=current_shape.bucket_key,
        cross_market_context_ids=("OLD",),
    )
    evidence = ATRBufferResearchRanker().hierarchical_evidence(
        current, current_shape, (standard,),
        current_cross_market_context_id="NOW",
        cross_market_similarity_by_standard={"STD-H": 92},
    )
    assert evidence["research_scope"] == "HIERARCHICAL_FAMILY_AND_EXACT_SHAPE"
    assert evidence["family_research_score"] == 85
    assert evidence["exact_shape_research_score"] == 85
    assert evidence["hierarchical_research_ready"] is True


def test_low_exact_shape_research_fails_closed_before_plan_review() -> None:
    template = StrategyTemplate(
        "PULLBACK", "CONTINUATION", ("TREND_CONTINUATION",), ("TRENDING",),
        minimum_similarity=80, minimum_sample_size=30,
    )
    base = {
        "historical_context_id": "CTX",
        "similarity_score": 95,
        "sample_size": 1000,
        "evidence_quality": "HIGH",
        "outcome": "WIN",
        "metadata": {
            "historical_expectancy": 2.0,
            "historical_win_rate": 90,
            "pattern_family": "TREND_CONTINUATION",
            "market_regime": "TRENDING",
            "research_scope": "HIERARCHICAL_FAMILY_AND_EXACT_SHAPE",
            "hierarchical_research_ready": True,
            "family_research_score": 90,
            "exact_shape_research_score": 60,
            "shape_similarity_score": 95,
        },
    }
    result = StrategyIntelligenceEngine(1, 30).evaluate(template, (base,))
    assert result.status == "WAIT"
    assert result.reasons[0] == "insufficient_evidence_count"
    assert result.execution_authority is False


def test_research_can_pause_and_resume_independently(monkeypatch, tmp_path: Path) -> None:
    runtime = FinalIntegrationRuntime(tmp_path)
    runtime._write_desired_state("RUNNING", "test", research_state="RUNNING")
    monkeypatch.setattr(runtime, "_terminate_service", lambda *args: None)
    monkeypatch.setattr(runtime, "_spawn", lambda *args: True)
    monkeypatch.setattr(runtime, "_trading", lambda command: {"status": "READY", "profiles": []})
    monkeypatch.setattr(runtime, "_service_running", lambda *args: False)
    paused = runtime.pause_research().as_dict()
    assert paused["research_runtime"]["process_state"] == "PAUSED"
    assert runtime._desired_state() == "RUNNING"
    assert runtime._desired_research_state() == "PAUSED"
    resumed = runtime.resume_research().as_dict()
    assert runtime._desired_state() == "RUNNING"
    assert runtime._desired_research_state() == "RUNNING"
    assert resumed["research_runtime"]["desired_state"] == "RUNNING"
