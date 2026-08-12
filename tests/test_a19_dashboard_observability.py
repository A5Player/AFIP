import json
from pathlib import Path
from afip.dashboard_ui.split_runtime import SplitDashboardRenderer
def test_dashboard_reads_persisted_a18_status(tmp_path: Path):
 p=tmp_path/'runtime'/'research';p.mkdir(parents=True)
 (p/'a18_research_runtime_status.jsonl').write_text(json.dumps({'record':{'status':'RUNNING','progress_current':2,'progress_total':5,'heartbeat_at_utc':'2026-01-01T00:00:00Z','reason_code':'replay_in_progress'}})+'\n',encoding='utf-8')
 html=SplitDashboardRenderer().render_research_html({},tmp_path)
 assert 'A18 Research Runtime Status' in html and 'RUNNING' in html and '2/5' in html and 'RESEARCH_ONLY' in html
