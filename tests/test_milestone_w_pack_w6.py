import json
from pathlib import Path

from afip.adaptive_sl import (
    AdaptiveSLInput,
    AdaptiveSLRuntime,
    EXTENDED_SL_APPROVED,
    NORMAL_SL_APPROVED,
    NOT_ELIGIBLE,
)


def _item(**changes):
    base = dict(
        plan_id="plan-001",
        oqs=99.4,
        oqs_status="ELITE",
        adaptive_sl_review_status="ELIGIBLE_FOR_ADAPTIVE_SL_REVIEW",
        final_confidence=99.5,
        evidence_quality="HIGH",
        capital_pass=True,
        risk_pass=True,
        execution_pass=True,
        reward_risk_pass=True,
        data_integrity_pass=True,
        atr_points=700,
        structure_points=650,
        buffer_points=50,
    )
    base.update(changes)
    return AdaptiveSLInput(**base)


def test_structural_sl_is_not_clamped_to_legacy_bands():
    engine = AdaptiveSLRuntime()
    low = engine.assess(_item(atr_points=300, structure_points=350, buffer_points=50))
    high = engine.assess(_item(atr_points=900, structure_points=850, buffer_points=50))
    assert low.status == NORMAL_SL_APPROVED
    assert low.recommended_sl_points == 400
    assert high.recommended_sl_points == 950


def test_structural_sl_has_no_fixed_extended_band():
    engine = AdaptiveSLRuntime()
    passed = engine.assess(_item(atr_points=1100, structure_points=1000, buffer_points=100))
    assert passed.status == NORMAL_SL_APPROVED
    assert passed.recommended_sl_points == 1200

    assert engine.assess(_item(atr_points=1100, buffer_points=100, oqs=98.9)).status == NORMAL_SL_APPROVED
    assert engine.assess(_item(atr_points=1100, buffer_points=100, final_confidence=98.9)).status == NORMAL_SL_APPROVED


def test_no_fixed_hard_ceiling_compresses_researched_distance():
    result = AdaptiveSLRuntime().assess(_item(atr_points=1500, structure_points=1400, buffer_points=100))
    assert result.status == NORMAL_SL_APPROVED
    assert result.recommended_sl_points == 1600
    assert result.hard_ceiling_points is None


def test_all_independent_gates_fail_closed():
    engine = AdaptiveSLRuntime()
    for gate in ("capital_pass", "risk_pass", "execution_pass", "reward_risk_pass", "data_integrity_pass"):
        result = engine.assess(_item(**{gate: False}))
        assert result.status == NOT_ELIGIBLE
        assert result.reason == "required_gate_not_approved"


def test_contract_and_no_execution_authority():
    root = Path(__file__).resolve().parents[1]
    contract = json.loads((root / "config" / "adaptive_sl_runtime_contract.json").read_text(encoding="utf-8"))
    assert contract["hard_ceiling_points"] is None
    assert contract["fixed_stop_distance_bands_allowed"] is False
    assert contract["fail_closed"] is True
    result = AdaptiveSLRuntime().assess(_item())
    assert result.execution_authority is False
    assert result.order_send_called is False
