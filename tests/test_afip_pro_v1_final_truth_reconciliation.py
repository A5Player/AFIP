from pathlib import Path
from types import SimpleNamespace

from afip.live_mt5_snapshot_authority import publish_live_mt5_snapshot
from afip.runtime_truth import build_profile_truth
from afip.dashboard_state_machine import normalize_profile_state
from afip.dashboard_ui.split_runtime import _live_position_summary


class FakeMT5:
    def symbol_info_tick(self, symbol):
        return SimpleNamespace(bid=4042.33, ask=4042.63)
    def symbol_info(self, symbol):
        return SimpleNamespace(point=0.01, digits=2)
    def terminal_info(self):
        return SimpleNamespace(connected=True)
    def positions_get(self, symbol):
        return (SimpleNamespace(ticket=123, symbol=symbol, type=1, volume=0.01,
            price_open=4050.0, price_current=4042.33, sl=4070.0, tp=4000.0,
            profit=7.67, swap=0.0, comment='AFIP', magic=77, time=1, time_msc=1000),)
    def orders_get(self, symbol):
        return ()


def test_live_snapshot_publishes_position_details(tmp_path: Path):
    profile = SimpleNamespace(profile_id='P1', symbol='GOLD#', runtime_directory=tmp_path,
                              login='123456', server='S', mt5_terminal='terminal64.exe', enabled=True)
    account = SimpleNamespace(login='123456', server='S', currency='USD', balance=100,
                              equity=107.67, margin=4, margin_free=103.67, profit=7.67,
                              trade_allowed=True)
    result = publish_live_mt5_snapshot(profile=profile, mt5=FakeMT5(), account=account)
    assert result['position_tickets'] == [123]
    assert result['positions'][0]['side'] == 'SELL'
    assert result['positions'][0]['entry_price'] == 4050.0
    assert result['verified_snapshot'] is True


def test_read_only_existing_session_is_connected_truth():
    truth = build_profile_truth({
        'profile_id': 'P1', 'enabled': True, 'process_alive': True,
        'monitoring_mode': 'EXISTING_RUNTIME_SESSION_READ_ONLY',
        'connection_status': 'CONNECTED', 'evidence_kind': 'LIVE',
        'balance': 100, 'equity': 101, 'free_margin': 97, 'bid': 1, 'ask': 2,
        'data_fresh': True, 'runtime_state': 'RUNNING',
    })
    assert truth['broker_session_state'] == 'CONNECTED'
    assert truth['financial_state'] == 'LIVE'
    assert truth['observation_current'] is True


def test_live_tick_evidence_sets_market_open_and_normalizes_reason():
    result = normalize_profile_state({
        'runtime_state': 'RUNNING', 'bid': 4042.33, 'ask': 4042.63, 'data_fresh': True,
        'demo_gateway_status': 'WAITING', 'demo_gateway_reason': 'waiting_for_runtime_evidence',
        'source_metadata': {
            'mt5_health': {'exists': True, 'fresh': True},
            'profile_status': {'exists': True, 'fresh': True},
            'execution_state': {'exists': True, 'fresh': True, 'modified_at_utc': '2099-01-01T00:00:00+00:00'},
            'runtime_authority': {'fresh': True},
        },
        'connection_status': 'CONNECTED',
    })
    assert result['market_current'] == 'OPEN_TICKING'
    assert result['market_current_source'] == 'LIVE_TICK_EVIDENCE'
    assert result['current_reason'] == 'waiting_for_next_runtime_cycle'


def test_live_position_summary_never_claims_no_active_position():
    result = _live_position_summary({'positions': [{
        'ticket': 123, 'entry_price': 4050.0, 'current_price': 4042.33,
        'sl': 4070.0, 'tp': 4000.0,
    }]})
    assert result['trade_plan'] == 'UNMATCHED_LIVE_POSITION'
    assert result['care'] == 'LIVE_POSITION_OBSERVED'
    assert result['tickets'] == '123'
    assert 'NO_ACTIVE_POSITION' not in result.values()
