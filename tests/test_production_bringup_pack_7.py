from afip.historical_data_manager import HistoricalDataLiveRuntime
from afip.dashboard_ui import DashboardUIRuntime


def test_pack7_ready_for_xm_gold_complete_history():
    report = HistoricalDataLiveRuntime().evaluate_one({"broker":"XM","symbol":"GOLD#","bars_per_timeframe":20})
    assert report.status == "READY"
    assert report.walk_forward_ready is True
    assert report.live_execution_enabled is False


def test_pack7_waits_for_empty_history():
    report = HistoricalDataLiveRuntime().evaluate_one({"broker":"XM","symbol":"GOLD#","bars_per_timeframe":0})
    assert report.status == "WAITING"
    assert report.research_ready is False


def test_pack7_reviews_missing_bars():
    report = HistoricalDataLiveRuntime().evaluate_one({"broker":"XM","symbol":"GOLD#","bars_per_timeframe":100,"historical_missing_bars":1})
    assert report.status == "REVIEW"
    assert report.walk_forward_ready is False


def test_pack7_blocks_non_version1_policy():
    report = HistoricalDataLiveRuntime().evaluate_one({"broker":"OTHER","symbol":"GOLD#","bars_per_timeframe":20})
    assert report.status == "BLOCKED"


def test_pack7_dashboard_contains_bilingual_history_panel():
    html = DashboardUIRuntime().render_html({"broker":"XM","symbol":"GOLD#","mode":"PAPER","bars_per_timeframe":20})
    assert "Historical Data Manager" in html
    assert "ตัวจัดการข้อมูลย้อนหลัง" in html
    assert "Walk Forward Ready" in html


def test_pack7_is_read_only_and_deterministic():
    runtime = HistoricalDataLiveRuntime()
    record = {"broker":"XM","symbol":"GOLD#","bars_per_timeframe":20}
    assert runtime.evaluate_one(record) == runtime.evaluate_one(record)
    assert runtime.evaluate_one(record).trading_logic_changed is False
