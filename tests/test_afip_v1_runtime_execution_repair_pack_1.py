from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATEWAY = ROOT / "afip" / "demo_execution_gateway" / "runtime.py"
WORKER = ROOT / "tools" / "afip_profile_execution_once.py"


def test_worker_prelaunches_exact_portable_terminal():
    text = WORKER.read_text(encoding="utf-8")
    assert "_ensure_target_terminal(profile)" in text
    assert '[str(terminal), "/portable"]' in text
    assert "time.sleep(2.0)" in text


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
