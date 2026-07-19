from pathlib import Path

from afip.automatic_research_runtime import AutomaticResearchRuntime


def test_runtime_accepts_progress_reporter(tmp_path: Path) -> None:
    messages: list[str] = []
    summary = AutomaticResearchRuntime(tmp_path, progress=messages.append).run(collect_mt5_when_needed=False)
    assert summary.status == "WAITING"
    assert any("Scanning existing" in message for message in messages)
    assert any("Running chronological replay" in message for message in messages)
    assert any("Complete:" in message for message in messages)


def test_running_stage_is_visible_in_status_file(tmp_path: Path) -> None:
    runtime = AutomaticResearchRuntime(tmp_path)
    runtime._write_stage("TEST_STAGE", "test_reason")
    text = runtime.status_path.read_text(encoding="utf-8")
    assert '"status": "RUNNING"' in text
    assert '"stage": "TEST_STAGE"' in text
    assert '"order_send_called": false' in text


def test_run_script_uses_unbuffered_cli_and_opens_dashboard() -> None:
    script = Path("RUN_PHASE_U_PACK_3_2_1.ps1").read_text(encoding="utf-8")
    assert "python -u afip.py research-bootstrap" in script
    assert "Start-Process" in script
    assert "afip_research_data_dashboard.html" in script
