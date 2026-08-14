from pathlib import Path
import json
from afip.dashboard_ui.split_runtime import SplitDashboardRenderer

def test_dashboard_exposes_a24_summary_without_execution_authority(tmp_path:Path):
    root=tmp_path/'runtime'/'research';root.mkdir(parents=True)
    item={'recommended_action':'RUNNER','timeframe':'H1','market_regime':'TREND',
          'session_name':'LONDON','sample_size':30,'expectancy_after_cost_r':.3,
          'average_holding_seconds':7200}
    (root/'a24_tp_volume_summaries.jsonl').write_text(json.dumps({'record':item})+'\n',encoding='utf-8')
    html=SplitDashboardRenderer().render_research_html({},tmp_path)
    assert 'A20–A23 Holding & Exit Research' in html
    assert 'A24 TP Buffer & Volume-Aware Exit Research' in html
    assert 'MT5 Tick Volume' in html and 'RUNNER' in html and 'no order sent' in html
    assert 'execution authority: NONE' in html
