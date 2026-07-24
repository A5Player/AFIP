from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATEWAY = ROOT / "afip" / "demo_execution_gateway" / "runtime.py"
CONTROL = ROOT / "tools" / "afip_demo_execution_control.py"
PLANNER = ROOT / "afip" / "protection" / "sl_tp_planner.py"


def test_exact_terminal_identity_accepts_directory_or_executable_only():
    text = GATEWAY.read_text(encoding="utf-8")
    assert "return actual in {expected_folder, expected_terminal}" in text
    assert "_normalized_windows_path" in text


def test_binding_is_repaired_before_order_check_and_order_send():
    text = GATEWAY.read_text(encoding="utf-8")
    assert text.count("_repair_exact_binding(mt5)") >= 2
    assert text.index("_repair_exact_binding(mt5)") < text.index("check = mt5.order_check(request)")
    assert "execution_ownership_mismatch_before_order_check" in text


def test_successful_execution_persists_binding_certification():
    text = GATEWAY.read_text(encoding="utf-8")
    assert "binding_verified: bool = False" in text
    assert "binding_verified=True" in text
    control = CONTROL.read_text(encoding="utf-8")
    assert 'bool(state.get("binding_verified", False))' in control


def test_legacy_fixed_sl_tp_has_no_default_execution_path():
    text = PLANNER.read_text(encoding="utf-8")
    assert "stop_loss_points: float | None = None" in text
    assert "take_profit_points: float | None = None" in text
    assert "adaptive_protection_required" in text
    assert "legacy_fixed_sl_tp_fallback_rejected" in text


def test_profile_isolation_remains_globally_serialized():
    text = GATEWAY.read_text(encoding="utf-8")
    assert 'Path("runtime/execution/account_routing.lock")' in text
    assert "portable=True" in text
    assert "mt5.shutdown()" in text
