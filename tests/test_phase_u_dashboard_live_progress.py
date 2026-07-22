from pathlib import Path
import json
from afip.dashboard_ui.live_research_dashboard import build

def test_builds_single_four_page_dashboard(tmp_path:Path):
 p=tmp_path/'runtime/research/automatic_research_status.json';p.parent.mkdir(parents=True)
 p.write_text(json.dumps({'status':'RUNNING','stage':'REPLAY_RESEARCH','current_timeframe':'H1','replay_bars_processed':19415}),encoding='utf-8')
 out=build(tmp_path)
 text=out.read_text(encoding='utf-8')
 assert 'AFIP Unified Production Dashboard · 4 Pages' in text
 assert 'H1' in text and '19415' in text
 assert 'Execution authority' in text
