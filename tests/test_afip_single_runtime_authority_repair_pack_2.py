from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_safe_start_preserves_account_isolation_preflight() -> None:
    text = _text("START_AFIP_SAFE.ps1")
    assert "tools.afip_verify_account_isolation" in text
    assert "SAFE START BLOCKED" in text


def test_safe_start_delegates_to_canonical_start() -> None:
    text = _text("START_AFIP_SAFE.ps1")
    assert "START_AFIP.ps1" in text
    assert "tools.afip_demo_execution_control start-all" not in text
    assert "FINAL_INTEGRATION_RUNTIME" in text
    assert "status.trading.router.running" in text
    assert "status.trading.router.pid" in text


def test_operational_launcher_is_compatibility_wrapper() -> None:
    text = _text("RUN_AFIP_V1_FINAL_OPERATIONAL_RUNTIME.ps1")
    assert "compatibility wrapper" in text
    assert "FINAL_INTEGRATION_RUNTIME" in text
    assert "START_AFIP.ps1" in text
    assert "STOP_AFIP.ps1" in text
    assert "STATUS_AFIP.ps1" in text
    assert "tools.afip_operational_runtime start" not in text
    assert "tools.afip_operational_runtime stop" not in text


def test_canonical_start_stop_status_share_final_integration() -> None:
    start = _text("START_AFIP.ps1")
    stop = _text("STOP_AFIP.ps1")
    status = _text("STATUS_AFIP.ps1")
    assert "tools.afip_final_integration start" in start
    assert "tools.afip_final_integration stop" in stop
    assert "tools.afip_final_integration status" in status


def test_no_launcher_auto_starts_mt5() -> None:
    combined = "\n".join(
        _text(name)
        for name in (
            "START_AFIP.ps1",
            "START_AFIP_SAFE.ps1",
            "STOP_AFIP.ps1",
            "STATUS_AFIP.ps1",
            "RUN_AFIP_V1_FINAL_OPERATIONAL_RUNTIME.ps1",
        )
    ).lower()
    assert "terminal64.exe" not in combined
    assert "start-process" not in combined
