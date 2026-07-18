import json
from pathlib import Path

import pytest

from afip.capital_growth_engine import CapitalGrowthEngine
from afip.position_policy import confidence_maximum_units

CONFIG = Path(__file__).resolve().parents[1] / "config" / "four_profile_demo.json"


def profiles():
    payload = json.loads(CONFIG.read_text(encoding="utf-8"))
    return payload, {item["profile_id"]: item for item in payload["profiles"]}


@pytest.mark.parametrize(
    ("confidence", "units"),
    [
        (-1, 0), (0, 0), (97.9999, 0), (98.0, 1), (98.4999, 1),
        (98.5, 2), (99.4999, 2), (99.5, 3), (100.0, 3), (101.0, 3),
    ],
)
def test_confidence_boundaries_are_certified(confidence, units):
    assert confidence_maximum_units(confidence).maximum_units == units


def test_position_policy_is_machine_readable_and_martingale_is_disabled():
    payload, _ = profiles()
    policy = payload["position_policy"]
    assert policy["version"] == "AFIP_POSITION_POLICY_V2"
    assert policy["martingale_allowed"] is False
    assert "MIN_CONFIDENCE" in policy["final_allocation_rule"]


def test_p1_reaches_permanent_010_ceiling_at_16500():
    _, by_id = profiles()
    p1 = by_id["P1"]
    tiers = tuple((x["minimum_balance"], tuple(x["lots"])) for x in p1["capital_tiers"])
    below = CapitalGrowthEngine.evaluate(mode=p1["allocation_mode"], balance=16499.99, current_orders=0, capital_tiers=tiers, maximum_orders=p1["maximum_concurrent_orders"])
    at_cap = CapitalGrowthEngine.evaluate(mode=p1["allocation_mode"], balance=16500, current_orders=0, capital_tiers=tiers, maximum_orders=p1["maximum_concurrent_orders"])
    above = CapitalGrowthEngine.evaluate(mode=p1["allocation_mode"], balance=1_000_000, current_orders=0, capital_tiers=tiers, maximum_orders=p1["maximum_concurrent_orders"])
    assert below.target_lots == (0.09, 0.09, 0.09)
    assert at_cap.target_lots == (0.10, 0.10, 0.10)
    assert above.target_lots == (0.10, 0.10, 0.10)
    assert p1["maximum_lot_per_order"] == 0.10


def test_p2_tiers_are_ordered_equal_unit_lots_and_stop_at_100():
    _, by_id = profiles()
    p2 = by_id["P2"]
    tiers = p2["capital_tiers"]
    assert all(a["minimum_balance"] < b["minimum_balance"] for a, b in zip(tiers, tiers[1:]))
    assert all(len(set(t["lots"])) == 1 for t in tiers[3:])
    assert tiers[-1]["lots"] == [1.0, 1.0, 1.0]
    assert p2["maximum_lot_per_order"] == 1.0


def test_p3_after_002_increases_001_for_each_450_balance_and_caps_at_1000():
    _, by_id = profiles()
    p3 = by_id["P3"]
    tiers = p3["capital_tiers"]
    growth = tiers[3:]
    for previous, current in zip(growth, growth[1:]):
        assert current["minimum_balance"] - previous["minimum_balance"] == 450
        assert round(current["lots"][0] - previous["lots"][0], 2) == 0.01
        assert current["lots"] == [current["lots"][0]] * 3
    assert tiers[-1]["minimum_balance"] == 450000
    assert tiers[-1]["lots"] == [10.0, 10.0, 10.0]
    assert p3["maximum_lot_per_order"] == 10.0


def test_p4_is_fixed_001_research_without_lot_growth():
    _, by_id = profiles()
    p4 = by_id["P4"]
    assert p4["allocation_mode"] == "RESEARCH_FIXED_001"
    assert p4["lot_per_unit"] == 0.01
    assert p4["maximum_lot_per_order"] == 0.01
    assert p4["capital_tiers"] == []
