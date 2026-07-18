import json
from pathlib import Path

from afip.capital_growth_engine import CapitalGrowthEngine
from afip.position_policy import (
    confidence_maximum_units,
    requested_units_within_confidence_ceiling,
)

CONFIG = Path(__file__).resolve().parents[1] / "config" / "four_profile_demo.json"


def _profiles():
    payload = json.loads(CONFIG.read_text(encoding="utf-8"))
    return payload, {item["profile_id"]: item for item in payload["profiles"]}


def _tier_decision(profile, balance, current_orders=0):
    tiers = tuple(
        (item["minimum_balance"], tuple(item["lots"]))
        for item in profile["capital_tiers"]
    )
    return CapitalGrowthEngine.evaluate(
        mode=profile["allocation_mode"],
        balance=balance,
        current_orders=current_orders,
        capital_tiers=tiers,
        maximum_orders=profile["maximum_concurrent_orders"],
        lot_per_unit=profile["lot_per_unit"],
    )


def test_confidence_boundaries_are_maximum_capacity_only():
    assert confidence_maximum_units(97.9999).maximum_units == 0
    assert confidence_maximum_units(98.0).maximum_units == 1
    assert confidence_maximum_units(98.49).maximum_units == 1
    assert confidence_maximum_units(98.5).maximum_units == 2
    assert confidence_maximum_units(99.49).maximum_units == 2
    assert confidence_maximum_units(99.5).maximum_units == 3
    assert confidence_maximum_units(100.0).maximum_units == 3


def test_missing_intelligence_request_defaults_to_one_not_the_ceiling():
    result = requested_units_within_confidence_ceiling({}, 100.0)
    assert result.confidence_maximum_units == 3
    assert result.requested_units == 1
    assert result.approved_units == 1
    assert result.source == "CONSERVATIVE_DEFAULT_ONE_UNIT"


def test_explicit_intelligence_request_can_use_less_than_ceiling():
    result = requested_units_within_confidence_ceiling({"requested_units": 2}, 100.0)
    assert result.confidence_maximum_units == 3
    assert result.requested_units == 2
    assert result.approved_units == 2


def test_explicit_request_is_reduced_by_confidence_ceiling():
    result = requested_units_within_confidence_ceiling({"requested_units": 3}, 98.6)
    assert result.confidence_maximum_units == 2
    assert result.requested_units == 3
    assert result.approved_units == 2
    assert result.reason == "requested_units_reduced_by_confidence_ceiling"


def test_p1_exact_tiers_and_per_order_ceiling():
    _, profiles = _profiles()
    p1 = profiles["P1"]
    expected = {
        0: (0.01,), 100: (0.01, 0.01), 300: (0.01, 0.01, 0.01),
        900: (0.02, 0.02, 0.02), 1800: (0.03, 0.03, 0.03),
        3000: (0.04, 0.04, 0.04), 4500: (0.05, 0.05, 0.05),
        6300: (0.06, 0.06, 0.06), 8400: (0.07, 0.07, 0.07),
        10800: (0.08, 0.08, 0.08), 13500: (0.09, 0.09, 0.09),
        16500: (0.10, 0.10, 0.10),
    }
    assert {x["minimum_balance"]: tuple(x["lots"]) for x in p1["capital_tiers"]} == expected
    assert p1["maximum_lot_per_order"] == 0.10
    assert _tier_decision(p1, 1_000_000).target_lots == (0.10, 0.10, 0.10)


def test_p2_010_starts_at_15000_and_caps_at_100():
    _, profiles = _profiles()
    p2 = profiles["P2"]
    by_lot = {round(x["lots"][0], 2): x["minimum_balance"] for x in p2["capital_tiers"]}
    assert by_lot[0.10] == 15000
    assert p2["capital_tiers"][-1]["lots"] == [1.0, 1.0, 1.0]
    assert p2["maximum_lot_per_order"] == 1.0


def test_p3_exact_early_growth_and_caps_at_1000():
    _, profiles = _profiles()
    p3 = profiles["P3"]
    early = [(x["minimum_balance"], x["lots"]) for x in p3["capital_tiers"][:12]]
    assert early == [
        (0, [0.01]), (100, [0.01, 0.01]), (300, [0.01, 0.01, 0.01]),
        (900, [0.02, 0.02, 0.02]), (1350, [0.03, 0.03, 0.03]),
        (1800, [0.04, 0.04, 0.04]), (2250, [0.05, 0.05, 0.05]),
        (2700, [0.06, 0.06, 0.06]), (3150, [0.07, 0.07, 0.07]),
        (3600, [0.08, 0.08, 0.08]), (4050, [0.09, 0.09, 0.09]),
        (4500, [0.10, 0.10, 0.10]),
    ]
    assert p3["capital_tiers"][-1]["lots"] == [10.0, 10.0, 10.0]
    assert p3["maximum_lot_per_order"] == 10.0


def test_p4_remains_fixed_001_without_growth_or_total_unit_ceiling():
    payload, profiles = _profiles()
    p4 = profiles["P4"]
    assert p4["allocation_mode"] == "RESEARCH_FIXED_001"
    assert p4["maximum_concurrent_orders"] == 0
    assert p4["maximum_lot_per_order"] == 0.01
    assert p4["capital_tiers"] == []
    assert payload["position_policy"]["automatic_fill_to_ceiling"] is False
    assert payload["position_policy"]["missing_intelligence_request_default_units"] == 1
