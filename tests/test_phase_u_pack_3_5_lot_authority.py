import json
from pathlib import Path

from afip.lot_authority import BASE_LOT, calculate_lot_authority


def profiles():
    raw = json.loads(Path('config/four_profile_demo.json').read_text(encoding='utf-8-sig'))
    return {item['profile_id']: item for item in raw['profiles']}


def test_base_lot_and_three_units_are_split_orders():
    result = calculate_lot_authority(
        profile=profiles()['P1'], decision={'requested_units': 3}, confidence=100,
        balance=1000, equity=1000,
    )
    assert result.base_lot == BASE_LOT == 0.01
    assert result.approved_units == 3
    assert result.approved_lots == (0.01, 0.01, 0.01)
    assert result.total_approved_lot == 0.03


def test_final_units_are_minimum_of_all_gates():
    result = calculate_lot_authority(
        profile=profiles()['P1'], decision={'requested_units': 3}, confidence=100,
        balance=1000, equity=1000, risk_units=2, execution_safety_units=3,
    )
    assert result.approved_units == 2
    assert result.limiting_gate == 'RISK'
    assert result.reason == 'RISK_LIMITED'


def test_capital_gate_prevents_forced_three_orders():
    result = calculate_lot_authority(
        profile=profiles()['P1'], decision={'requested_units': 3}, confidence=100,
        balance=100, equity=100,
    )
    assert result.approved_units == 1
    assert result.approved_lots == (0.01,)
    assert result.reason == 'CAPITAL_LIMITED'


def test_p3_below_200_is_one_unit_not_blocked():
    result = calculate_lot_authority(
        profile=profiles()['P3'], decision={'requested_units': 3}, confidence=100,
        balance=150, equity=150,
    )
    assert result.capital_units == 1
    assert result.approved_units == 1
    assert result.approved_lots == (0.01,)
    assert result.reason == 'CAPITAL_LIMITED'


def test_confidence_gate_and_profile_ceiling_never_exceed_three():
    p = dict(profiles()['P2'])
    p['maximum_units'] = 99
    p['maximum_concurrent_orders'] = 99
    result = calculate_lot_authority(
        profile=p, decision={'requested_units': 99}, confidence=98.6,
        balance=100000, equity=100000,
    )
    assert result.confidence_units == 2
    assert result.approved_units == 2
    assert result.approved_lots == (0.24, 0.24)


def test_deterministic_when_timestamp_is_supplied():
    kwargs = dict(
        profile=profiles()['P2'], decision={'requested_units': 2}, confidence=99,
        balance=600, equity=600, calculated_at='2026-07-20T00:00:00+00:00',
    )
    assert calculate_lot_authority(**kwargs).as_dict() == calculate_lot_authority(**kwargs).as_dict()
