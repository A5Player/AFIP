import json
from pathlib import Path

import pytest

from afip.demo_execution_gateway.runtime import DemoProfilePolicy
from afip.position_capacity_formula import capital_tiers_from_profile, expand_capital_tier_formula

CONFIG = Path(__file__).resolve().parents[1] / "config" / "four_profile_demo.json"


def _raw_profiles():
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    return {item["profile_id"]: item for item in data["profiles"]}


def test_config_uses_compact_formulas_for_p1_to_p3():
    profiles = _raw_profiles()
    for profile_id in ("P1", "P2", "P3"):
        assert "capital_tier_formula" in profiles[profile_id]
        assert "capital_tiers" not in profiles[profile_id]
    assert profiles["P4"]["capital_tiers"] == []


def test_p1_formula_is_exactly_equivalent_to_pack_7_2_curve():
    tiers = capital_tiers_from_profile(_raw_profiles()["P1"])
    expected_balances = (0, 300, 900, 1800, 3000, 4500, 6300, 8400, 10800, 13500, 16500, 19800)
    assert tuple(level for level, _ in tiers) == expected_balances
    assert tiers[0][1] == (0.01,)
    assert tiers[1][1] == (0.01, 0.01)
    assert tiers[-1][1] == (0.10, 0.10, 0.10)


def test_p2_formula_preserves_every_balance_and_lot_through_100():
    tiers = capital_tiers_from_profile(_raw_profiles()["P2"])
    assert len(tiers) == 102
    assert tiers[:3] == (
        (0, (0.01,)),
        (300, (0.01, 0.01)),
        (900, (0.01, 0.01, 0.01)),
    )
    for lot_step in range(2, 101):
        index = lot_step + 1
        expected_balance = 300 * ((lot_step + 1) * (lot_step + 2) // 2)
        expected_lot = round(lot_step / 100, 2)
        assert tiers[index] == (expected_balance, (expected_lot,) * 3)
    assert tiers[-1] == (1545300, (1.0, 1.0, 1.0))


def test_p3_formula_preserves_every_balance_and_lot_through_1000():
    tiers = capital_tiers_from_profile(_raw_profiles()["P3"])
    assert len(tiers) == 1002
    assert tiers[:3] == (
        (0, (0.01,)),
        (200, (0.01, 0.01)),
        (450, (0.01, 0.01, 0.01)),
    )
    for lot_step in range(2, 1001):
        index = lot_step + 1
        expected_lot = round(lot_step / 100, 2)
        assert tiers[index] == (600 * lot_step, (expected_lot,) * 3)
    assert tiers[-1] == (600000, (10.0, 10.0, 10.0))


def test_runtime_policy_receives_legacy_in_memory_tier_table():
    for raw in _raw_profiles().values():
        policy = DemoProfilePolicy.from_mapping(raw)
        assert policy.validate() == ()
    assert len(DemoProfilePolicy.from_mapping(_raw_profiles()["P2"]).capital_tiers) == 102
    assert len(DemoProfilePolicy.from_mapping(_raw_profiles()["P3"]).capital_tiers) == 1002


def test_legacy_explicit_table_remains_supported():
    raw = {
        "capital_tiers": [
            {"minimum_balance": 0, "lots": [0.01]},
            {"minimum_balance": 300, "lots": [0.01, 0.01]},
        ],
        "capital_tier_formula": {"kind": "LINEAR_BALANCE"},
    }
    assert capital_tiers_from_profile(raw) == (
        (0.0, (0.01,)),
        (300.0, (0.01, 0.01)),
    )


def test_invalid_formula_is_rejected_before_execution_policy_is_usable():
    with pytest.raises(ValueError, match="capital_tier_formula_kind_unknown"):
        expand_capital_tier_formula({
            "kind": "UNKNOWN",
            "lot_step": 0.01,
            "maximum_lot": 0.02,
            "one_order_minimum_balance": 0,
            "two_order_minimum_balance": 100,
            "three_order_minimum_balance": 200,
        })
