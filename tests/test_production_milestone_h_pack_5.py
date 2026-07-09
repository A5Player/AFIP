from afip.dashboard_center import DashboardRuntimeStatus, HistoricalDataDownloadPipeline
from afip.historical_data_manager import default_download_steps


def _ready_record():
    return {
        "profile_name": "Research",
        "profile_type": "Research",
        "broker": "XM",
        "symbol": "GOLD#",
        "mt5_status": "connected",
        "broker_status": "connected",
        "internet_status": "online",
        "login": "123456",
        "password": "secret",
        "mt5_terminal_path": "C:/Program Files/MetaTrader 5/terminal64.exe",
        "historical_download_requested": True,
        "downloaded_bars": 60000,
        "missing_bars": 0,
        "duplicate_bars": 0,
        "invalid_bars": 0,
        "requested_days": 365,
        "timeframes": ("M1", "M5", "M15", "H1", "H4", "D1"),
        "heartbeat_age_seconds": 5,
        "cpu_percent": 12,
        "ram_percent": 35,
        "disk_percent": 44,
    }


def test_historical_download_pipeline_accepts_xm_gold_all_required_timeframes():
    report = HistoricalDataDownloadPipeline().evaluate_one(_ready_record())
    assert report.status == "READY"
    assert report.broker == "XM"
    assert report.symbol == "GOLD#"
    assert report.walk_forward_ready is True
    assert report.research_ready is True
    assert report.paper_trading_ready is True
    assert report.live_execution_enabled is False


def test_historical_download_pipeline_blocks_non_xm_or_non_gold_version1_policy():
    record = _ready_record() | {"broker": "EXNESS", "symbol": "XAUUSD"}
    report = HistoricalDataDownloadPipeline().evaluate_one(record)
    assert report.status == "WAITING"
    assert "version1_xm_only_required" in report.validation_items
    assert "version1_gold_only_required" in report.validation_items
    assert report.trading_logic_changed is False


def test_historical_download_pipeline_detects_missing_duplicate_and_invalid_bars():
    record = _ready_record() | {"missing_bars": 8, "duplicate_bars": 3, "invalid_bars": 1}
    report = HistoricalDataDownloadPipeline().evaluate_one(record)
    assert report.status in {"WAITING", "REVIEW"}
    assert "missing_bars_detected" in report.validation_items
    assert "duplicate_bars_detected" in report.validation_items
    assert "invalid_bars_detected" in report.validation_items
    assert report.quality_score < 100


def test_historical_download_pipeline_requires_all_core_timeframes_for_walk_forward():
    record = _ready_record() | {"timeframes": ("H1", "H4", "D1"), "downloaded_bars": 60000}
    report = HistoricalDataDownloadPipeline().evaluate_one(record)
    assert report.walk_forward_ready is False
    assert "required_timeframes_missing" in report.validation_items
    assert report.research_ready is True


def test_download_steps_have_thai_and_english_explainability():
    steps = default_download_steps()
    assert len(steps) >= 5
    assert all(step.thai_name for step in steps)
    assert all(step.description for step in steps)
    assert all(step.waiting_reason for step in steps)
    assert steps[-1].output == "datasets_ready"


def test_research_and_live_statistics_are_separated_in_quality_report():
    report = HistoricalDataDownloadPipeline().evaluate_one(_ready_record())
    assert report.research_statistics_scope == "RESEARCH_ONLY"
    assert report.live_statistics_scope == "LIVE_SEPARATE"
    assert "Research Ready: True" in report.as_text()


def test_dashboard_runtime_includes_historical_download_dependency():
    report = DashboardRuntimeStatus().evaluate_one(_ready_record())
    assert report.historical_download_status == "READY"
    assert "historical_download_status" in report.as_dict()
    assert "historical_download" not in report.decision_explainability_sections
