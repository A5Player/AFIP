from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]


def load_module():
    path = ROOT / "tools" / "afip_phase_u_final_research.py"
    spec = importlib.util.spec_from_file_location("afip_phase_u_final_research", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_final_runner_exists_and_has_no_execution_authority():
    text = (ROOT / "tools" / "afip_phase_u_final_research.py").read_text(encoding="utf-8")
    assert '"execution_authority": False' in text
    assert "subprocess.run" in text
    assert "timeout=" in text


def test_final_powershell_runner_calls_bounded_orchestrator():
    text = (ROOT / "RUN_AFIP_FINAL_RESEARCH.ps1").read_text(encoding="utf-8")
    assert "afip_phase_u_final_research.py" in text
    assert "$LASTEXITCODE" in text
    assert "CollectorTimeoutSeconds" in text


def test_run_step_timeout_is_reported(tmp_path):
    module = load_module()
    result = module.run_step("timeout_probe", [__import__("sys").executable, "-c", "import time; time.sleep(2)"], 1)
    assert result["status"] == "TIMEOUT"
