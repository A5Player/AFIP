from pathlib import Path
import json
import pytest
from afip.phase_v_major import MODES, PhaseVMajorRuntime


def test_modes_are_explicit():
    assert MODES == {"DATA_ONLY", "RESEARCH_ONLY", "SHADOW_EXECUTION", "DEMO_EXECUTION", "LIVE_EXECUTION"}


def test_default_config_is_data_only(tmp_path: Path):
    runtime = PhaseVMajorRuntime(tmp_path)
    assert runtime.config()["mode"] == "DATA_ONLY"


def test_manual_arm_requires_exact_confirmation(tmp_path: Path):
    runtime = PhaseVMajorRuntime(tmp_path)
    with pytest.raises(ValueError): runtime.arm_live("yes")
    path = runtime.arm_live("ARM AFIP LIVE EXECUTION")
    assert path.exists()
    assert runtime.disarm_live() is True


def test_research_certification_blocks_gaps(tmp_path: Path):
    runtime = PhaseVMajorRuntime(tmp_path)
    ok, blockers = runtime._research_certified({"usable_bars": 5000, "replay_completed": True, "gap_ranges_detected": 1, "missing_bars_detected": 0}, runtime.config())
    assert ok is False
    assert "historical_gap_ranges_detected" in blockers


def test_research_certification_ignores_expected_market_closures(tmp_path: Path):
    runtime = PhaseVMajorRuntime(tmp_path)
    ok, blockers = runtime._research_certified(
        {
            "usable_bars": 5000,
            "replay_completed": True,
            "gap_ranges_detected": 1618,
            "missing_bars_detected": 17748,
            "expected_closure_ranges_detected": 1618,
            "expected_closure_bars_detected": 17748,
            "unexpected_gap_ranges_detected": 0,
            "unexpected_missing_bars_detected": 0,
        },
        runtime.config(),
    )
    assert ok is True
    assert blockers == []


def test_research_certification_blocks_unexpected_gaps_even_when_closures_exist(tmp_path: Path):
    runtime = PhaseVMajorRuntime(tmp_path)
    ok, blockers = runtime._research_certified(
        {
            "usable_bars": 5000,
            "replay_completed": True,
            "gap_ranges_detected": 1619,
            "missing_bars_detected": 17749,
            "unexpected_gap_ranges_detected": 1,
            "unexpected_missing_bars_detected": 1,
        },
        runtime.config(),
    )
    assert ok is False
    assert blockers == ["historical_gap_ranges_detected", "historical_missing_bars_detected"]


def test_research_certification_accepts_complete_clean_dataset(tmp_path: Path):
    runtime = PhaseVMajorRuntime(tmp_path)
    ok, blockers = runtime._research_certified({"usable_bars": 5000, "replay_completed": True, "gap_ranges_detected": 0, "missing_bars_detected": 0}, runtime.config())
    assert ok is True and blockers == []


def test_config_rejects_unknown_mode(tmp_path: Path):
    path = tmp_path / "config/phase_v_major.json"; path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"mode": "AUTO_DANGEROUS"}), encoding="utf-8")
    with pytest.raises(ValueError): PhaseVMajorRuntime(tmp_path).config()


def test_policy_promotion_requires_certification(tmp_path: Path):
    from afip.phase_v_major import CertifiedPolicyPromotion
    authority = CertifiedPolicyPromotion(tmp_path)
    allowed, blockers = authority.evaluate({"policy_version": "V2", "sample_size": 1000})
    assert allowed is False
    assert "walk_forward_passed_required" in blockers


def test_policy_promotion_accepts_complete_evidence(tmp_path: Path):
    from afip.phase_v_major import CertifiedPolicyPromotion
    authority = CertifiedPolicyPromotion(tmp_path)
    candidate = {"policy_version":"V2", "sample_size":1000, "minimum_sample_size":1000, "walk_forward_passed":True, "out_of_sample_passed":True, "drawdown_limit_passed":True, "stability_passed":True, "no_data_leakage":True}
    allowed, blockers = authority.evaluate(candidate)
    assert allowed is True and blockers == ()
