from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from afip.mt5_historical_integration import MetaTrader5ReadOnlyGateway, write_json_atomic


class FakeRows(list):
    pass


class FakeMT5:
    TIMEFRAME_M1=1; TIMEFRAME_M5=5; TIMEFRAME_M15=15; TIMEFRAME_M30=30
    TIMEFRAME_H1=60; TIMEFRAME_H4=240; TIMEFRAME_D1=1440
    def __init__(self):
        self.range_calls=[]
    def terminal_info(self):
        return SimpleNamespace(connected=True, trade_allowed=False, path=r"C:\MT5", build=5735)
    def account_info(self):
        return SimpleNamespace(login=123456789, company="XM", server="XMGlobal-MT5 6")
    def symbols_get(self):
        return [SimpleNamespace(name="GOLD#"), SimpleNamespace(name="EURUSD")]
    def copy_rates_from(self, symbol, timeframe, when, count):
        return [{"time": 1577836800}]
    def copy_rates_from_pos(self, symbol, timeframe, pos, count):
        return [{"time": 1577836860 if pos == 1 else 1577836800}]
    def copy_rates_range(self, symbol, timeframe, start, end):
        self.range_calls.append((symbol,timeframe,start,end))
        return [
            {"time":1577836800,"open":1,"high":2,"low":0,"close":1.5,"tick_volume":10,"spread":20,"real_volume":0},
            {"time":1577836860,"open":1.5,"high":2.5,"low":1,"close":2,"tick_volume":11,"spread":21,"real_volume":0},
        ]


def test_terminal_evidence_masks_login_and_is_read_only():
    evidence=MetaTrader5ReadOnlyGateway(FakeMT5()).terminal_evidence()
    assert evidence.status=="READY"
    assert evidence.login_masked.endswith("6789") and evidence.login_masked.startswith("*****")
    assert evidence.trade_allowed is False


def test_available_symbols_are_real_terminal_symbols():
    assert tuple(MetaTrader5ReadOnlyGateway(FakeMT5()).available_symbols()) == ("GOLD#","EURUSD")


def test_gateway_resolves_earliest_and_latest_closed_bar():
    gateway=MetaTrader5ReadOnlyGateway(FakeMT5())
    assert gateway.earliest_available("GOLD#","M1")=="2020-01-01T00:00:00+00:00"
    assert gateway.latest_closed_bar("GOLD#","M1")=="2020-01-01T00:01:00+00:00"


def test_fetch_normalizes_mt5_rows_and_advances_cursor():
    gateway=MetaTrader5ReadOnlyGateway(FakeMT5())
    rows=gateway.fetch("GOLD#","M1","2020-01-01T00:00:00+00:00","2020-01-02T00:00:00+00:00",50000)
    assert len(rows)==2 and rows[0]["spread"]==20 and rows[0]["volume"]==10
    assert rows[-1]["next_start_utc"]=="2020-01-01T00:01:01+00:00"


def test_fetch_respects_batch_limit():
    rows=MetaTrader5ReadOnlyGateway(FakeMT5()).fetch("GOLD#","M1","2020-01-01T00:00:00+00:00","2020-01-02T00:00:00+00:00",1)
    assert len(rows)==1 and rows[-1]["next_start_utc"]=="2020-01-01T00:00:01+00:00"


def test_unsupported_timeframe_is_blocked():
    try:
        MetaTrader5ReadOnlyGateway(FakeMT5()).fetch("GOLD#","W1","2020-01-01T00:00:00+00:00","2020-01-02T00:00:00+00:00",1)
    except ValueError as exc:
        assert "Unsupported MT5 timeframe" in str(exc)
    else:
        raise AssertionError("unsupported timeframe was accepted")


def test_atomic_json_writer_replaces_file(tmp_path):
    target=write_json_atomic(tmp_path/"status.json", {"status":"READY"})
    assert target.exists() and '"READY"' in target.read_text(encoding="utf-8")
    assert not (tmp_path/"status.json.tmp").exists()
