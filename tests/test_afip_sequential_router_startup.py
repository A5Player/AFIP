from pathlib import Path


def test_start_control_waits_for_router_handshake():
    text = Path("tools/afip_demo_execution_control.py").read_text(encoding="utf-8")
    assert "_wait_for_router" in text
    assert "router_start_timeout" in text
    assert "router_process_exited" in text


def test_status_uses_verified_binding_as_authority():
    text = Path("tools/afip_demo_execution_control.py").read_text(encoding="utf-8")
    assert '"connected_account_login": actual_login' in text
    assert '"connected_terminal_folder": actual_terminal' in text
    assert '"last_execution_account_login"' in text


def test_router_keeps_running_after_profile_exception():
    text = Path("tools/afip_profile_sequential_execution_router.py").read_text(encoding="utf-8")
    assert "except Exception as exc" in text
    assert '"profile_errors": errors' in text
    assert '"status": status' in text


def test_safe_start_requires_running_pid():
    text = Path("START_AFIP_SAFE.ps1").read_text(encoding="utf-8")
    assert "router.running" in text
    assert "router.pid" in text
    assert "SAFE START BLOCKED" in text
