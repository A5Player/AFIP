from afip.dashboard_completeness import assess_dashboard_completeness, write_dashboard_completeness


def test_complete_mt5_profile_reports_full_required_coverage(tmp_path):
    contract={"profiles":[{"profile_id":"P1","account":"****1","server":"S","currency":"USD","balance":90,"equity":90,"free_margin":90,"positions_total":0,"orders_total":0,"bid":1,"ask":2,"spread_points":1,"connection_status":"CONNECTED","checked_at_utc":"now"}],"research":{}}
    result=assess_dashboard_completeness(contract)
    assert result["profiles"][0]["required_coverage_percent"] == 100.0
    assert result["research"]["ranking_status"] == "NOT_GENERATED"


def test_missing_fields_are_reported_not_invented():
    result=assess_dashboard_completeness({"profiles":[{"profile_id":"P1"}],"research":{}})
    assert "balance" in result["profiles"][0]["required_missing"]
    assert result["research"]["data_status"] == "DATA_UNAVAILABLE"


def test_completeness_html_is_written(tmp_path):
    path=write_dashboard_completeness({"profiles":[],"research":{}},tmp_path)
    text=path.read_text(encoding="utf-8")
    assert "Dashboard Data Completeness" in text
    assert "No values are invented" in text
