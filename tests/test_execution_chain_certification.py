from __future__ import annotations
import json
from pathlib import Path

from afip.lot_authority import calculate_lot_authority
from afip.position_policy import requested_units_within_confidence_ceiling

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config" / "four_profile_demo.json").read_text(encoding="utf-8-sig"))
PROFILES = {p["profile_id"]: p for p in CONFIG["profiles"]}


def authority(pid, balance, confidence, decision=None, **kwargs):
    return calculate_lot_authority(
        profile=PROFILES[pid], decision=decision or {}, confidence=confidence,
        balance=balance, equity=kwargs.pop("equity", balance), current_orders=kwargs.pop("current_orders", 0), **kwargs,
    )


def test_confidence_is_ceiling_not_three_unit_target():
    resolved = requested_units_within_confidence_ceiling({}, 100.0)
    assert resolved.confidence_maximum_units == 3
    assert resolved.requested_units == 1
    assert resolved.approved_units == 1


def test_current_balances_do_not_force_three_orders():
    assert authority("P1", 70.19, 99.7, {"requested_units": 3}).approved_units == 1
    assert authority("P2", 272.10, 99.7, {"requested_units": 3}).approved_units == 1
    assert authority("P3", 875.37, 99.7, {}).approved_units == 1
    assert authority("P4", 17.26, 99.7, {"requested_units": 3}).approved_units == 1


def test_three_orders_require_explicit_request_and_all_gates():
    result = authority("P3", 875.37, 99.7, {"requested_units": 3})
    assert result.approved_units == 3
    assert result.approved_lots == (0.01, 0.01, 0.01)


def test_confidence_reduces_explicit_three_request():
    result = authority("P3", 875.37, 98.7, {"requested_units": 3})
    assert result.confidence_units == 2
    assert result.approved_units == 2


def test_risk_and_execution_caps_reduce_units():
    assert authority("P3", 875.37, 100.0, {"requested_units": 3}, risk_units=1).approved_units == 1
    assert authority("P3", 875.37, 100.0, {"requested_units": 3}, execution_safety_units=1).approved_units == 1


def test_open_orders_reduce_remaining_capacity():
    result = authority("P3", 875.37, 100.0, {"requested_units": 3}, current_orders=2)
    assert result.capital_units == 1
    assert result.approved_units == 1


def test_zero_equity_is_fail_closed():
    result = authority("P3", 875.37, 100.0, {"requested_units": 3}, equity=0.0)
    assert result.available_capital == 0.0
    assert result.capital_units == 0
    assert result.approved_units == 0


def test_no_approved_lot_exceeds_single_unit_size_at_current_tiers():
    balances = {"P1": 70.19, "P2": 272.10, "P3": 875.37, "P4": 17.26}
    for pid, balance in balances.items():
        result = authority(pid, balance, 100.0, {"requested_units": 3})
        assert all(lot == 0.01 for lot in result.approved_lots)
