from __future__ import annotations

import json
from pathlib import Path

import pytest

from afip.lot_authority import calculate_lot_authority
from afip.position_capacity_formula import capital_tiers_from_profile


CONFIG = Path("config/four_profile_demo.json")


def _profiles():
    return {p["profile_id"]: p for p in json.loads(CONFIG.read_text(encoding="utf-8"))["profiles"]}


def _authority(profile, balance, confidence=100.0, requested_units=3):
    return calculate_lot_authority(
        profile=profile,
        decision={"requested_units": requested_units},
        confidence=confidence,
        balance=balance,
        equity=balance,
        current_orders=0,
    )


def test_obsolete_capital_per_unit_fields_are_absent():
    text = CONFIG.read_text(encoding="utf-8")
    assert '"capital_per_unit"' not in text
    assert '"capital_per_unit_legacy_only"' not in text


@pytest.mark.parametrize(
    "profile_id,balance,units,lot",
    [
        ("P1", 299, 1, 0.01), ("P1", 300, 2, 0.01), ("P1", 900, 3, 0.01),
        ("P1", 1800, 3, 0.02), ("P1", 19800, 3, 0.10), ("P1", 999999, 3, 0.10),
        ("P2", 299, 1, 0.01), ("P2", 300, 2, 0.01), ("P2", 900, 3, 0.01),
        ("P2", 1800, 3, 0.02), ("P2", 19800, 3, 0.10),
        ("P3", 199, 1, 0.01), ("P3", 200, 2, 0.01), ("P3", 450, 3, 0.01),
        ("P3", 1200, 3, 0.02), ("P3", 1800, 3, 0.03), ("P3", 3000, 3, 0.05),
    ],
)
def test_exact_balance_ladder(profile_id, balance, units, lot):
    result = _authority(_profiles()[profile_id], balance)
    assert result.approved_units == units
    assert result.approved_lot_per_order == lot
    assert result.approved_lots == tuple(lot for _ in range(units))


@pytest.mark.parametrize(
    "confidence,maximum_units",
    [(97.99, 0), (98.0, 1), (98.49, 1), (98.5, 2), (99.49, 2), (99.5, 3), (100.0, 3)],
)
def test_confidence_unit_ceiling(confidence, maximum_units):
    result = _authority(_profiles()["P1"], 19800, confidence=confidence)
    assert result.approved_units == maximum_units


def test_p1_small_balance_cannot_open_three_orders():
    result = _authority(_profiles()["P1"], 138.0)
    assert result.approved_units == 1
    assert result.approved_lots == (0.01,)


def test_p4_is_experimental_execution_profile():
    p4 = _profiles()["P4"]
    assert p4["maximum_lot_per_order"] == 0.01
    assert p4["allocation_mode"] == "CAPITAL_TIER_TABLE"
    assert p4["sizing_authority"] == "CAPITAL_TIER_FORMULA_ONLY"
    assert p4["maximum_units"] == 1
    assert p4["execution_enabled"] is True
    assert p4["research_enabled"] is True


def test_formula_maximums_are_exact():
    profiles = _profiles()
    assert capital_tiers_from_profile(profiles["P1"])[-1][1] == (0.1, 0.1, 0.1)
    assert capital_tiers_from_profile(profiles["P2"])[-1][1] == (1.0, 1.0, 1.0)
    assert capital_tiers_from_profile(profiles["P3"])[-1][1] == (10.0, 10.0, 10.0)
