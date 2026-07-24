from pathlib import Path

from afip.lot_authority.runtime import calculate_lot_authority

GATEWAY = Path("afip/demo_execution_gateway/runtime.py")

def _profile(maximum_lot: float = 0.01):
    return {
        "profile_id": "P1", "maximum_units": 3, "maximum_concurrent_orders": 3,
        "allocation_mode": "CAPITAL_TIER_TABLE", "execution_enabled": True,
        "maximum_lot_per_order": maximum_lot,
        "capital_tiers": [{"minimum_balance": 0, "lots": [0.10, 0.10, 0.10]}],
    }

def test_lot_authority_enforces_configured_maximum_lot_per_order():
    result = calculate_lot_authority(profile=_profile(), decision={"requested_units": 3}, confidence=100, balance=100000, equity=100000)
    assert result.approved_lots == (0.01, 0.01, 0.01)

def test_gateway_passes_maximum_lot_to_single_authority():
    text = GATEWAY.read_text(encoding="utf-8")
    assert '"maximum_lot_per_order": self.policy.maximum_lot_per_order' in text
    assert '"unit_selection_source": "SINGLE_LOT_AUTHORITY"' in text

def test_gateway_keeps_adaptive_per_unit_rr_path():
    text = GATEWAY.read_text(encoding="utf-8")
    assert 'rr_plans = tuple(protection_portfolio.get("unit_plans", ()))' in text
    assert 'unit_plan = rr_plans[order_index] if rr_plans else protection' in text
    assert 'request = self._request(mt5, action, unit_sl_points, unit_tp_points, volume)' in text

def test_legacy_fixed_pair_is_detected_by_safety_guard_but_not_yet_gateway_enforced():
    guard = Path("afip/execution_safety/capital_aware_protection_guard.py").read_text(encoding="utf-8")
    assert "legacy_fixed_sl_tp_fallback_rejected" in guard
    gateway = GATEWAY.read_text(encoding="utf-8")
    assert "protective_sl_tp_missing" in gateway
