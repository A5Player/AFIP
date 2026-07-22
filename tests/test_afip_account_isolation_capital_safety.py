from pathlib import Path
import json

def test_capital_thresholds_are_not_zero():
    p=json.loads(Path("config/four_profile_demo.json").read_text(encoding="utf-8-sig"))
    expected={"P1":1000,"P2":500,"P3":200}
    for row in p["profiles"]:
        if row["profile_id"] in expected:
            assert row["capital_tier_formula"]["one_order_minimum_balance"]==expected[row["profile_id"]]

def test_binding_rechecked_before_send():
    text=Path("afip/demo_execution_gateway/runtime.py").read_text(encoding="utf-8")
    assert "binding_changed_before_order_send" in text
    assert text.count("_binding_snapshot(mt5)") >= 2

def test_start_all_requires_isolation_verification():
    text=Path("tools/afip_demo_execution_control.py").read_text(encoding="utf-8")
    assert "account_isolation_verification_failed" in text
