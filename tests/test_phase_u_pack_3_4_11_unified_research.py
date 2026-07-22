from pathlib import Path
from afip.dashboard_ui.research_operations import render_research_operations
from afip.continuous_research_runtime import ContinuousResearchRuntime

def test_dashboard_four_is_research_only(tmp_path: Path):
    html=render_research_operations(tmp_path)
    assert 'Dashboard 4' in html and 'M1' in html and 'D1' in html
    assert 'execution_authority=false' in html and 'order_send_called=false' in html

def test_continuous_runtime_has_visible_status(tmp_path: Path):
    rt=ContinuousResearchRuntime(tmp_path,60,500)
    data=rt._status('RUNNING','TEST','evidence_only')
    assert data['execution_authority'] is False
    assert (tmp_path/'runtime/research/continuous_research_status.json').exists()
