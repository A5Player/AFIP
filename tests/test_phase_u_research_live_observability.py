import json
from pathlib import Path
from afip.research_live_dashboard import TIMEFRAMES, build_live_snapshot, write_live_dashboard

def test_live_snapshot_is_evidence_only_and_execution_safe(tmp_path: Path):
    lake=tmp_path/'runtime/research/historical_data_lake/timeframe=M1'
    lake.mkdir(parents=True)
    (lake/'bars.json').write_text(json.dumps({'bars':[{},{}]}),encoding='utf-8')
    snapshot=build_live_snapshot(tmp_path,'REPLAY_RESEARCH','test')
    assert snapshot['execution_authority'] is False
    assert snapshot['order_send_called'] is False
    assert snapshot['timeframe_coverage']['M1']['record_count']==2
    assert snapshot['timeframe_coverage']['D1']['status']=='DATA_UNAVAILABLE'
    assert tuple(snapshot['timeframe_coverage'])==TIMEFRAMES

def test_live_dashboard_contains_required_timeframes(tmp_path: Path):
    path=write_live_dashboard(tmp_path)
    text=path.read_text(encoding='utf-8')
    assert 'AFIP Research Live Dashboard' in text
    for timeframe in TIMEFRAMES: assert f'>{timeframe}<' in text
    assert 'execution_authority=false' in text
