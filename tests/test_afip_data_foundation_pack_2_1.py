from pathlib import Path

from afip.mt5_historical_integration.mt5_gateway import MetaTrader5ReadOnlyGateway


class FakeMT5:
    TIMEFRAME_M1 = 1
    def __init__(self):
        self.initialize_calls = []
        self.shutdown_calls = 0
    def initialize(self, **kwargs):
        self.initialize_calls.append(kwargs)
        return True
    def shutdown(self):
        self.shutdown_calls += 1
    def last_error(self):
        return (0, "OK")


def test_binding_refuses_to_start_missing_or_stopped_terminal(tmp_path, monkeypatch):
    mt5 = FakeMT5()
    gateway = MetaTrader5ReadOnlyGateway(mt5)
    missing = tmp_path / "terminal64.exe"
    ok, reason = gateway.bind_running_terminal(missing)
    assert not ok
    assert reason == "configured_terminal_not_found"
    missing.write_bytes(b"")
    monkeypatch.setattr(gateway, "running_terminal_paths", lambda: set())
    ok, reason = gateway.bind_running_terminal(missing)
    assert not ok
    assert reason == "configured_terminal_process_not_running"
    assert mt5.initialize_calls == []


def test_binding_uses_exact_running_terminal_path(tmp_path, monkeypatch):
    mt5 = FakeMT5()
    gateway = MetaTrader5ReadOnlyGateway(mt5)
    terminal = tmp_path / "terminal64.exe"
    terminal.write_bytes(b"")
    monkeypatch.setattr(gateway, "running_terminal_paths", lambda: {gateway._normal_path(terminal)})
    ok, reason = gateway.bind_running_terminal(terminal)
    assert ok
    assert reason == "bound_to_existing_terminal"
    assert mt5.initialize_calls == [{"path": str(terminal), "portable": True}]
