from pathlib import Path
from types import SimpleNamespace
import json

from afip.live_mt5_snapshot_authority import publish_live_mt5_snapshot


class FakeMT5:
    def symbol_info_tick(self, symbol): return SimpleNamespace(bid=4049.10, ask=4049.35)
    def symbol_info(self, symbol): return SimpleNamespace(point=0.01, digits=2)
    def terminal_info(self): return SimpleNamespace(connected=True)
    def positions_get(self, **kwargs): return (SimpleNamespace(ticket=1),)
    def orders_get(self, **kwargs): return ()


def test_existing_session_snapshot_contains_live_financial_and_market_data(tmp_path: Path):
    profile = SimpleNamespace(profile_id="P1", enabled=True, symbol="GOLD#", login="12340369",
        server="XMGlobal-MT5 6", mt5_terminal=tmp_path / "terminal64.exe", runtime_directory=tmp_path / "p1")
    account = SimpleNamespace(login=12340369, server="XMGlobal-MT5 6", currency="USD", balance=88.52,
        equity=90.10, margin=1.20, margin_free=88.90, profit=1.58, trade_allowed=True)
    report = publish_live_mt5_snapshot(profile=profile, mt5=FakeMT5(), account=account)
    assert report["currency"] == "USD"
    assert report["equity"] == 90.10
    assert report["bid"] == 4049.10
    assert report["spread_points"] == 25.0
    assert report["positions_total"] == 1
    assert report["execution_authority"] is False
    assert report["order_send_called"] is False
    stored = json.loads((profile.runtime_directory / "mt5_live_snapshot.json").read_text())
    assert stored["evidence_kind"] == "LIVE"


def test_gateway_source_publishes_snapshot_after_successful_preflight():
    source = Path("afip/demo_execution_gateway/runtime.py").read_text(encoding="utf-8")
    assert "from afip.live_mt5_snapshot_authority import publish_live_mt5_snapshot" in source
    assert "publish_live_mt5_snapshot(" in source
