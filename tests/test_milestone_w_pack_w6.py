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


def test_normal_sl_is_clamped_to_500_1000():
    engine = AdaptiveSLRuntime()
    low = engine.assess(_item(atr_points=300, structure_points=350, buffer_points=50))
    high = engine.assess(_item(atr_points=900, structure_points=850, buffer_points=50))
    assert low.status == NORMAL_SL_APPROVED
    assert low.recommended_sl_points == 500
    assert high.recommended_sl_points == 950


def test_extended_requires_elite_confidence_evidence_and_w5_review():
    engine = AdaptiveSLRuntime()
    passed = engine.assess(_item(atr_points=1100, structure_points=1000, buffer_points=100))
    assert passed.status == EXTENDED_SL_APPROVED
    assert passed.recommended_sl_points == 1200

    assert engine.assess(_item(atr_points=1100, buffer_points=100, oqs=98.9)).status == NOT_ELIGIBLE
    assert engine.assess(_item(atr_points=1100, buffer_points=100, final_confidence=98.9)).status == NOT_ELIGIBLE
    assert engine.assess(_item(atr_points=1100, buffer_points=100, evidence_quality="MEDIUM")).status == NOT_ELIGIBLE


def test_hard_ceiling_is_never_exceeded():
    result = AdaptiveSLRuntime().assess(_item(atr_points=1500, structure_points=1400, buffer_points=100))
    assert result.status == NOT_ELIGIBLE
    assert result.reason == "hard_ceiling_exceeded"
    assert result.recommended_sl_points is None


def test_all_independent_gates_fail_closed():
    engine = AdaptiveSLRuntime()
    for gate in ("capital_pass", "risk_pass", "execution_pass", "reward_risk_pass", "data_integrity_pass"):
        result = engine.assess(_item(**{gate: False}))
        assert result.status == NOT_ELIGIBLE
        assert result.reason == "required_gate_not_approved"


def test_contract_and_no_execution_authority():
    root = Path(__file__).resolve().parents[1]
    contract = json.loads((root / "config" / "adaptive_sl_runtime_contract.json").read_text(encoding="utf-8"))
    assert contract["hard_ceiling_points"] == 1500
    assert contract["fail_closed"] is True
    result = AdaptiveSLRuntime().assess(_item())
    assert result.execution_authority is False
    assert result.order_send_called is False
