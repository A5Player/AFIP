from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "afip" / "demo_execution_gateway" / "runtime.py"
CONTROL = ROOT / "tools" / "afip_demo_execution_control.py"


def test_execution_is_serialized_across_profiles():
    text = RUNTIME.read_text(encoding="utf-8")
    assert "account_routing.lock" in text
    assert "os.O_CREAT | os.O_EXCL" in text
    assert "account_routing_lock_busy" in text


def test_exact_binding_is_checked_at_all_critical_points():
    text = RUNTIME.read_text(encoding="utf-8")
    assert "exact_profile_binding_mismatch" in text
    assert "execution_ownership_mismatch_before_order_check" in text
    assert "execution_ownership_changed_before_order_send" in text
    assert "execution_ownership_changed_after_order_send" in text


def test_request_has_profile_ownership():
    text = RUNTIME.read_text(encoding="utf-8")
    assert 'f"AFIP {self.profile.profile_id} ' in text
    assert 'int(request.get("magic", 0)) == self.policy.magic' in text


def test_obsolete_capital_per_unit_policy_is_rejected():
    text = RUNTIME.read_text(encoding="utf-8")
    assert "obsolete_sizing_fields_forbidden" in text
    assert "LEGACY_FIXED_UNIT" not in text


def test_status_exposes_execution_ownership():
    text = CONTROL.read_text(encoding="utf-8")
    assert '"connected_account_login"' in text
    assert '"connected_terminal_folder"' in text
    assert '"ownership_token"' in text
