import json
from pathlib import Path

from afip.dashboard_ui.split_runtime import ThreeDashboardRuntime


def test_research_ranking_keeps_data_quality_and_evidence_sections(tmp_path: Path) -> None:
    status_path = tmp_path / "runtime" / "research" / "automatic_research_status.json"
    status_path.parent.mkdir(parents=True)
    status_path.write_text(json.dumps({"status": "READY", "timeframe_data_quality": {}}), encoding="utf-8")
    html = ThreeDashboardRuntime().render_research_html({}, tmp_path)
    assert "Research-to-trading connection audit" in html
    assert "research-status-layout" in html
    assert 'class="research-evidence-grid"' in html
    for timeframe in ("M1", "M5", "M15", "M30", "H1", "H4", "D1"):
        assert f"<b>{timeframe}</b>" in html
