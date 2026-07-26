from pathlib import Path
import json

def test_maximum_lot_unit_initial_tiers_are_the_only_production_thresholds():
    p=json.loads(Path("config/four_profile_demo.json").read_text(encoding="utf-8-sig"))
    expected={
        "P1": [(0, 1), (300, 2), (900, 3)],
        "P2": [(0, 1), (300, 2), (900, 3)],
        "P3": [(0, 1), (200, 2), (450, 3)],
    }
    forbidden = {
        "one_order_minimum_balance", "two_order_minimum_balance", "three_order_minimum_balance",
        "authority_one_order_minimum_balance", "authority_two_order_minimum_balance",
        "authority_three_order_minimum_balance",
    }
    for row in p["profiles"]:
        if row["profile_id"] not in expected:
            continue
        formula = row["capital_tier_formula"]
        assert forbidden.isdisjoint(formula)
        assert [(tier["minimum_balance"], len(tier["lots"])) for tier in formula["initial_tiers"]] == expected[row["profile_id"]]

def test_binding_rechecked_before_send():
    text=Path("afip/demo_execution_gateway/runtime.py").read_text(encoding="utf-8")
    assert "binding_changed_before_order_send" in text
    assert text.count("_binding_snapshot(mt5)") >= 2

def test_start_all_requires_isolation_verification():
    text=Path("tools/afip_demo_execution_control.py").read_text(encoding="utf-8")
    assert "account_isolation_verification_failed" in text
