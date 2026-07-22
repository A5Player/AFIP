from __future__ import annotations

import json
from pathlib import Path

import pytest

from afip.lot_authority.runtime import calculate_lot_authority

CONFIG = Path("config/four_profile_demo.json")


def profiles():
    payload = json.loads(CONFIG.read_text(encoding="utf-8"))
    return {row["profile_id"]: row for row in payload["profiles"]}


def authority(profile_id: str, balance: float, confidence: float = 100.0):
    profile = profiles()[profile_id]
    return calculate_lot_authority(
        profile=profile,
        decision={"requested_units": 3},
        confidence=confidence,
        balance=balance,
        equity=balance,
    )


@pytest.mark.parametrize(
    "balance,units,lot",
    [
        (299, 1, 0.01), (300, 2, 0.01), (900, 3, 0.01),
        (1800, 3, 0.02), (3000, 3, 0.03), (4500, 3, 0.04),
        (6300, 3, 0.05), (8400, 3, 0.06), (10800, 3, 0.07),
        (13500, 3, 0.08), (16500, 3, 0.09), (19800, 3, 0.10),
        (999999, 3, 0.10),
    ],
)
def test_p1_maximum_lot_size_and_units(balance, units, lot):
    result = authority("P1", balance)
    assert result.approved_units == units
    assert result.approved_lot_per_order == lot


@pytest.mark.parametrize(
    "balance,units,lot",
    [
        (299, 1, 0.01), (300, 2, 0.01), (900, 3, 0.01),
        (1800, 3, 0.02), (19800, 3, 0.10),
    ],
)
def test_p2_starts_with_p1_ladder_and_can_continue_to_one_lot(balance, units, lot):
    result = authority("P2", balance)
    assert result.approved_units == units
    assert result.approved_lot_per_order == lot
    assert result.approved_lot_per_order <= 1.0


@pytest.mark.parametrize(
    "balance,units,lot",
    [
        (199, 1, 0.01), (200, 2, 0.01), (450, 3, 0.01),
        (1200, 3, 0.02), (1800, 3, 0.03), (2400, 3, 0.04),
        (3000, 3, 0.05), (600000, 3, 10.0),
    ],
)
def test_p3_maximum_lot_size_and_units(balance, units, lot):
    result = authority("P3", balance)
    assert result.approved_units == units
    assert result.approved_lot_per_order == lot
    assert result.approved_lot_per_order <= 10.0


@pytest.mark.parametrize(
    "confidence,units",
    [(97.99, 0), (98.0, 1), (98.49, 1), (98.5, 2), (99.49, 2), (99.5, 3), (100.0, 3)],
)
def test_confidence_gate_is_the_maximum_unit_ceiling(confidence, units):
    assert authority("P1", 19800, confidence).approved_units == units


def test_p4_is_always_one_001_lot_order_at_most():
    profile = profiles()["P4"]
    assert profile["maximum_units"] == 1
    assert profile["maximum_concurrent_orders"] == 1
    assert profile["maximum_lot_per_order"] == 0.01
    assert authority("P4", 1000000, 100.0).approved_lots == (0.01,)
    assert authority("P4", 1000000, 97.99).approved_lots == ()


def test_legacy_capital_fields_are_not_configuration_authorities():
    text = CONFIG.read_text(encoding="utf-8")
    assert '"capital_per_unit"' not in text
    assert '"capital_per_unit_legacy_only"' not in text
