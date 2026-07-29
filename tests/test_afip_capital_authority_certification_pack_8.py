from pathlib import Path

from afip.lot_authority import calculate_lot_authority
from afip.control_center_runtime import ControlCenterRuntime
from afip.dashboard_ui.control_center import render_control_center


def _profile():
    return {
        "profile_id": "P1",
        "maximum_units": 3,
        "maximum_concurrent_orders": 3,
        "allocation_mode": "CAPITAL_TIER_TABLE",
        "capital_tiers": [
            {"minimum_balance": 0, "lots": [0.01]},
            {"minimum_balance": 300, "lots": [0.01, 0.01]},
            {"minimum_balance": 900, "lots": [0.01, 0.01, 0.01]},
        ],
        "execution_enabled": True,
        "maximum_lot_per_order": 0.1,
        "capital_per_unit": 1,
        "capital_per_unit_legacy_only": 1,
    }


def _decision(units=3):
    return {"requested_units": units}


def test_explicit_zero_equity_is_fail_closed():
    result = calculate_lot_authority(
        profile=_profile(), decision=_decision(), confidence=100,
        balance=1000, equity=0,
    )
    assert result.available_capital == 0
    assert result.capital_basis == "MIN_BALANCE_EQUITY"
    assert result.capital_units == 0
    assert result.approved_units == 0
    assert result.limiting_gate == "CAPITAL"


def test_zero_balance_never_receives_initial_free_unit():
    result = calculate_lot_authority(
        profile=_profile(), decision=_decision(), confidence=100,
        balance=0, equity=0,
    )
    assert result.capital_units == 0
    assert result.approved_lots == ()


def test_positive_small_capital_can_receive_initial_001_unit():
    result = calculate_lot_authority(
        profile=_profile(), decision=_decision(), confidence=100,
        balance=25, equity=20,
    )
    assert result.available_capital == 20
    assert result.capital_units == 1
    assert result.approved_units == 1
    assert result.approved_lots == (0.01,)


def test_lower_equity_is_the_capital_authority():
    result = calculate_lot_authority(
        profile=_profile(), decision=_decision(), confidence=100,
        balance=1000, equity=350,
    )
    assert result.available_capital == 350
    assert result.capital_units == 2
    assert result.approved_units == 2


def test_legacy_capital_fields_do_not_change_result():
    a = calculate_lot_authority(profile=_profile(), decision=_decision(), confidence=100, balance=350, equity=350)
    profile = _profile()
    profile["capital_per_unit"] = 999999
    profile["capital_per_unit_legacy_only"] = 999999
    b = calculate_lot_authority(profile=profile, decision=_decision(), confidence=100, balance=350, equity=350)
    assert a.approved_units == b.approved_units == 2
    assert a.total_approved_lot == b.total_approved_lot


def test_authority_result_contains_complete_gate_trace():
    row = calculate_lot_authority(
        profile=_profile(), decision=_decision(2), confidence=99,
        balance=1000, equity=900, risk_units=1, execution_safety_units=3,
    ).as_dict()
    for key in (
        "balance", "equity", "available_capital", "capital_basis",
        "requested_units", "confidence_units", "capital_units", "risk_units",
        "profile_max_units", "execution_safety_units", "approved_units",
        "approved_lot_per_order", "total_approved_lot", "limiting_gate",
        "policy_version",
    ):
        assert key in row
    assert row["approved_units"] == 1
    assert row["limiting_gate"] == "RISK"


def test_dashboard_exposes_capital_authority_fields(tmp_path: Path):
    base = tmp_path / "runtime" / "profiles" / "p1"
    base.mkdir(parents=True)
    (base / "demo_execution_state.json").write_text(
        '{"account_balance":1000,"account_equity":850,"available_capital":850,'
        '"capital_basis":"MIN_BALANCE_EQUITY","capital_units":2,"risk_units":1,'
        '"confidence_units":3,"profile_max_units":3,"execution_safety_units":3,'
        '"limiting_gate":"RISK","approved_lot_per_order":0.01,'
        '"total_approved_lot":0.01,"capital_authority_policy":"PACK8"}',
        encoding="utf-8",
    )
    snapshot = ControlCenterRuntime(tmp_path).snapshot()
    p1 = next(row for row in snapshot["profiles"] if row["profile_id"] == "P1")
    assert p1["available_capital"] == 850
    assert p1["capital_basis"] == "MIN_BALANCE_EQUITY"
    assert p1["lot_limiting_gate"] == "RISK"
    html = render_control_center(tmp_path)
    assert "Available Capital" in html
    assert "Lot Limiting Gate" in html
    assert "MIN_BALANCE_EQUITY" in html
