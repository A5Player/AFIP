from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATEWAY = ROOT / "afip" / "demo_execution_gateway" / "runtime.py"
WORKER = ROOT / "tools" / "afip_profile_execution_once.py"


def test_worker_requires_existing_terminal_without_launching_it():
    text = WORKER.read_text(encoding="utf-8")
    assert "_require_target_terminal_running(profile)" in text
    assert "running_terminal_paths()" in text
    assert "mt5_terminal_not_running_manual_start_required" in text
    assert "subprocess.Popen" not in text
    assert '[str(terminal), "/portable"]' not in text


def test_gateway_resets_bridge_before_initialize():
    text = GATEWAY.read_text(encoding="utf-8")
    segment = text[text.index("def preflight"):text.index("def _existing_positions")]
    assert segment.index("mt5.shutdown()") < segment.index("mt5.initialize(")


def test_binding_is_verified_during_preflight():
    text = GATEWAY.read_text(encoding="utf-8")
    segment = text[text.index("def preflight"):text.index("def _existing_positions")]
    assert '"exact_profile_binding_mismatch"' in segment
    assert "configured_terminal_folder=str(self.profile.mt5_folder)" in segment


def test_lot_ceiling_uses_float_tolerance():
    text = GATEWAY.read_text(encoding="utf-8")
    assert "(lot - self.maximum_lot_per_order) > 1e-12" in text
