from pathlib import Path

from afip.final_integration.continuous_research import ContinuousResearchPipeline


def test_a37_is_incremental_fail_closed_and_research_only(tmp_path: Path):
    pipeline = ContinuousResearchPipeline(tmp_path)
    result = pipeline.run_once()
    assert result["execution_authority"] == "NONE"
    assert result["orders_sent"] is False
    assert result["profile_strategy_selection"] == "NOT_DECIDED"
    assert result["mt5_collection_authority"] == "EXISTING_PHASE_V_ONLY"
    assert all(item["stage"] != "A36_ACTIVE_COLLECTION" for item in result["stages"])


def test_a37_unchanged_inputs_do_not_run_heavy_stages_twice(tmp_path: Path):
    pipeline = ContinuousResearchPipeline(tmp_path)
    first = pipeline.run_once()
    second = pipeline.run_once()
    names = {item["stage"] for item in second["stages"]}
    assert "A32_A33_BACKTEST_RANKING" not in names
    assert "A35_ATR_BUFFER" not in names
    assert second["execution_authority"] == "NONE"


def test_a37_source_has_no_mt5_or_order_authority():
    source = Path(__file__).resolve().parents[1] / "afip/final_integration/continuous_research.py"
    text = source.read_text(encoding="utf-8")
    assert "MetaTrader5" not in text
    assert ".order_send(" not in text
    assert ".order_check(" not in text


def test_a31_continuous_stage_has_snapshot_idempotency_guard():
    source = Path(__file__).resolve().parents[1] / "tools/afip_a31_daily_participation_research.py"
    text = source.read_text(encoding="utf-8")
    assert "source_snapshot_id" in text
    assert "ALREADY_CURRENT" in text


def test_dashboard_exposes_a37_status_without_execution_authority(tmp_path: Path):
    from afip.dashboard_ui.split_runtime import SplitDashboardRenderer
    html = SplitDashboardRenderer().render_research_html({}, tmp_path)
    assert "A37 Continuous Research Pipeline" in html
    assert "Execution authority: NONE" in html
