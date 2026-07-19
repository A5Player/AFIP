from datetime import datetime, timedelta, timezone
from afip.historical_dataset_certification import HistoricalDatasetCertifier


def bars(count=120, missing_at=None):
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    out=[]
    for tf, seconds in {"M1":60,"M5":300,"M15":900,"M30":1800,"H1":3600,"H4":14400,"D1":86400}.items():
        for index in range(count):
            if missing_at == (tf,index): continue
            out.append({"timeframe":tf,"timestamp_utc":(start+timedelta(seconds=seconds*index)).isoformat(),"open":2000,"high":2002,"low":1999,"close":2001})
    return out


def policy(**changes):
    value={"minimum_valid_records":100,"minimum_coverage_days":0,"maximum_missing_ratio_ready":0.02,"maximum_missing_ratio_caution":0.10}
    value.update(changes); return value


def test_complete_dataset_is_ready():
    report=HistoricalDatasetCertifier(policy()).certify(bars(),instrument="GOLD#",source_id="TEST")
    assert report.overall_status == "READY"
    assert report.research_eligible is True
    assert len(report.ready_timeframes) == 7


def test_small_gap_is_caution():
    report=HistoricalDatasetCertifier(policy(maximum_missing_ratio_ready=0)).certify(bars(missing_at=("M1",50)),instrument="GOLD#",source_id="TEST")
    assert report.overall_status == "CAUTION"
    assert report.research_eligible is True


def test_missing_timeframe_is_quarantined():
    data=[r for r in bars() if r["timeframe"] != "D1"]
    report=HistoricalDatasetCertifier(policy()).certify(data,instrument="GOLD#",source_id="TEST")
    assert report.overall_status == "QUARANTINED"
    assert "D1" in report.quarantined_timeframes
    assert report.research_eligible is False


def test_invalid_price_is_quarantined():
    data=bars(); data[0]["low"]=-1
    report=HistoricalDatasetCertifier(policy()).certify(data,instrument="GOLD#",source_id="TEST")
    assert report.overall_status == "QUARANTINED"


def test_dataset_id_is_deterministic():
    c=HistoricalDatasetCertifier(policy())
    a=c.certify(bars(),instrument="GOLD#",source_id="TEST")
    b=c.certify(bars(),instrument="GOLD#",source_id="TEST")
    assert a.dataset_id == b.dataset_id
