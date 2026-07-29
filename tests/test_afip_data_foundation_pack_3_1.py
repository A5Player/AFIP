from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from afip.mt5_historical_integration.mt5_gateway import MetaTrader5ReadOnlyGateway
from afip.mt5_historical_integration.runtime import ResumableMT5HistoricalProvider
from afip.runtime_standard_adapter import BackfillRequest


class RangeFallbackMT5:
    TIMEFRAME_M1 = 1
    def __init__(self):
        self.calls=[]
    def symbol_select(self,*a): return True
    def copy_rates_range(self, symbol, tf, start, end):
        self.calls.append((start,end))
        if len(self.calls)==1: return []
        epoch=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp())+10800
        return [{"time":epoch,"open":1.0,"high":2.0,"low":0.5,"close":1.5,"tick_volume":1,"spread":1,"real_volume":0}]


def test_range_fetch_retries_without_broker_offset():
    fake=RangeFallbackMT5(); g=MetaTrader5ReadOnlyGateway(fake); g._broker_time_offset_seconds=10800
    rows=g.fetch("GOLD#","M1","2026-01-01T00:00:00+00:00","2026-01-01T01:00:00+00:00",100)
    assert len(fake.calls)==2
    assert len(rows)==1
    assert rows[0]["timestamp_utc"]=="2026-01-01T00:00:00+00:00"


class EmptyGateway:
    def available_symbols(self): return ["GOLD#"]
    def earliest_available(self,*a): return "2026-01-01T00:00:00+00:00"
    def latest_closed_bar(self,*a): return "2026-01-02T00:00:00+00:00"
    def fetch(self,*a): return []


def test_empty_discovered_range_is_not_falsely_completed(tmp_path: Path):
    req=BackfillRequest("R1","GOLD#","M1",None,None,50000)
    result=ResumableMT5HistoricalProvider(tmp_path).run(req,EmptyGateway(),1)
    assert result.status=="NO_DATA"
    assert result.reason=="provider_returned_no_rows_for_discovered_range"
    assert result.quality_status=="UNKNOWN"
