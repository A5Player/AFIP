from afip.runtime_coverage import RuntimeCoverageRuntime
from afip.dashboard_ui.runtime import DashboardUIRuntime

def test_default_report_is_integration_required():
 r=RuntimeCoverageRuntime().evaluate_one({}); assert r.status=="INTEGRATION_REQUIRED"; assert r.execution_permission is False; assert r.total_components==14

def test_trade_plan_foundation_is_visible_but_not_connected_by_default():
 r=RuntimeCoverageRuntime().evaluate_one({}); x=next(i for i in r.items if i.component_id=="trade_plan_runtime"); assert x.dashboard_visible; assert not x.runtime_connected; assert x.status=="FOUNDATION_ONLY"

def test_record_can_certify_all_components_connected():
 ids=[x[0] for x in RuntimeCoverageRuntime.COMPONENTS]; r=RuntimeCoverageRuntime().evaluate_one({"runtime_connected_components":ids,"dataset_registered_components":ids,"decision_trace_components":ids,"dashboard_visible_components":ids,"test_covered_components":ids}); assert r.status=="READY"; assert r.coverage_percent==100.0

def test_dashboard_contains_prominent_coverage_matrix():
 html=DashboardUIRuntime().render_html({"mode":"SIMULATION","broker":"XM","symbol":"GOLD#"}); assert "Runtime Coverage Matrix" in html; assert "สร้างแล้ว ≠ เชื่อม Runtime แล้ว" in html; assert "Execution Permission" in html
