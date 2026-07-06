from afip.confidence_calibration import (
    ConfidenceCalibrationObservation,
    ConfidenceCalibrationPolicy,
    ConfidenceCalibrationProfile,
    ConfidenceCalibrationRepository,
    ConfidenceCalibrationRuntime,
)
from afip.runtime.production_milestone_e_confidence_calibration_runtime import (
    ProductionMilestoneEConfidenceCalibrationRuntime,
)


def _ready_observations():
    return [
        {
            "market_regime": "trend expansion",
            "confidence_bucket": "high confidence",
            "direction": "buy",
            "sample_count": 12,
            "raw_confidence_score": 72,
            "realized_accuracy_rate": 68,
            "calibration_error_score": 11,
            "confidence_stability_score": 74,
            "confidence_drift_score": 15,
            "execution_cost_score": 65,
            "trace_id": "cal-001",
        },
        {
            "regime": "TREND_EXPANSION",
            "bucket": "HIGH_CONFIDENCE",
            "bias": "BUY",
            "samples": 14,
            "raw_confidence": 76,
            "accuracy_rate": 70,
            "calibration_error": 9,
            "stability_score": 72,
            "drift_score": 17,
            "cost_score": 67,
            "trace": "cal-002",
        },
    ]


def test_confidence_calibration_observation_normalizes_market_regime_first_key():
    observation = ConfidenceCalibrationObservation.from_mapping(
        {
            "regime": "trend expansion",
            "bucket": "high confidence",
            "bias": "buy",
            "samples": 5,
            "raw_confidence": 70,
            "accuracy_rate": 66,
            "calibration_error": 12,
            "stability_score": 71,
            "drift_score": 16,
            "cost_score": 60,
            "trace": "cal-a",
        }
    )

    assert observation.market_regime == "TREND_EXPANSION"
    assert observation.regime_confidence_key == "TREND_EXPANSION:HIGH_CONFIDENCE:BUY"


def test_confidence_calibration_observation_blocks_missing_traceability():
    observation = ConfidenceCalibrationObservation.from_mapping(
        {
            "market_regime": "TREND_EXPANSION",
            "confidence_bucket": "HIGH_CONFIDENCE",
            "direction": "BUY",
            "sample_count": 5,
            "raw_confidence_score": 70,
            "realized_accuracy_rate": 66,
            "calibration_error_score": 12,
            "confidence_stability_score": 71,
            "confidence_drift_score": 16,
            "execution_cost_score": 60,
        }
    )

    assert observation.is_usable is False


def test_confidence_calibration_repository_groups_by_market_regime_before_bucket():
    repository = ConfidenceCalibrationRepository(
        _ready_observations()
        + [
            {
                "market_regime": "range compression",
                "confidence_bucket": "medium confidence",
                "direction": "sell",
                "sample_count": 25,
                "raw_confidence_score": 69,
                "realized_accuracy_rate": 72,
                "calibration_error_score": 8,
                "confidence_stability_score": 75,
                "confidence_drift_score": 12,
                "execution_cost_score": 70,
                "trace_id": "cal-003",
            }
        ]
    )

    keys = [profile.profile_key for profile in repository.build_profiles()]
    assert keys == ["RANGE_COMPRESSION:MEDIUM_CONFIDENCE:SELL", "TREND_EXPANSION:HIGH_CONFIDENCE:BUY"]


def test_confidence_calibration_profile_uses_data_derived_metrics():
    profile = ConfidenceCalibrationRepository(_ready_observations()).build_profiles()[0]

    assert profile.sample_count == 26
    assert profile.average_raw_confidence_score == 74.0
    assert profile.realized_accuracy_rate == 69.0
    assert profile.average_calibration_error_score == 10.0
    assert profile.calibrated_confidence_score == 76.15


def test_confidence_calibration_profile_requires_sufficient_samples():
    profile = ConfidenceCalibrationProfile.from_observations(
        (
            ConfidenceCalibrationObservation.from_mapping(
                {
                    **_ready_observations()[0],
                    "sample_count": 2,
                }
            ),
        )
    )

    assert profile.is_ready is False


def test_confidence_calibration_profile_blocks_high_calibration_error():
    profile = ConfidenceCalibrationRepository(
        [{**item, "calibration_error_score": 45} for item in _ready_observations()]
    ).build_profiles()[0]

    assert profile.is_ready is False


def test_confidence_calibration_policy_waits_for_empty_profiles():
    decision = ConfidenceCalibrationPolicy().decide(())

    assert decision.status == "CONFIDENCE_CALIBRATION_WAIT"
    assert decision.action == "WAIT"


def test_confidence_calibration_policy_selects_strongest_ready_profile():
    profiles = ConfidenceCalibrationRepository(
        _ready_observations()
        + [
            {
                "market_regime": "trend expansion",
                "confidence_bucket": "validated confidence",
                "direction": "buy",
                "sample_count": 30,
                "raw_confidence_score": 82,
                "realized_accuracy_rate": 81,
                "calibration_error_score": 6,
                "confidence_stability_score": 80,
                "confidence_drift_score": 10,
                "execution_cost_score": 75,
                "trace_id": "cal-004",
            }
        ]
    ).build_profiles()

    decision = ConfidenceCalibrationPolicy().decide(profiles)

    assert decision.status == "CONFIDENCE_CALIBRATION_READY"
    assert decision.selected_profile_key == "TREND_EXPANSION:VALIDATED_CONFIDENCE:BUY"


def test_confidence_calibration_runtime_builds_ready_report():
    report = ConfidenceCalibrationRuntime().run(_ready_observations())

    assert report.status == "CONFIDENCE_CALIBRATION_READY"
    assert report.action == "USE_CALIBRATED_CONFIDENCE"
    assert report.active_market_regime == "TREND_EXPANSION"
    assert report.selected_confidence_bucket == "HIGH_CONFIDENCE"
    assert report.is_ready is True


def test_confidence_calibration_runtime_handles_empty_observations():
    report = ConfidenceCalibrationRuntime().run([])

    assert report.status == "CONFIDENCE_CALIBRATION_WAIT"
    assert report.profile_count == 0
    assert report.is_ready is False


def test_production_milestone_e_confidence_calibration_runtime_is_deterministic():
    runtime = ProductionMilestoneEConfidenceCalibrationRuntime()

    first = runtime.run(_ready_observations())
    second = runtime.run(list(reversed(_ready_observations())))

    assert first == second
