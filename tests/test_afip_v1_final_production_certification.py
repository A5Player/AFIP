from __future__ import annotations
import os, subprocess
from pathlib import Path
from unittest.mock import patch

from afip.final_integration.research_engine import UnifiedResearchEngine
from afip.final_integration.runtime import FinalIntegrationRuntime


def test_research_cycle_keeps_service_running(tmp_path: Path) -> None:
    engine = UnifiedResearchEngine(tmp_path)
    with patch("afip.phase_v_major.PhaseVMajorRuntime.run_once", return_value={}):
        result = engine.run_once()
    assert result["status"] == "RUNNING"
    assert result["service_state"] == "RUNNING"
    assert result["cycle_status"] == "READY"
    assert result["execution_authority"] is False


def test_research_cycle_error_does_not_stop_service(tmp_path: Path) -> None:
    engine = UnifiedResearchEngine(tmp_path)
    with patch("afip.phase_v_major.PhaseVMajorRuntime.run_once", side_effect=RuntimeError("boom")):
        result = engine.run_once()
    assert result["status"] == "RUNNING"
    assert result["cycle_status"] == "ERROR"


def test_background_spawn_is_console_isolated(tmp_path: Path) -> None:
    runtime = FinalIntegrationRuntime(tmp_path)
    runtime.logs.mkdir(parents=True)
    runtime.control.mkdir(parents=True)
    proc = type("P", (), {"pid": 4321})()
    with patch("afip.final_integration.runtime.subprocess.Popen", return_value=proc) as popen:
        with patch("afip.final_integration.runtime.pid_running", return_value=False):
            runtime._spawn(runtime.research_pid_path, ["python", "service"], "service.log")
    kwargs = popen.call_args.kwargs
    if os.name == "nt":
        assert kwargs["creationflags"] & getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        assert kwargs["start_new_session"] is True
