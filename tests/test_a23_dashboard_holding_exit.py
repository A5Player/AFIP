import json
from pathlib import Path
from afip.dashboard_ui.split_runtime import SplitDashboardRenderer
def test_dashboard_renders_persisted_holding_exit_validation_read_only(tmp_path:Path):
 p=tmp_path/'runtime'/'research';p.mkdir(parents=True)
 record={'status':'ROBUST','result_id':'A22-X','partition':{'policy_id':'R_STEP','holding_bucket_id':'SHORT','timeframe':'H1','market_regime':'TREND','session_name':'LONDON'},'blind_forward_samples':30,'blind_forward_expectancy_r':.5,'out_of_sample_degradation_r':.1,'reason':'walk_forward_robust'}
 (p/'a22_holding_exit_validation_results.jsonl').write_text(json.dumps({'record':record})+'\n',encoding='utf-8')
 html=SplitDashboardRenderer().render_research_html({},tmp_path)
 assert 'A20–A23 Holding & Exit Research' in html and 'R_STEP' in html and 'ROBUST' in html
 assert 'no automatic promotion' in html and 'execution authority: NONE' in html
