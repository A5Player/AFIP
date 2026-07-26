from afip.dashboard_ui.control_center import render_control_center
from afip.dashboard_ui.research_operations import render_research_operations
from afip.dashboard_ui.split_runtime import ThreeDashboardRuntime


def test_control_center_uses_four_column_grid(tmp_path):
    html = render_control_center(tmp_path)
    assert 'grid-template-columns:repeat(4,minmax(0,1fr))' in html


def test_research_runtime_summary_does_not_require_internal_scroll(tmp_path):
    html = ThreeDashboardRuntime().render_research_html({}, tmp_path)
    assert '.research-status-layout .table-wrap{overflow:visible' in html
    assert '.research-status-layout>.panel:first-child table{table-layout:fixed;font-size:9.5px}' in html


def test_research_operations_has_valid_unicode_labels(tmp_path):
    html = render_research_operations(tmp_path)
    assert '📡 AFIP Dashboard 4 · Data Loading & Research Operations' in html
    assert '📥' in html and 'MT5 Closed Bars' in html
    assert 'ðŸ' not in html
    assert 'â†' not in html
