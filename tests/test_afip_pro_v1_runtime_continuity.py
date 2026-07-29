from pathlib import Path

from afip.final_integration.runtime import FinalIntegrationRuntime


def test_desired_state_defaults_to_stopped(tmp_path: Path) -> None:
    runtime = FinalIntegrationRuntime(tmp_path)
    assert runtime._desired_state() == "STOPPED"


def test_desired_state_round_trip(tmp_path: Path) -> None:
    runtime = FinalIntegrationRuntime(tmp_path)
    runtime.control.mkdir(parents=True, exist_ok=True)
    runtime._write_desired_state("RUNNING", "test")
    assert runtime._desired_state() == "RUNNING"


def test_ensure_services_does_nothing_when_intentionally_stopped(tmp_path: Path) -> None:
    runtime = FinalIntegrationRuntime(tmp_path)
    result = runtime.ensure_services()
    assert result["status"] == "IDLE"
    assert result["actions"] == []


def test_watchdog_source_has_no_mt5_or_order_authority() -> None:
    source = Path("tools/afip_runtime_continuity_watchdog.py").read_text(encoding="utf-8")
    forbidden_calls = ("mt5.initialize(", "order_send(", "order_check(", "terminal64.exe")
    assert all(value not in source for value in forbidden_calls)
