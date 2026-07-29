from afip.production_dashboard_certification import build_production_dashboard_snapshot


def ready_source():
    return {
        "runtime": {"status": "RUNNING", "source_authority": "runtime_authority"},
        "execution": {"status": "VERIFIED", "source_authority": "execution_gateway"},
        "position": {"status": "READY", "source_authority": "position_care"},
        "research": {"status": "READY", "source_authority": "research_dataset"},
        "financial": {"status": "VERIFIED", "source_authority": "financial_analytics"},
        "portfolio": {"status": "VERIFIED", "source_authority": "portfolio_authority"},
    }


def test_all_authorities_pass():
    report = build_production_dashboard_snapshot(ready_source())
    assert report["status"] == "PASS"
    assert report["completeness_percent"] == 100.0
    assert report["certification_blockers"] == []


def test_missing_authority_is_not_zero_or_ready():
    source = ready_source(); source.pop("financial")
    report = build_production_dashboard_snapshot(source)
    assert report["status"] == "REVIEW_REQUIRED"
    assert "financial_authority_missing" in report["certification_blockers"]
    financial = next(x for x in report["authority_sections"] if x["section"] == "financial")
    assert financial["status"] == "DATA_UNAVAILABLE"


def test_blocked_execution_blocks_dashboard_certification():
    source = ready_source(); source["execution"] = {"status": "BLOCKED"}
    report = build_production_dashboard_snapshot(source)
    assert report["status"] == "REVIEW_REQUIRED"
    assert "execution_authority_blocked" in report["certification_blockers"]


def test_read_only_safety_contract():
    report = build_production_dashboard_snapshot(ready_source())
    policy = report["truth_policy"]
    assert policy["execution_permission"] is False
    assert policy["affects_trading"] is False
    assert policy["automatic_control_change_allowed"] is False


def test_unknown_status_is_visible_warning():
    source = ready_source(); source["research"] = {"status": "WAITING"}
    report = build_production_dashboard_snapshot(source)
    assert report["status"] == "PASS"
    assert "research_authority_status_waiting" in report["warnings"]


def test_required_sections_are_fixed_and_traceable():
    report = build_production_dashboard_snapshot(ready_source())
    assert report["required_sections"] == ["runtime", "execution", "position", "research", "financial", "portfolio"]
    assert all(item["source_authority"] for item in report["authority_sections"])
