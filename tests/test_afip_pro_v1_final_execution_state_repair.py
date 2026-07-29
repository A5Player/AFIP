from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from afip.dashboard_state_machine import normalize_profile_state
from afip.dashboard_ui.split_runtime import _profile_rows
from afip.live_mt5_snapshot_authority import publish_live_mt5_snapshot


class FakeMT5:
    def symbol_info_tick(self, symbol):
        return SimpleNamespace(bid=4049.50, ask=4049.80)

    def symbol_info(self, symbol):
        return SimpleNamespace(point=0.01, digits=2)

    def terminal_info(self):
        return SimpleNamespace(connected=True)

    def positions_get(self, symbol=None):
        return [SimpleNamespace(
            ticket=123456, identifier=123456, symbol=symbol, type=0,
            volume=0.01, price_open=4040.0, price_current=4049.5,
            sl=4020.0, tp=4090.0, profit=9.5, swap=0.0,
            magic=1001, comment='AFIP', time=1, time_msc=1000,
        )]

    def orders_get(self, symbol=None):
        return []


def test_live_snapshot_contains_position_details(tmp_path: Path):
    profile = SimpleNamespace(
        profile_id='P1', symbol='GOLD#', runtime_directory=tmp_path,
        enabled=True, login='123456', server='XMGlobal-MT5 6',
        mt5_terminal='C:/XM/terminal64.exe',
    )
    account = SimpleNamespace(
        login=123456, server='XMGlobal-MT5 6', currency='USD',
        balance=100.0, equity=109.5, margin=4.0, margin_free=105.5,
        profit=9.5, trade_allowed=True,
    )
    payload = publish_live_mt5_snapshot(profile=profile, mt5=FakeMT5(), account=account)
    assert payload['positions_total'] == 1
    assert payload['position_tickets'] == [123456]
    assert payload['positions'][0]['entry_price'] == 4040.0
    assert payload['positions'][0]['current_price'] == 4049.5
    assert payload['positions'][0]['stop_loss'] == 4020.0
    assert payload['positions'][0]['take_profit'] == 4090.0


def _row_map(profile):
    return {label: value for _, label, value in _profile_rows(profile)}


def test_open_position_is_not_rendered_as_no_position():
    profile = {
        'positions_total': 1,
        'has_open_position': True,
        'live_positions': [{
            'ticket': 123456, 'entry_price': 4040.0, 'current_price': 4049.5,
            'stop_loss': 4020.0, 'take_profit': 4090.0,
        }],
        'position_tickets': [123456],
        'position_reconciliation_state': 'MATCHED_LIVE_POSITION',
        'trade_plan_id': 'PLAN-ABC',
        'position_care_action': 'OBSERVING_OPEN_POSITION',
        'holding_reason': 'LIVE_POSITION_PRESENT',
        'normalized_order_status': 'ORDER_SENT',
        'sent_units': 1,
        'data_fresh': True,
        'runtime_truth': {},
        'operations_health': {},
    }
    rows = _row_map(profile)
    assert rows['Trade plan'] == 'PLAN-ABC'
    assert rows['Entry / Current'] == '4040.0 / 4049.5'
    assert rows['SL / TP'] == '4020.0 / 4090.0'
    assert rows['Position care'] == 'OBSERVING_OPEN_POSITION'
    assert rows['Holding reason'] == 'LIVE_POSITION_PRESENT'
    assert rows['Order / Units'] == 'ORDER_SENT / 1'


def test_no_position_remains_waiting_for_entry():
    rows = _row_map({
        'positions_total': 0,
        'data_fresh': True,
        'runtime_truth': {},
        'operations_health': {},
    })
    assert rows['SL / TP'] == 'NO_OPEN_POSITION'
    assert rows['Position care'] == 'NOT_ACTIVE'
    assert rows['Holding reason'] == 'WAITING_FOR_ENTRY'


def test_completed_order_event_is_not_permanently_active():
    profile = {
        'runtime_state': 'RUNNING',
        'connection_status': 'CONNECTED',
        'gateway_status': 'ORDER_SENT',
        'order_status': 'ORDER_SENT',
        'has_open_position': True,
        'source_metadata': {
            'profile_status': {'fresh': True},
            'runtime_authority': {'fresh': True},
            'mt5_health': {'fresh': True},
            'execution_state': {'fresh': True, 'exists': True, 'modified_at_utc': '2099-01-01T00:00:00+00:00'},
        },
    }
    truth = normalize_profile_state(profile)
    assert truth['gateway_current'] == 'WAITING'
    assert truth['current_reason'] == 'open_position_observed_after_order_sent'
    assert truth['normalized_order_status'] == 'ORDER_SENT'
