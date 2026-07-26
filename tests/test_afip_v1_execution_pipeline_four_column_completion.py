from afip.execution_pipeline_dashboard import build_profile_pipeline, render_execution_pipeline_dashboard


def test_pipeline_is_fixed_four_column_comparison():
    contract = {"generated_at_utc": "2026-07-26T00:00:00+00:00", "execution_pipelines": [
        {"profile_id": f"P{i}", "profile_name": "Profile", "trace_id": "x", "data_status": "FRESH", "data_age_seconds": 1,
         "evidence_mode": "LIVE", "overall_status": "WAITING", "current_stage": "market_feed", "reason": "waiting", "stages": []}
        for i in range(1, 5)
    ]}
    html = render_execution_pipeline_dashboard(contract)
    assert "grid-template-columns:repeat(4,minmax(0,1fr))" in html
    assert "P1–P4 Comparison" in html


def test_stopped_runtime_is_not_presented_as_live_order_sent():
    profile = {
        "profile_id": "P1", "runtime_state": "STOPPED", "gateway_status": "ORDER_SENT",
        "gateway_reason": "protected_demo_orders_sent",
        "source_metadata": {"execution_state": {"fresh": False, "age_seconds": 900}, "profile_status": {"fresh": False, "age_seconds": 800}},
    }
    pipe = build_profile_pipeline(profile)
    assert pipe["overall_status"] == "INACTIVE"
    assert pipe["evidence_mode"] == "INACTIVE"
    assert pipe["reason"] == "runtime_not_currently_running"
    assert pipe["data_age_seconds"] == 900
