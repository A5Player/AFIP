from pathlib import Path
from afip.automatic_research_runtime.runtime import AutomaticResearchRuntime

def test_research_index_is_written_and_unchanged_non_ohlc_is_skipped(tmp_path: Path):
    p=tmp_path/'data/research/events.jsonl'; p.parent.mkdir(parents=True); p.write_text('{"event":"x"}\n')
    r=AutomaticResearchRuntime(tmp_path)
    bars, files, scanned, rejected=r.discover_bars(); assert bars==[] and rejected==1
    bars, files, scanned, rejected=r.discover_bars(); assert bars==[] and rejected==1
    assert r.discovery_index_path.exists()
    assert 'skipped_unchanged_non_ohlc_files' in r.discovery_index_path.read_text()

def test_historical_data_lake_is_read_before_mt5(tmp_path: Path):
    p=tmp_path/'runtime/research/historical_data_lake/layer=normalized/domain=market_ohlc/instrument=GOLD#/year=2026/month=01/day=01/records.jsonl'
    p.parent.mkdir(parents=True)
    p.write_text('{"observed_at_utc":"2026-01-01T00:00:00+00:00","payload":{"timeframe":"M1","open":1,"high":2,"low":0.5,"close":1.5,"volume":10}}\n')
    bars, *_ = AutomaticResearchRuntime(tmp_path).discover_bars()
    assert len(bars)==1 and bars[0]['timeframe']=='M1'

def test_background_scripts_exist():
    root=Path(__file__).resolve().parents[1]
    for name in ('START_AFIP_RESEARCH_BACKGROUND.ps1','STOP_AFIP_RESEARCH_BACKGROUND.ps1','STATUS_AFIP_RESEARCH_BACKGROUND.ps1'):
        assert (root/name).exists()
